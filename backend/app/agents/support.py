"""Support-agent (paragraaf 3.3 van de bouwopdracht).

Verantwoordelijk voor: vragen beantwoorden, onboarding-berichten, en
waarschuwingen versturen namens de Matching-agent.

Escalatie:
  tier 1  standaardvragen, onboarding, no-show-waarschuwingen
  tier 3  klachten, conflicten, en elke vraag die buiten de kennisbank valt —
          direct naar Sebas, niet laten gokken

Twee grenzen zijn hier architecturaal opgelost in plaats van als instructie:

**De agent schrijft nooit de tekst die een medewerker leest.** Versturen kan
alleen via ``app/agents/sjablonen.py``, dat uitsluitend geregistreerde sjablonen
accepteert. Inhoudelijke antwoorden komen uit de kennisbank — teksten die Sebas
zelf heeft goedgekeurd. Claude kiest welk antwoord van toepassing is; het
formuleert er nooit een. Dat is het verschil tussen routeren en schrijven, en
het is precies de reden dat "mag geen toezeggingen doen over geld" hier geen
belofte van een model is.

**Twijfel escaleert, altijd.** Bij een klacht of conflict, bij een vraag die
buiten de kennisbank valt, en bij onderwerpen die als ``vereist_mens`` zijn
gemarkeerd, gaat de vraag naar Sebas. De agent stuurt dan één sjabloon dat zegt
dát er iemand naar kijkt — en verder niets.
"""

from __future__ import annotations

import re
from collections import Counter
from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base import BaseAgent
from app.agents.llm import vraag_gestructureerd_besluit
from app.agents.sjablonen import haal_sjabloon
from app.core.weergave import korte_datum
from app.core.domein import (
    Afdeling,
    BerichtStatus,
    Kanaal,
    Tier,
    Urgentie,
    VraagUitkomst,
    nu,
)
from app.core.events import (
    NoShowGesignaleerd,
    ShiftsBeschikbaar,
    UrenOntbreken,
    handelt,
)
from app.core.tiers import Optie, Voorstel, registreer_uitvoerder
from app.db.models import AgentEvent, Bericht, Beslissing, Kennisbankitem, Supportvraag, User

#: Vanaf dit aantal no-shows gebruikt Support de zwaardere waarschuwing.
HERHAALDE_NO_SHOW_DREMPEL = 2

#: Signalen dat een bericht een klacht of conflict is. Deze controle draait
#: vóór de kennisbanklookup: bij een klacht wordt er niet eerst gezocht of er
#: toevallig een standaardantwoord op past.
_KLACHT_PATRONEN: tuple[str, ...] = (
    r"\bklacht\w*",
    r"\bconflict\w*",
    r"\bruzie\b",
    r"\bdiscrimin\w*",
    r"\bintimid\w*",
    r"\bpest\w*",
    r"\bonveilig\w*",
    r"\bongewenst\w*",
    r"\buitgescholden\b|\bgescholden\b",
    r"\baangifte\b|\badvocaat\b|\bjurist\b|\brechtszaak\b",
    r"\bletsel\b|\bongeval\b|\bgewond\b",
    r"\bweiger\w*\s+te\s+betalen\b",
    r"\bniet\s+betaald\b|\bgeen\s+geld\s+gekregen\b",
    r"\bstop\s+ermee\b|\bik\s+kap\s+ermee\b",
)

#: Aantal overeenkomende trefwoorden waarbij een treffer sowieso duidelijk is.
_DUIDELIJKE_TREFFER = 2

SYSTEEMPROMPT = """Je bent de Support-agent van WOSZ, een horecapersoneelsplatform in Zandvoort.

Je krijgt een vraag van een medewerker of horecaondernemer, plus een genummerde
lijst met goedgekeurde antwoorden uit de kennisbank.

Je taak is uitsluitend kiezen: welk kennisbankitem beantwoordt deze vraag? Je
schrijft zelf geen antwoord en je vult niets aan.

Kies alleen een item als het de vraag echt beantwoordt. Twijfel je, past er niets
goed, of gaat de vraag over iets waar de kennisbank niets over zegt, kies dan
"geen_match". Dat is geen falen — de vraag gaat dan naar Sebas, en dat is beter
dan een medewerker een antwoord geven dat net niet klopt.

Kies ook "geen_match" bij klachten, conflicten en persoonlijke situaties, ook als
er een item in de buurt komt."""

