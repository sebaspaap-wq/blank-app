"""Berichtsjablonen voor de Support-agent.

Paragraaf 3.3 van de bouwopdracht: de Support-agent mag zelfstandig
standaardberichten versturen, maar **geen inhoudelijke toezeggingen doen over
geld, tarieven of contractvoorwaarden**.

Net als bij de uitbetalingen is dat hier geen instructie in een systeemprompt,
maar een eigenschap van de constructie:

1. **De agent kan geen vrije tekst versturen.** ``verstuur_bericht`` accepteert
   alleen de naam van een geregistreerd sjabloon plus variabelen. Er is geen
   parameter waarin een model een zelfgeschreven zin kwijt kan.

2. **Sjablonen worden bij registratie gecontroleerd.** Een sjabloon dat een
   bedrag, tarief of contractvoorwaarde bevat, wordt geweigerd op importtijd —
   de applicatie start dan niet. Een toezegging over geld kan dus niet per
   ongeluk in productie belanden.

3. **Variabelen zijn vastgelegd.** Rendering is strikt: een ontbrekende of een
   onverwachte variabele is een fout, geen lege string. Zo kan een half gevuld
   bericht nooit de deur uit.

Inhoudelijke antwoorden op vragen komen niet uit deze sjablonen maar uit de
kennisbank — teksten die Sebas zelf heeft goedgekeurd. Het model kiest alleen
welk antwoord van toepassing is; het schrijft er nooit een.
"""

from __future__ import annotations

import re
import string
from dataclasses import dataclass

from app.core.domein import Kanaal


class SjabloonFout(ValueError):
    """Het sjabloon bestaat niet, of de variabelen kloppen niet."""


class VerbodenToezeggingError(ValueError):
    """Een sjabloon doet een toezegging die Support niet mag doen."""


#: Termen die duiden op een toezegging over geld, tarieven of voorwaarden.
#: Bewust ruim: liever een sjabloon dat opnieuw geformuleerd moet worden dan een
#: bericht dat namens WOSZ iets belooft.
_VERBODEN_PATRONEN: tuple[tuple[str, str], ...] = (
    (r"€", "bedrag"),
    (r"\beuro\b", "bedrag"),
    (r"\btarief\b|\btarieven\b", "tarief"),
    (r"\buurloon\b|\bper uur\b", "tarief"),
    (r"\bkorting\b", "tarief"),
    (r"\bbonus\b", "geldtoezegging"),
    (r"\buitbetal\w*", "geldtoezegging"),
    (r"\bvergoeding\b", "geldtoezegging"),
    (r"\bcontract\w*", "contractvoorwaarde"),
    (r"\bgarande\w*|\bgarantie\b", "toezegging"),
    (r"\bwij beloven\b|\bwe beloven\b", "toezegging"),
)


def _controleer_geen_toezegging(naam: str, tekst: str) -> None:
    for patroon, soort in _VERBODEN_PATRONEN:
        treffer = re.search(patroon, tekst, flags=re.IGNORECASE)
        if treffer:
            raise VerbodenToezeggingError(
                f"Sjabloon '{naam}' bevat een {soort} ('{treffer.group(0)}'). "
                "Support mag geen toezeggingen doen over geld, tarieven of "
                "contractvoorwaarden — zie paragraaf 3.3 van de bouwopdracht. "
                "Verwijs door naar Sebas in plaats van iets toe te zeggen."
            )


def _placeholders(tekst: str) -> set[str]:
    return {
        veld
        for _, veld, _, _ in string.Formatter().parse(tekst)
        if veld is not None
    }


@dataclass(frozen=True, slots=True)
class Sjabloon:
    """Eén vastgelegd berichtsjabloon."""

    naam: str
    kanaal: Kanaal
    onderwerp: str
    body: str

    def __post_init__(self) -> None:
        _controleer_geen_toezegging(self.naam, f"{self.onderwerp}\n{self.body}")

    @property
    def variabelen(self) -> set[str]:
        return _placeholders(self.onderwerp) | _placeholders(self.body)

    def render(self, **waarden: object) -> tuple[str, str]:
        """Render onderwerp en body. Strikt: alles moet precies kloppen."""
        verwacht = self.variabelen
        gegeven = set(waarden)

        ontbreekt = verwacht - gegeven
        if ontbreekt:
            raise SjabloonFout(
                f"Sjabloon '{self.naam}' mist variabele(n): {sorted(ontbreekt)}"
            )
        teveel = gegeven - verwacht
        if teveel:
            raise SjabloonFout(
                f"Sjabloon '{self.naam}' kent variabele(n) niet: {sorted(teveel)}"
            )
        for sleutel, waarde in waarden.items():
            if not str(waarde).strip():
                raise SjabloonFout(
                    f"Sjabloon '{self.naam}': variabele '{sleutel}' is leeg"
                )

        return self.onderwerp.format(**waarden), self.body.format(**waarden)


# ---------------------------------------------------------------------------
# De registry — dit is alles wat Support kan versturen
# ---------------------------------------------------------------------------

_SJABLONEN: dict[str, Sjabloon] = {}


def registreer(sjabloon: Sjabloon) -> Sjabloon:
    if sjabloon.naam in _SJABLONEN:
        raise ValueError(f"Sjabloon '{sjabloon.naam}' bestaat al")
    _SJABLONEN[sjabloon.naam] = sjabloon
    return sjabloon


