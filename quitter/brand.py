"""Het merk QUITTER — één bron van waarheid.

Alles wat het bedrijf naar buiten brengt (website, ads, mails, doos, agents)
leest hieruit. Verander het hier, en het verandert overal.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# --------------------------------------------------------------------------
# De rode draad
# --------------------------------------------------------------------------
# Eén zin die het bedrijf beschrijft. Elke tekst, elke ad, elke mail en elk
# ontwerp moet hierop terug te voeren zijn. Kun je een zin niet herleiden tot
# deze zin, dan hoort hij niet bij QUITTER.

RODE_DRAAD = "QUITTER haalt de nicotine er in 90 dagen uit — volgens schema, niet op wilskracht."

# De vier woorden die de rode draad dragen. Gebruikt door de agents als toets.
KERNWOORDEN = ["schema", "afbouwen", "90 dagen", "geen wilskracht"]

PAYOFF = "90 dagen. Volgens schema."
CTA = "Word een QUITTER"

# De belofte in de taal van de klant, voor koppen en ads.
ELEVATOR = (
    "Stoppen met roken mislukt bijna nooit omdat je te zwak bent. Het mislukt omdat "
    "je van 20 sigaretten naar nul springt en je lichaam die sprong niet aankan. "
    "QUITTER is een doosje met 90 dagen nicotinekauwgom in aflopende sterkte, plus "
    "elke ochtend één mail die vertelt wat je die dag doet. Je bouwt af van 4 mg naar "
    "2 mg naar niets. Geen wilskracht. Een schema."
)


@dataclass(frozen=True)
class Kleur:
    naam: str
    hex: str
    gebruik: str


PALET: list[Kleur] = [
    Kleur("Ink", "#101110", "Achtergrond van alles. Bijna zwart, niet zwart."),
    Kleur("Paper", "#F6F3EC", "Tekst op donker, en vlakken die rust moeten geven."),
    Kleur("Ember", "#FF4B26", "De gloed van een sigaret. Alleen voor knoppen en dag 1."),
    Kleur("Lime", "#DDFF57", "Voortgang, afgevinkt, 'je bent er'. Nooit naast Ember."),
    Kleur("Ash", "#6E706B", "Bijschriften, kleine letters, uitgegrijsde stappen."),
    Kleur("Line", "#2A2C29", "Randen en scheidingslijnen op donker."),
]

FONT_DISPLAY = "'Archivo', 'Helvetica Neue', Arial, sans-serif"
FONT_TEKST = "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif"


# --------------------------------------------------------------------------
# Toon
# --------------------------------------------------------------------------
# Tussen hard en warm in: nuchter over de verslaving, zacht over de persoon.
# We veroordelen de roker nooit, we veroordelen de sprong naar nul.

TOON_WEL = [
    "Nuchter. Zeg wat er gebeurt, niet wat iemand moet voelen.",
    "Korte zinnen. Nederlandse woorden. Geen Engels als het niet hoeft.",
    "Concreet: getallen, dagen, aantallen stuks. Nooit 'binnenkort' of 'vaak'.",
    "Je-vorm. Eén lezer, geen publiek.",
    "Zacht over de persoon: falen is nooit hun schuld, het schema was verkeerd.",
    "Eerlijk over wat het niet doet: dit haalt de trek er niet uit, het maakt hem kleiner.",
]

TOON_NIET = [
    "Geen bangmakerij met longfoto's of sterftecijfers.",
    "Geen 'gefeliciteerd, held!' — geen kinderfeestje.",
    "Geen therapie-taal: 'reis', 'omarmen', 'jouw waarheid'.",
    "Geen absolute beloftes: nooit 'gegarandeerd rookvrij'.",
    "Geen uitroeptekens in bodytekst. Eén per pagina, hooguit.",
    "Nooit spotten met mensen die eerder gestopt en teruggevallen zijn.",
]

# Zinnen die het merk mag zeggen, letterlijk herbruikbaar in ads en pagina's.
COPY_BANK = [
    "Wilskracht is geen plan.",
    "Van 20 naar nul is een sprong. Wij maken er 90 stappen van.",
    "Je hoeft het niet te voelen. Je hoeft het alleen te volgen.",
    "Dag 1 is niet de zwaarste dag. Dag 3 is dat. Daarom staat er iets klaar voor dag 3.",
    "Het doosje past in je broekzak, precies waar je pakje zat.",
    "Elke ochtend één mail: dit is wat je vandaag doet.",
    "Stoppen is geen moment. Het is negentig keer opstaan met een plan.",
    "4 mg. Dan 2 mg. Dan niets.",
]


@dataclass(frozen=True)
class Merk:
    naam: str = "QUITTER"
    domein: str = "quitter90.nl"
    domeinen_extra: tuple[str, ...] = ("wordeenquitter.nl", "quitterco.nl", "wordquitter.nl")
    rode_draad: str = RODE_DRAAD
    payoff: str = PAYOFF
    cta: str = CTA
    elevator: str = ELEVATOR
    palet: tuple[Kleur, ...] = field(default_factory=lambda: tuple(PALET))
    toon_wel: tuple[str, ...] = field(default_factory=lambda: tuple(TOON_WEL))
    toon_niet: tuple[str, ...] = field(default_factory=lambda: tuple(TOON_NIET))

    def kleur(self, naam: str) -> str:
        for k in self.palet:
            if k.naam.lower() == naam.lower():
                return k.hex
        raise KeyError(f"onbekende kleur: {naam}")

    def briefing(self) -> str:
        """De merkbriefing die elke AI-agent in zijn systeemprompt krijgt."""
        wel = "\n".join(f"- {t}" for t in self.toon_wel)
        niet = "\n".join(f"- {t}" for t in self.toon_niet)
        zinnen = "\n".join(f"- {z}" for z in COPY_BANK)
        return f"""# Merk: {self.naam}

## De rode draad (elke tekst moet hierop terug te voeren zijn)
{self.rode_draad}

## Payoff
{self.payoff}

## In het kort
{self.elevator}

## Toon — wel
{wel}

## Toon — niet
{niet}

## Zinnen die van ons zijn (mag je hergebruiken)
{zinnen}
"""


MERK = Merk()