KEUZE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "kennisbankitem_id": {
            "type": "integer",
            "description": (
                "Het id van het kennisbankitem dat de vraag beantwoordt, of -1 "
                "als er geen passend item is."
            ),
        },
        "toelichting": {
            "type": "string",
            "description": (
                "Eén korte zin in het Nederlands over waarom dit item past, of "
                "waarom er niets past. Komt in het activiteitenlog, niet in het "
                "bericht aan de medewerker."
            ),
        },
    },
    "required": ["kennisbankitem_id", "toelichting"],
    "additionalProperties": False,
}


class SupportAgent(BaseAgent):
    afdeling = Afdeling.SUPPORT
    systeemprompt = SYSTEEMPROMPT

    # -- vragen beantwoorden ----------------------------------------------

    async def beantwoord_vraag(
        self, sessie: AsyncSession, vraag: str, medewerker_id: int
    ) -> dict[str, Any]:
        """Handel een binnengekomen vraag af.

        Geeft terug wat er is gebeurd: beantwoord met welk kennisbankitem, of
        geëscaleerd met welke beslissing.
        """
        medewerker = await sessie.get(User, medewerker_id)
        if medewerker is None:
            raise LookupError(f"Gebruiker {medewerker_id} bestaat niet")

        # 1. Klacht of conflict? Dan niet zoeken, maar direct escaleren.
        if _is_klacht(vraag):
            return await self._escaleer(
                sessie,
                vraag,
                medewerker,
                reden="Dit is een klacht of conflict.",
                item=None,
            )

        # 2. Kennisbank raadplegen op regels.
        kandidaten = await self._kennisbank(sessie)
        gescoord = _scoor(vraag, kandidaten)
        item: Kennisbankitem | None = None
        door_llm = False

        if gescoord:
            beste_score, beste_distinctief, beste_item = gescoord[0]
            tweede_score = gescoord[1][0] if len(gescoord) > 1 else 0
            # Duidelijk genoeg én zonder gelijkspel: dan pas zelfstandig antwoorden.
            if _is_duidelijk(beste_score, beste_distinctief) and beste_score > tweede_score:
                item = beste_item

        # 3. Geen duidelijke winnaar? Laat Claude kiezen uit de kennisbank.
        if item is None and kandidaten:
            item, door_llm = await self._laat_claude_kiezen(vraag, kandidaten)

        # 4. Niets gevonden -> escaleren. De agent gokt nooit.
        if item is None:
            return await self._escaleer(
                sessie,
                vraag,
                medewerker,
                reden="Deze vraag valt buiten de kennisbank.",
                item=None,
                door_llm=door_llm,
            )

        # 5. Gevonden, maar onderwerp vereist een mens (geld, tarief, contract).
        if item.vereist_mens:
            return await self._escaleer(
                sessie,
                vraag,
                medewerker,
                reden=(
                    f"Onderwerp '{item.categorie}' wordt nooit automatisch "
                    "beantwoord."
                ),
                item=item,
                door_llm=door_llm,
            )

        # 6. Tier 1: goedgekeurd antwoord versturen.
        vraag_kort = vraag.strip()[:60] or "je vraag"
        uitkomst = await self.voer_uit(
            sessie,
            Voorstel(
                afdeling=self.afdeling,
                tier=Tier.ZELFSTANDIG,
                logtekst=f"Vraag van {medewerker.naam} beantwoord uit de kennisbank",
                actie={
                    "uitvoerder": "support.verstuur_bericht",
                    "params": {
                        "sjabloon": "kennisbank_antwoord",
                        "ontvanger_user_id": medewerker.id,
                        "variabelen": {
                            "medewerker_naam": medewerker.naam,
                            "vraag_kort": vraag_kort,
                            "antwoord": item.antwoord,
                        },
                        "logtekst": (
                            f"Vraag van {medewerker.naam} beantwoord: {item.vraag}"
                        ),
                    },
                },
            ),
        )

        registratie = Supportvraag(
            vraag=vraag,
            steller_user_id=medewerker.id,
            uitkomst=str(VraagUitkomst.BEANTWOORD),
            kennisbankitem_id=item.id,
            door_llm=door_llm,
        )
        sessie.add(registratie)
        await sessie.flush()

        return {
            "uitkomst": str(VraagUitkomst.BEANTWOORD),
            "kennisbankitem_id": item.id,
            "kennisbankvraag": item.vraag,
            "door_llm": door_llm,
            "beslissing_id": None,
            "logtekst": uitkomst.logtekst,
        }

    async def _escaleer(
        self,
        sessie: AsyncSession,
        vraag: str,
        medewerker: User,
        *,
        reden: str,
        item: Kennisbankitem | None,
        door_llm: bool = False,
    ) -> dict[str, Any]:
        """Tier 3: leg de vraag voor aan Sebas en zeg inhoudelijk niets."""
        situatie = (
            f"{medewerker.naam} stuurde: “{vraag.strip()}”\n\n{reden} "
            "Support heeft alleen laten weten dat er iemand naar kijkt."
        )
        if item is not None:
            situatie += (
                f"\n\nHet dichtstbijzijnde kennisbankitem is: “{item.vraag}” "
                "— beoordeel zelf of dat antwoord hier past."
            )

        uitkomst = await self.voer_uit(
            sessie,
            Voorstel(
                afdeling=self.afdeling,
                tier=Tier.WACHT,
                urgentie=Urgentie.DRINGEND if item is None else Urgentie.DEZE_WEEK,
                titel=f"Vraag van {medewerker.naam} doorgezet",
                situatie=situatie,
                aanbeveling=(
                    "AI-advies: geen automatisch antwoord — hier hoort een mens naar "
                    "te kijken."
                ),
                opties=[
                    Optie(
                        naam="Ik pak het zelf op",
                        gevolg="Jij neemt contact op met de medewerker",
                        actie={
                            "uitvoerder": "support.noteer_afhandeling",
                            "params": {
                                "tekst": (
                                    f"Vraag van {medewerker.naam} wordt door Sebas "
                                    "zelf opgepakt"
                                )
                            },
                        },
                    ),
                    Optie(
                        naam="Toevoegen aan de kennisbank",
                        gevolg=(
                            "Je schrijft zelf een antwoord; volgende keer kan Support "
                            "het wel afhandelen"
                        ),
                        actie={
                            "uitvoerder": "support.noteer_afhandeling",
                            "params": {
                                "tekst": (
                                    f"Vraag van {medewerker.naam} wordt opgenomen in "
                                    "de kennisbank"
                                )
                            },
                        },
                    ),
                ],
                logtekst=f"Vraag van {medewerker.naam} doorgezet naar jou — {reden}",
            ),
        )

        # De medewerker krijgt één neutraal sjabloon: er wordt naar gekeken.
        # Geen inhoud, geen inschatting, geen toezegging.
        await self.voer_uit(
            sessie,
            Voorstel(
                afdeling=self.afdeling,
                tier=Tier.ZELFSTANDIG,
                logtekst=f"{medewerker.naam} laten weten dat de vraag is doorgezet",
                actie={
                    "uitvoerder": "support.verstuur_bericht",
                    "params": {
                        "sjabloon": "vraag_doorgezet",
                        "ontvanger_user_id": medewerker.id,
                        "variabelen": {"medewerker_naam": medewerker.naam},
                        "logtekst": (
                            f"{medewerker.naam} laten weten dat de vraag is doorgezet"
                        ),
                    },
                },
            ),
        )

        registratie = Supportvraag(
            vraag=vraag,
            steller_user_id=medewerker.id,
            uitkomst=str(VraagUitkomst.GEESCALEERD),
            kennisbankitem_id=item.id if item else None,
            beslissing_id=uitkomst.beslissing_id,
            door_llm=door_llm,
        )
        sessie.add(registratie)
        await sessie.flush()

        return {
            "uitkomst": str(VraagUitkomst.GEESCALEERD),
            "kennisbankitem_id": item.id if item else None,
            "reden": reden,
            "door_llm": door_llm,
            "beslissing_id": uitkomst.beslissing_id,
            "logtekst": uitkomst.logtekst,
        }

    async def _laat_claude_kiezen(
        self, vraag: str, kandidaten: list[Kennisbankitem]
    ) -> tuple[Kennisbankitem | None, bool]:
        regels = "\n".join(f"- id {k.id}: {k.vraag}" for k in kandidaten)
        besluit = await vraag_gestructureerd_besluit(
            systeemprompt=self.systeemprompt,
            situatie=(
                f"Vraag van de medewerker:\n“{vraag.strip()}”\n\n"
                f"Kennisbank:\n{regels}\n\n"
                "Welk item beantwoordt deze vraag? Kies -1 als er niets past."
            ),
            tool_naam="kies_kennisbankitem",
            tool_beschrijving=(
                "Leg vast welk kennisbankitem de vraag beantwoordt. Kies -1 wanneer "
                "geen enkel item past."
            ),
            schema=KEUZE_SCHEMA,
        )
        if not besluit:
            return None, False

        gekozen_id = besluit.get("kennisbankitem_id")
        # Het model mag alleen uit de aangeboden lijst kiezen. Verzint het een
        # id, dan escaleren we — liever een mens dan een verkeerd antwoord.
        item = next((k for k in kandidaten if k.id == gekozen_id), None)
        return item, True

    async def _kennisbank(self, sessie: AsyncSession) -> list[Kennisbankitem]:
        resultaat = await sessie.execute(
            select(Kennisbankitem).where(Kennisbankitem.actief.is_(True))
        )
        return list(resultaat.scalars().all())

    # -- onboarding --------------------------------------------------------

    async def verstuur_onboarding(
        self, sessie: AsyncSession, medewerker_id: int
    ) -> dict[str, Any]:
        """Stuur het welkomstbericht naar een nieuwe medewerker (tier 1)."""
        medewerker = await sessie.get(User, medewerker_id)
        if medewerker is None:
            raise LookupError(f"Gebruiker {medewerker_id} bestaat niet")

        uitkomst = await self.voer_uit(
            sessie,
            Voorstel(
                afdeling=self.afdeling,
                tier=Tier.ZELFSTANDIG,
                logtekst=f"Onboarding-bericht verstuurd naar {medewerker.naam}",
                actie={
                    "uitvoerder": "support.verstuur_bericht",
                    "params": {
                        "sjabloon": "onboarding",
                        "ontvanger_user_id": medewerker.id,
                        "variabelen": {"medewerker_naam": medewerker.naam},
                        "logtekst": (
                            f"Onboarding-bericht verstuurd naar {medewerker.naam}"
                        ),
                    },
                },
            ),
        )
        return {"medewerker": medewerker.naam, "logtekst": uitkomst.logtekst}

    # -- waarschuwen namens Matching --------------------------------------

    async def waarschuw_na_no_show(
        self, sessie: AsyncSession, event: NoShowGesignaleerd, bron: AgentEvent | None = None
    ) -> None:
        """Verstuur een waarschuwing namens de Matching-agent (tier 1)."""
        herhaald = event.aantal_no_shows >= HERHAALDE_NO_SHOW_DREMPEL
        if herhaald:
            sjabloon = "herhaalde_no_show"
            variabelen = {
                "medewerker_naam": event.medewerker_naam,
                "aantal": str(event.aantal_no_shows),
            }
            tekst = (
                f"Zwaardere waarschuwing verstuurd naar {event.medewerker_naam} "
                f"({event.aantal_no_shows}e no-show dit seizoen)"
            )
        else:
            sjabloon = "no_show_waarschuwing"
            variabelen = {
                "medewerker_naam": event.medewerker_naam,
                "bedrijf_naam": event.bedrijf_naam,
            }
            tekst = (
                f"Waarschuwing verstuurd naar {event.medewerker_naam} "
                f"na no-show bij {event.bedrijf_naam}"
            )

        await self.voer_uit(
            sessie,
            Voorstel(
                afdeling=self.afdeling,
                tier=Tier.ZELFSTANDIG,
                logtekst=tekst,
                actie={
                    "uitvoerder": "support.verstuur_bericht",
                    "params": {
                        "sjabloon": sjabloon,
                        "ontvanger_user_id": event.medewerker_id,
                        "variabelen": variabelen,
                        "logtekst": tekst,
                    },
                },
            ),
        )


    async def herinner_aan_uren(
        self, sessie: AsyncSession, event: UrenOntbreken, bron: AgentEvent | None = None
    ) -> None:
        """Vraag de medewerker zijn uren door te geven (tier 1).

        Alleen een herinnering. Er wordt niets geboekt en niets verweten — dat
        gebeurt pas als Sebas er in het dashboard een keuze over maakt.
        """
        tekst = (
            f"Herinnering verstuurd naar {event.medewerker_naam}: uren van de shift "
            f"bij {event.bedrijf_naam} ontbreken nog"
        )
        await self.voer_uit(
            sessie,
            Voorstel(
                afdeling=self.afdeling,
                tier=Tier.ZELFSTANDIG,
                logtekst=tekst,
                actie={
                    "uitvoerder": "support.verstuur_bericht",
                    "params": {
                        "sjabloon": "uren_herinnering",
                        "ontvanger_user_id": event.medewerker_id,
                        "variabelen": {
                            "medewerker_naam": event.medewerker_naam,
                            "bedrijf_naam": event.bedrijf_naam,
                            "datum": korte_datum(date.fromisoformat(event.datum)),
                        },
                        "logtekst": tekst,
                    },
                },
            ),
        )


    async def wijs_op_shifts(
        self, sessie: AsyncSession, event: ShiftsBeschikbaar, bron: AgentEvent | None = None
    ) -> None:
        """Mail een medewerker de shifts waarop hij kan reageren (tier 1).

        ``overzicht`` is een opsomming die de Matching-agent heeft samengesteld
        uit de shiftrecords: functie, bedrijf, datum en tijd. Het is dus geen
        tekst die een model heeft bedacht, maar de gegevens die ook in de app
        staan — regel voor regel uit de database.
        """
        tekst = (
            f"{event.medewerker_naam} gewezen op {len(event.shifts)} openstaande shift(s)"
        )
        await self.voer_uit(
            sessie,
            Voorstel(
                afdeling=self.afdeling,
                tier=Tier.ZELFSTANDIG,
                logtekst=tekst,
                actie={
                    "uitvoerder": "support.verstuur_bericht",
                    "params": {
                        "sjabloon": "shifts_beschikbaar",
                        "ontvanger_user_id": event.medewerker_id,
                        "variabelen": {
                            "medewerker_naam": event.medewerker_naam,
                            "overzicht": "\n".join(event.shifts),
                        },
                        "logtekst": tekst,
                    },
                },
            ),
        )