def haal_sjabloon(naam: str) -> Sjabloon:
    sjabloon = _SJABLONEN.get(naam)
    if sjabloon is None:
        raise SjabloonFout(
            f"Onbekend sjabloon '{naam}'. Support kan uitsluitend geregistreerde "
            f"sjablonen versturen; beschikbaar: {sorted(_SJABLONEN)}"
        )
    return sjabloon


def alle_sjablonen() -> dict[str, Sjabloon]:
    return dict(_SJABLONEN)


NO_SHOW_WAARSCHUWING = registreer(
    Sjabloon(
        naam="no_show_waarschuwing",
        kanaal=Kanaal.WHATSAPP,
        onderwerp="Je was er niet bij {bedrijf_naam}",
        body=(
            "Hoi {medewerker_naam},\n\n"
            "Je stond ingepland bij {bedrijf_naam}, maar je hebt je niet gemeld. "
            "Dat is vervelend voor het team dat op je rekende.\n\n"
            "Kon je er echt niet zijn? Laat het ons weten, dan kijken we mee. "
            "Meld je voortaan af zodra je weet dat het niet lukt, dan kunnen we "
            "op tijd iemand anders vragen.\n\n"
            "Groet,\nWOSZ"
        ),
    )
)

HERHAALDE_NO_SHOW = registreer(
    Sjabloon(
        naam="herhaalde_no_show",
        kanaal=Kanaal.WHATSAPP,
        onderwerp="We willen je even spreken",
        body=(
            "Hoi {medewerker_naam},\n\n"
            "Dit is de {aantal}e keer dit seizoen dat je niet bent komen opdagen "
            "voor een shift. Zo lopen bedrijven vast en dat kunnen we niet laten "
            "doorgaan.\n\n"
            "Sebas neemt persoonlijk contact met je op om te bespreken hoe nu "
            "verder.\n\n"
            "Groet,\nWOSZ"
        ),
    )
)

ONBOARDING = registreer(
    Sjabloon(
        naam="onboarding",
        kanaal=Kanaal.WHATSAPP,
        onderwerp="Welkom bij WOSZ, {medewerker_naam}",
        body=(
            "Hoi {medewerker_naam},\n\n"
            "Welkom bij WOSZ. Fijn dat je erbij bent.\n\n"
            "Zo werkt het: in de app zie je alle openstaande shifts bij "
            "strandtenten in Zandvoort. Reageer op wat je leuk lijkt en past bij "
            "je beschikbaarheid. Zodra een bedrijf je accepteert, staat de shift "
            "in je overzicht.\n\n"
            "Hoe meer uren je maakt, hoe hoger je level en hoe eerder je mag "
            "reageren op nieuwe shifts.\n\n"
            "Vragen? Stuur gerust een bericht.\n\n"
            "Groet,\nWOSZ"
        ),
    )
)

SHIFT_BEVESTIGD = registreer(
    Sjabloon(
        naam="shift_bevestigd",
        kanaal=Kanaal.WHATSAPP,
        onderwerp="Je shift bij {bedrijf_naam} staat vast",
        body=(
            "Hoi {medewerker_naam},\n\n"
            "Je bent ingepland bij {bedrijf_naam} op {datum} ({tijd}) als "
            "{functie}.\n\n"
            "Zorg dat je op tijd bent. Lukt het onverhoopt niet, meld je dan zo "
            "snel mogelijk af via de app.\n\n"
            "Groet,\nWOSZ"
        ),
    )
)

UREN_HERINNERING = registreer(
    Sjabloon(
        naam="uren_herinnering",
        kanaal=Kanaal.WHATSAPP,
        onderwerp="Hoeveel uur heb je gewerkt bij {bedrijf_naam}?",
        body=(
            "Hoi {medewerker_naam},\n\n"
            "Je shift bij {bedrijf_naam} op {datum} staat nog open in het "
            "systeem. Geef even in de app door hoeveel uur je hebt gewerkt, dan "
            "is het administratief rond.\n\n"
            "Klopt er iets niet aan deze shift? Stuur dan een bericht terug.\n\n"
            "Groet,\nWOSZ"
        ),
    )
)

KENNISBANK_ANTWOORD = registreer(
    Sjabloon(
        naam="kennisbank_antwoord",
        kanaal=Kanaal.WHATSAPP,
        onderwerp="Je vraag: {vraag_kort}",
        body=(
            "Hoi {medewerker_naam},\n\n"
            "{antwoord}\n\n"
            "Heb je er nog iets over? Stuur gerust een bericht terug.\n\n"
            "Groet,\nWOSZ"
        ),
    )
)

VRAAG_DOORGEZET = registreer(
    Sjabloon(
        naam="vraag_doorgezet",
        kanaal=Kanaal.WHATSAPP,
        onderwerp="We pakken je vraag op",
        body=(
            "Hoi {medewerker_naam},\n\n"
            "Bedankt voor je bericht. Hier wil ik niet zomaar iets op antwoorden, "
            "dus ik heb het doorgezet naar Sebas. Hij komt er zelf op terug.\n\n"
            "Groet,\nWOSZ"
        ),
    )
)


__all__ = [
    "Sjabloon",
    "SjabloonFout",
    "VerbodenToezeggingError",
    "alle_sjablonen",
    "haal_sjabloon",
    "registreer",
]