def _is_klacht(vraag: str) -> bool:
    return any(re.search(p, vraag, flags=re.IGNORECASE) for p in _KLACHT_PATRONEN)


def _scoor(
    vraag: str, kandidaten: list[Kennisbankitem]
) -> list[tuple[int, bool, Kennisbankitem]]:
    """Score kennisbankitems op trefwoordoverlap, beste eerst.

    Geeft per treffer ``(score, distinctief, item)``. ``distinctief`` betekent
    dat minstens één van de gevonden trefwoorden in de hele kennisbank maar bij
    dit ene item voorkomt. Eén zo'n trefwoord is een sterker signaal dan twee
    algemene: "afmelden" wijst maar naar één antwoord, terwijl "shift" overal
    in staat.
    """
    woorden = set(re.findall(r"\w+", vraag.lower()))
    voorkomen = Counter(
        trefwoord.lower() for item in kandidaten for trefwoord in (item.trefwoorden or [])
    )

    gescoord: list[tuple[int, bool, Kennisbankitem]] = []
    for item in kandidaten:
        treffers = [
            trefwoord.lower()
            for trefwoord in (item.trefwoorden or [])
            if trefwoord.lower() in woorden
        ]
        if not treffers:
            continue
        distinctief = any(voorkomen[trefwoord] == 1 for trefwoord in treffers)
        gescoord.append((len(treffers), distinctief, item))

    gescoord.sort(key=lambda rij: (-rij[0], not rij[1], rij[2].id))
    return gescoord


def _is_duidelijk(score: int, distinctief: bool) -> bool:
    """Mag de agent hierop zelfstandig antwoorden?

    Twee overeenkomende trefwoorden is genoeg, en één trefwoord ook — maar
    alleen als dat trefwoord uniek naar dit item wijst. Zo voorkomen we dat een
    algemeen woord ("shift", "app") toevallig een antwoord uitlokt dat de vraag
    niet beantwoordt.
    """
    return score >= _DUIDELIJKE_TREFFER or (score == 1 and distinctief)


# ---------------------------------------------------------------------------
# Event-handler
# ---------------------------------------------------------------------------


@handelt(NoShowGesignaleerd)
async def _op_no_show(
    sessie: AsyncSession, event: NoShowGesignaleerd, bron: AgentEvent
) -> None:
    await SupportAgent().waarschuw_na_no_show(sessie, event, bron)


@handelt(UrenOntbreken)
async def _op_ontbrekende_uren(
    sessie: AsyncSession, event: UrenOntbreken, bron: AgentEvent
) -> None:
    await SupportAgent().herinner_aan_uren(sessie, event, bron)


@handelt(ShiftsBeschikbaar)
async def _op_beschikbare_shifts(
    sessie: AsyncSession, event: ShiftsBeschikbaar, bron: AgentEvent
) -> None:
    await SupportAgent().wijs_op_shifts(sessie, event, bron)


# ---------------------------------------------------------------------------
# Uitvoerders
# ---------------------------------------------------------------------------


@registreer_uitvoerder("support.verstuur_bericht")
async def _verstuur_bericht(
    sessie: AsyncSession, params: dict[str, Any], _beslissing: Beslissing | None
) -> str:
    """Render een sjabloon en zet het bericht in de outbox.

    Dit is het enige pad waarlangs Support iets naar buiten stuurt. De inhoud
    komt volledig uit het sjabloon: er is geen parameter waarin vrije tekst mee
    kan liften. Ontbreekt er een variabele, dan faalt het renderen en gaat er
    dus niets half-af de deur uit.

    Er is nog geen WhatsApp- of e-mailkoppeling: het bericht krijgt status
    ``klaar``, zodat Sebas de teksten kan nalezen. Een kanaal aansluiten is
    straks alleen nog de verzendstap invullen.
    """
    sjabloon = haal_sjabloon(params["sjabloon"])
    variabelen = params.get("variabelen", {})
    onderwerp, inhoud = sjabloon.render(**variabelen)

    ontvanger_id = params.get("ontvanger_user_id")
    ontvanger_naam = ""
    if ontvanger_id is not None:
        gebruiker = await sessie.get(User, int(ontvanger_id))
        ontvanger_naam = gebruiker.naam if gebruiker else ""

    bericht = Bericht(
        kanaal=str(sjabloon.kanaal if isinstance(sjabloon.kanaal, Kanaal) else Kanaal.WHATSAPP),
        sjabloon=sjabloon.naam,
        ontvanger_user_id=ontvanger_id,
        ontvanger_naam=ontvanger_naam,
        onderwerp=onderwerp,
        inhoud=inhoud,
        status=str(BerichtStatus.KLAAR),
    )
    sessie.add(bericht)
    await sessie.flush()

    return str(params.get("logtekst", "")) or f"Bericht '{sjabloon.naam}' klaargezet"


@registreer_uitvoerder("support.noteer_afhandeling")
async def _noteer_afhandeling(
    _sessie: AsyncSession, params: dict[str, Any], _beslissing: Beslissing | None
) -> str:
    return str(params.get("tekst", ""))


async def markeer_bericht_verstuurd(sessie: AsyncSession, bericht_id: int) -> Bericht:
    """Leg vast dat een bericht daadwerkelijk is verstuurd.

    Zolang er geen kanaalkoppeling is, doet Sebas dit handmatig nadat hij de
    tekst heeft nagelezen — vergelijkbaar met de uitbetalingen.
    """
    bericht = await sessie.get(Bericht, bericht_id)
    if bericht is None:
        raise LookupError(f"Bericht {bericht_id} bestaat niet")
    bericht.status = str(BerichtStatus.VERSTUURD)
    bericht.verstuurd_op = nu()
    return bericht
