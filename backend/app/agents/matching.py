"""Matching-agent (paragraaf 3.2 van de bouwopdracht).

Verantwoordelijk voor: shifts koppelen aan medewerkers, no-shows signaleren en
het levelsysteem bijhouden.

Escalatie:
  tier 1  standaardmatches en levelupdates
  tier 2  herhaalde no-shows -> voorstel tot schorsing, tenzij Sebas ingrijpt
  tier 3  geschillen over gewerkte uren

Claude komt er alleen aan te pas wanneer de regels geen duidelijke winnaar
aanwijzen — bijvoorbeeld twee kandidaten op hetzelfde level. De onderbouwing
van die keuze gaat mee het activiteitenlog in.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base import BaseAgent
from app.agents.llm import vraag_gestructureerd_besluit
from app.core.domein import (
    Afdeling,
    MatchStatus,
    ReactieStatus,
    ShiftStatus,
    Tier,
    Urgentie,
    level_voor_uren,
)
from app.core.events import LevelBereikt, NoShowGesignaleerd, UrenGewerkt, WervingstekortGemeld
from app.core.tiers import Optie, Voorstel, registreer_uitvoerder
from app.db.models import Beslissing, Level, Match, Reactie, Shift, User

#: Weekdagafkortingen zoals ze in ``User.beschikbare_dagen`` staan.
DAGEN = ("ma", "di", "wo", "do", "vr", "za", "zo")

#: Vanaf dit aantal no-shows stelt de agent schorsing voor (tier 2).
NO_SHOW_DREMPEL = 3

SYSTEEMPROMPT = """Je bent de Matching-agent van WOSZ, een horecapersoneelsplatform in Zandvoort.

Je koppelt medewerkers aan shifts bij strandtenten en horecazaken. Je krijgt een
shift met de eisen en een lijst kandidaten die alle harde criteria al hebben
gehaald (juiste functie, beschikbaar op die dag, niet geschorst, geen dubbele
boeking). Jouw taak is alleen nog de beste kiezen.

Weeg in deze volgorde:
1. Ervaring met de gevraagde functie.
2. Levelprioriteit: medewerkers die dit seizoen meer uren hebben gemaakt,
   krijgen voorrang — dat is de belofte van het levelsysteem.
3. Betrouwbaarheid: eerdere no-shows tellen negatief.
4. Spreiding: is iemand deze week al vaak ingezet, gun het dan een ander.

Geef een korte, feitelijke onderbouwing in het Nederlands. Die tekst komt
letterlijk in het activiteitenlog dat de eigenaar leest, dus schrijf hem voor
een mens: één zin, geen jargon, geen opsomming."""

KANDIDAAT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "medewerker_id": {
            "type": "integer",
            "description": "Het id van de kandidaat die de shift krijgt.",
        },
        "onderbouwing": {
            "type": "string",
            "description": (
                "Eén zin in het Nederlands waarom deze kandidaat de beste keuze is. "
                "Komt letterlijk in het activiteitenlog."
            ),
        },
    },
    "required": ["medewerker_id", "onderbouwing"],
    "additionalProperties": False,
}


class MatchingAgent(BaseAgent):
    afdeling = Afdeling.MATCHING
    systeemprompt = SYSTEEMPROMPT

    # -- shifts matchen ----------------------------------------------------

    async def match_open_shifts(self, sessie: AsyncSession) -> list[dict[str, Any]]:
        """Loop alle open shifts langs en vul ze waar mogelijk.

        Geeft per shift terug wat er is gebeurd, zodat de API-laag en de tests
        kunnen zien wat de agent heeft gedaan.
        """
        resultaat = await sessie.execute(
            select(Shift)
            .where(Shift.status.in_([str(ShiftStatus.OPEN), str(ShiftStatus.DEELS_GEMATCHT)]))
            .order_by(Shift.datum, Shift.id)
        )
        verslag: list[dict[str, Any]] = []
        for shift in resultaat.scalars().all():
            verslag.append(await self.match_shift(sessie, shift))
        return verslag

    async def match_shift(self, sessie: AsyncSession, shift: Shift) -> dict[str, Any]:
        """Vul één shift tot het gevraagde aantal plekken vol."""
        bedrijf_naam = await self._bedrijf_naam(sessie, shift.bedrijf_id)
        gekoppeld: list[str] = []

        while True:
            open_plekken = await self._open_plekken(sessie, shift)
            if open_plekken <= 0:
                break

            kandidaten = await self._kandidaten(sessie, shift)
            if not kandidaten:
                break

            keuze, onderbouwing, door_llm = await self._kies_kandidaat(
                sessie, shift, kandidaten, bedrijf_naam
            )
            await self.plan_kandidaat_in(
                sessie,
                shift,
                keuze,
                onderbouwing=onderbouwing,
                door_llm=door_llm,
                bedrijf_naam=bedrijf_naam,
            )
            gekoppeld.append(keuze.naam)

        resterend = await self._open_plekken(sessie, shift)
        await self._werk_shiftstatus_bij(sessie, shift)

        if resterend > 0:
            # Marketing hoort te weten dat er te weinig mensen zijn. Dat gaat via
            # een gestructureerd event, niet via een bericht aan de Marketing-agent.
            await self.publiceer(
                sessie,
                WervingstekortGemeld(
                    functie=shift.functie,
                    open_plekken=resterend,
                    datum=shift.datum.isoformat(),
                ),
            )

        return {
            "shift_id": shift.id,
            "functie": shift.functie,
            "bedrijf": bedrijf_naam,
            "gematcht": gekoppeld,
            "open_plekken": resterend,
        }

    async def kandidaten_voor(self, sessie: AsyncSession, shift: Shift) -> list[User]:
        """Wie er voor deze shift in aanmerking komt.

        Publiek omdat het horecascherm dezelfde lijst toont als waaruit de agent
        kiest. Twee lijsten die uiteen kunnen lopen zou betekenen dat een bedrijf
        iemand aanklikt die de agent zou weigeren.
        """
        return await self._kandidaten(sessie, shift)

    async def plan_kandidaat_in(
        self,
        sessie: AsyncSession,
        shift: Shift,
        kandidaat: User,
        *,
        onderbouwing: str,
        door_llm: bool = False,
        bedrijf_naam: str | None = None,
    ) -> None:
        """Leg één match vast via het normale uitvoerpad.

        Ook wanneer het bedrijf zelf iemand aanwijst loopt het hierlangs, zodat
        de actie in het activiteitenlog belandt en de shiftstatus meebeweegt.
        """
        if bedrijf_naam is None:
            bedrijf_naam = await self._bedrijf_naam(sessie, shift.bedrijf_id)

        await self.voer_uit(
            sessie,
            Voorstel(
                afdeling=self.afdeling,
                tier=Tier.ZELFSTANDIG,
                logtekst=(
                    f"Shift {shift.functie} bij {bedrijf_naam} gematcht met {kandidaat.naam}"
                ),
                actie={
                    "uitvoerder": "matching.bevestig_match",
                    "params": {
                        "shift_id": shift.id,
                        "medewerker_id": kandidaat.id,
                        "onderbouwing": onderbouwing,
                        "door_llm": door_llm,
                        "bedrijf_naam": bedrijf_naam,
                    },
                },
            ),
        )
        await self._werk_shiftstatus_bij(sessie, shift)

    async def _kies_kandidaat(
        self,
        sessie: AsyncSession,
        shift: Shift,
        kandidaten: list[User],
        bedrijf_naam: str,
    ) -> tuple[User, str, bool]:
        """Kies de beste kandidaat.

        Triviaal geval (één kandidaat, of een duidelijk levelverschil) gaat op
        regels. Pas als de kop-aan-kop staat, vragen we Claude om te kiezen.
        """
        profielen = [await self._profiel(sessie, k, shift) for k in kandidaten]
        # Wie zelf op de shift heeft gereageerd gaat voor. Dat is geen voorrang
        # op level maar een filter ervoor: binnen de groep die gereageerd heeft,
        # blijft de levelvolgorde onverkort gelden.
        profielen.sort(
            key=lambda p: (not p["gereageerd"], -p["seizoen_uren"], p["no_shows"], p["id"])
        )

        beste = profielen[0]
        gelijkwaardig = [
            p
            for p in profielen
            if p["gereageerd"] == beste["gereageerd"]
            and p["level"] == beste["level"]
            and p["no_shows"] == beste["no_shows"]
        ]

        if len(gelijkwaardig) > 1:
            besluit = await self._vraag_claude(shift, bedrijf_naam, gelijkwaardig)
            if besluit is not None:
                gekozen_id, onderbouwing = besluit
                kandidaat = next((k for k in kandidaten if k.id == gekozen_id), None)
                if kandidaat is not None:
                    return kandidaat, onderbouwing, True

        kandidaat = next(k for k in kandidaten if k.id == beste["id"])
        aanhef = (
            "Zelf gereageerd op deze shift en de hoogste levelprioriteit"
            if beste["gereageerd"]
            else "Hoogste levelprioriteit"
        )
        onderbouwing = (
            f"{aanhef} ({beste['level_naam']}, "
            f"{beste['seizoen_uren']:.0f} uur dit seizoen) en ervaring met {shift.functie}."
        )
        return kandidaat, onderbouwing, False

    async def _vraag_claude(
        self, shift: Shift, bedrijf_naam: str, profielen: list[dict[str, Any]]
    ) -> tuple[int, str] | None:
        regels = "\n".join(
            f"- id {p['id']}: {p['naam']}, level {p['level']} ({p['level_naam']}), "
            f"{p['seizoen_uren']:.0f} uur dit seizoen, {p['no_shows']} no-show(s), "
            f"functies: {', '.join(p['functies']) or 'onbekend'}, "
            f"{p['shifts_deze_week']} shift(s) deze week"
            + (", heeft zelf op deze shift gereageerd" if p["gereageerd"] else "")
            for p in profielen
        )
        situatie = (
            f"Shift: {shift.functie} bij {bedrijf_naam} op {shift.datum.isoformat()} "
            f"({shift.tijd}), {shift.duur_uren:.0f} uur.\n\n"
            f"Kandidaten die alle harde criteria halen:\n{regels}\n\n"
            "Kies wie deze shift krijgt."
        )
        besluit = await vraag_gestructureerd_besluit(
            systeemprompt=self.systeemprompt,
            situatie=situatie,
            tool_naam="kies_kandidaat",
            tool_beschrijving=(
                "Leg vast welke kandidaat de shift krijgt en waarom. Kies uitsluitend "
                "uit de aangeboden kandidaten."
            ),
            schema=KANDIDAAT_SCHEMA,
        )
        if not besluit:
            return None

        toegestane_ids = {p["id"] for p in profielen}
        gekozen = besluit.get("medewerker_id")
        onderbouwing = str(besluit.get("onderbouwing", "")).strip()
        if gekozen not in toegestane_ids or not onderbouwing:
            # Het model koos buiten de lijst of gaf geen onderbouwing: negeren en
            # op regels terugvallen. De agent mag nooit een niet-aangeboden
            # kandidaat inplannen.
            return None
        return int(gekozen), onderbouwing

    # -- uren en levels ----------------------------------------------------

    async def registreer_gewerkte_uren(
        self, sessie: AsyncSession, match_id: int, uren: float
    ) -> dict[str, Any]:
        """Boek gewerkte uren, werk het level bij en meld het aan Financieel."""
        match = await sessie.get(Match, match_id)
        if match is None:
            raise LookupError(f"Match {match_id} bestaat niet")

        shift = await sessie.get(Shift, match.shift_id)
        medewerker = await sessie.get(User, match.medewerker_id)
        if shift is None or medewerker is None:
            raise LookupError(f"Match {match_id} verwijst naar ontbrekende gegevens")

        match.status = str(MatchStatus.GEWERKT)
        match.uren_gewerkt = uren

        level = await self._level(sessie, medewerker.id)
        vorig_level = level.huidig_level
        level.seizoen_uren += uren
        nieuw = level_voor_uren(level.seizoen_uren)
        level.huidig_level = nieuw["level"]

        await self.voer_uit(
            sessie,
            Voorstel(
                afdeling=self.afdeling,
                tier=Tier.ZELFSTANDIG,
                logtekst=(
                    f"{uren:.0f} gewerkte uren geregistreerd voor {medewerker.naam} "
                    f"({level.seizoen_uren:.0f} uur dit seizoen)"
                ),
                actie={"uitvoerder": "matching.geen_actie", "params": {}},
            ),
        )

        await self.publiceer(
            sessie,
            UrenGewerkt(
                match_id=match.id,
                medewerker_id=medewerker.id,
                bedrijf_id=shift.bedrijf_id,
                uren=uren,
                datum=shift.datum.isoformat(),
            ),
        )

        if nieuw["level"] > vorig_level:
            await self.voer_uit(
                sessie,
                Voorstel(
                    afdeling=self.afdeling,
                    tier=Tier.ZELFSTANDIG,
                    logtekst=(
                        f"{medewerker.naam} bereikte level {nieuw['level']} — {nieuw['naam']}"
                    ),
                    actie={"uitvoerder": "matching.geen_actie", "params": {}},
                ),
            )
            await self.publiceer(
                sessie,
                LevelBereikt(
                    medewerker_id=medewerker.id,
                    medewerker_naam=medewerker.naam,
                    nieuw_level=nieuw["level"],
                    level_naam=nieuw["naam"],
                    bonus_bedrag_cent=int(nieuw["bonus"]) * 100,
                    seizoen_uren=level.seizoen_uren,
                ),
            )

        return {
            "match_id": match.id,
            "uren": uren,
            "seizoen_uren": level.seizoen_uren,
            "level": nieuw["level"],
            "level_naam": nieuw["naam"],
        }

    # -- no-shows ----------------------------------------------------------

    async def signaleer_no_show(self, sessie: AsyncSession, match_id: int) -> dict[str, Any]:
        """Signaleer een no-show en waarschuw de medewerker via Support.

        Levert altijd twee logregels op: één met afdeling ``matching`` (deze
        agent) en één met afdeling ``support`` (de Support-agent, nadat die het
        event heeft opgepikt). Dat is precies wat hoofdstuk 8 vraagt.
        """
        match = await sessie.get(Match, match_id)
        if match is None:
            raise LookupError(f"Match {match_id} bestaat niet")

        shift = await sessie.get(Shift, match.shift_id)
        medewerker = await sessie.get(User, match.medewerker_id)
        if shift is None or medewerker is None:
            raise LookupError(f"Match {match_id} verwijst naar ontbrekende gegevens")

        match.status = str(MatchStatus.NO_SHOW)
        bedrijf_naam = await self._bedrijf_naam(sessie, shift.bedrijf_id)
        aantal = await self._aantal_no_shows(sessie, medewerker.id)

        await self.voer_uit(
            sessie,
            Voorstel(
                afdeling=self.afdeling,
                tier=Tier.ZELFSTANDIG,
                logtekst=f"No-show gesignaleerd bij {bedrijf_naam} ({medewerker.naam})",
                actie={"uitvoerder": "matching.geen_actie", "params": {}},
            ),
        )

        await self.publiceer(
            sessie,
            NoShowGesignaleerd(
                match_id=match.id,
                medewerker_id=medewerker.id,
                medewerker_naam=medewerker.naam,
                bedrijf_naam=bedrijf_naam,
                aantal_no_shows=aantal,
            ),
        )

        beslissing_id = None
        if aantal >= NO_SHOW_DREMPEL:
            uitkomst = await self.voer_uit(
                sessie,
                Voorstel(
                    afdeling=self.afdeling,
                    tier=Tier.TENZIJ,
                    urgentie=Urgentie.DEZE_WEEK,
                    titel=f"Schorsing voorstellen voor {medewerker.naam}",
                    situatie=(
                        f"{medewerker.naam} heeft nu {aantal} no-shows dit seizoen, "
                        f"de laatste bij {bedrijf_naam} op {shift.datum.isoformat()}. "
                        "Zonder ingrijpen wordt de medewerker geschorst voor nieuwe shifts."
                    ),
                    aanbeveling=(
                        "AI-advies: schorsen — bij dit aantal no-shows lopen bedrijven "
                        "risico op onbemande shifts."
                    ),
                    opties=[
                        Optie(
                            naam="Schorsen",
                            gevolg="Medewerker krijgt geen nieuwe shifts toegewezen",
                            actie={
                                "uitvoerder": "matching.schors_medewerker",
                                "params": {
                                    "medewerker_id": medewerker.id,
                                    "naam": medewerker.naam,
                                },
                            },
                        ),
                        Optie(
                            naam="Niet schorsen",
                            gevolg="Medewerker blijft beschikbaar, je neemt zelf contact op",
                            actie={
                                "uitvoerder": "matching.geen_actie",
                                "params": {
                                    "reden": (
                                        f"Schorsing van {medewerker.naam} afgewezen door Sebas"
                                    )
                                },
                            },
                        ),
                    ],
                    logtekst=f"Herhaalde no-shows van {medewerker.naam} ({aantal}x)",
                ),
            )
            beslissing_id = uitkomst.beslissing_id

        return {
            "match_id": match.id,
            "medewerker": medewerker.naam,
            "aantal_no_shows": aantal,
            "beslissing_id": beslissing_id,
        }

    # -- urengeschil (tier 3) ---------------------------------------------

    async def meld_urengeschil(
        self,
        sessie: AsyncSession,
        match_id: int,
        *,
        uren_medewerker: float,
        uren_bedrijf: float,
    ) -> int | None:
        """Leg een geschil over gewerkte uren voor aan Sebas.

        Tier 3: hier gebeurt niets tot Sebas kiest. De agent boekt geen van
        beide urenstanden vast, ook niet 'voorlopig'.
        """
        match = await sessie.get(Match, match_id)
        if match is None:
            raise LookupError(f"Match {match_id} bestaat niet")

        shift = await sessie.get(Shift, match.shift_id)
        medewerker = await sessie.get(User, match.medewerker_id)
        if shift is None or medewerker is None:
            raise LookupError(f"Match {match_id} verwijst naar ontbrekende gegevens")

        bedrijf_naam = await self._bedrijf_naam(sessie, shift.bedrijf_id)

        uitkomst = await self.voer_uit(
            sessie,
            Voorstel(
                afdeling=self.afdeling,
                tier=Tier.WACHT,
                urgentie=Urgentie.DRINGEND,
                titel=f"Urengeschil {medewerker.naam} en {bedrijf_naam}",
                situatie=(
                    f"{medewerker.naam} registreerde {uren_medewerker:.1f} uur voor de shift "
                    f"van {shift.datum.isoformat()} bij {bedrijf_naam}; het bedrijf meldt "
                    f"{uren_bedrijf:.1f} uur. Er is niets uitbetaald of gefactureerd zolang "
                    "dit openstaat."
                ),
                aanbeveling=(
                    "AI-advies: geen automatische keuze — een urengeschil raakt zowel de "
                    "uitbetaling als de relatie met het bedrijf."
                ),
                opties=[
                    Optie(
                        naam=f"Uren medewerker aanhouden ({uren_medewerker:.1f})",
                        gevolg="Deze uren worden vastgelegd en doorgegeven aan Financieel",
                        actie={
                            "uitvoerder": "matching.corrigeer_uren",
                            "params": {"match_id": match.id, "uren": uren_medewerker},
                        },
                    ),
                    Optie(
                        naam=f"Uren bedrijf aanhouden ({uren_bedrijf:.1f})",
                        gevolg="Deze uren worden vastgelegd en doorgegeven aan Financieel",
                        actie={
                            "uitvoerder": "matching.corrigeer_uren",
                            "params": {"match_id": match.id, "uren": uren_bedrijf},
                        },
                    ),
                    Optie(
                        naam="Zelf bellen voordat er iets vastligt",
                        gevolg="Er wordt niets geboekt; jij neemt contact op met beide partijen",
                        actie={
                            "uitvoerder": "matching.geen_actie",
                            "params": {
                                "reden": (
                                    f"Urengeschil {medewerker.naam} / {bedrijf_naam}: "
                                    "Sebas neemt zelf contact op"
                                )
                            },
                        },
                    ),
                ],
                logtekst=f"Urengeschil gemeld tussen {medewerker.naam} en {bedrijf_naam}",
            ),
        )
        return uitkomst.beslissing_id

    # -- interne hulpfuncties ---------------------------------------------

    async def _open_plekken(self, sessie: AsyncSession, shift: Shift) -> int:
        resultaat = await sessie.execute(
            select(Match).where(
                Match.shift_id == shift.id,
                Match.status.notin_(
                    [str(MatchStatus.GEANNULEERD), str(MatchStatus.NO_SHOW)]
                ),
            )
        )
        bezet = len(list(resultaat.scalars().all()))
        return max(0, shift.aantal_gevraagd - bezet)

    async def _kandidaten(self, sessie: AsyncSession, shift: Shift) -> list[User]:
        """Alle medewerkers die aan de harde criteria voldoen."""
        dag = DAGEN[shift.datum.weekday()]

        resultaat = await sessie.execute(
            select(User).where(
                User.rol == "medewerker", User.actief.is_(True), User.geschorst.is_(False)
            )
        )
        alle = list(resultaat.scalars().all())

        # Iedereen die op deze shift al een match heeft gehad valt af, ook als
        # die is geannuleerd of op een no-show is uitgelopen. Wie zojuist heeft
        # afgezegd, moet niet meteen opnieuw op dezelfde shift worden gezet.
        al_gekoppeld = await sessie.execute(
            select(Match.medewerker_id).where(Match.shift_id == shift.id)
        )
        bezet_ids = set(al_gekoppeld.scalars().all())

        geschikt: list[User] = []
        for gebruiker in alle:
            if gebruiker.id in bezet_ids:
                continue
            functies = [f.lower() for f in (gebruiker.functies or [])]
            if functies and shift.functie.lower() not in functies:
                continue
            dagen = gebruiker.beschikbare_dagen or []
            if dagen and dag not in dagen:
                continue
            if await self._al_ingepland_op(sessie, gebruiker.id, shift.datum, shift.id):
                continue
            geschikt.append(gebruiker)
        return geschikt

    async def _al_ingepland_op(
        self, sessie: AsyncSession, medewerker_id: int, datum: date, huidige_shift_id: int
    ) -> bool:
        resultaat = await sessie.execute(
            select(Match)
            .join(Shift, Shift.id == Match.shift_id)
            .where(
                Match.medewerker_id == medewerker_id,
                Shift.datum == datum,
                Shift.id != huidige_shift_id,
                Match.status.notin_([str(MatchStatus.GEANNULEERD)]),
            )
        )
        return resultaat.scalars().first() is not None

    async def _profiel(
        self, sessie: AsyncSession, gebruiker: User, shift: Shift
    ) -> dict[str, Any]:
        level = await self._level(sessie, gebruiker.id)
        info = level_voor_uren(level.seizoen_uren)
        return {
            "id": gebruiker.id,
            "naam": gebruiker.naam,
            "functies": list(gebruiker.functies or []),
            "seizoen_uren": level.seizoen_uren,
            "level": info["level"],
            "level_naam": info["naam"],
            "no_shows": await self._aantal_no_shows(sessie, gebruiker.id),
            "shifts_deze_week": await self._shifts_in_week(sessie, gebruiker.id, shift.datum),
            "gereageerd": await self._heeft_gereageerd(sessie, shift.id, gebruiker.id),
        }

    async def _heeft_gereageerd(
        self, sessie: AsyncSession, shift_id: int, medewerker_id: int
    ) -> bool:
        resultaat = await sessie.execute(
            select(Reactie).where(
                Reactie.shift_id == shift_id,
                Reactie.medewerker_id == medewerker_id,
                Reactie.status == str(ReactieStatus.OPEN),
            )
        )
        return resultaat.scalars().first() is not None

    async def _level(self, sessie: AsyncSession, medewerker_id: int) -> Level:
        level = await sessie.get(Level, medewerker_id)
        if level is None:
            level = Level(medewerker_id=medewerker_id, huidig_level=1, seizoen_uren=0.0)
            sessie.add(level)
            await sessie.flush()
        return level

    async def _aantal_no_shows(self, sessie: AsyncSession, medewerker_id: int) -> int:
        resultaat = await sessie.execute(
            select(Match).where(
                Match.medewerker_id == medewerker_id,
                Match.status == str(MatchStatus.NO_SHOW),
            )
        )
        return len(list(resultaat.scalars().all()))

    async def _shifts_in_week(
        self, sessie: AsyncSession, medewerker_id: int, rond: date
    ) -> int:
        from datetime import timedelta

        start = rond - timedelta(days=rond.weekday())
        eind = start + timedelta(days=6)
        resultaat = await sessie.execute(
            select(Match)
            .join(Shift, Shift.id == Match.shift_id)
            .where(
                Match.medewerker_id == medewerker_id,
                Shift.datum >= start,
                Shift.datum <= eind,
                Match.status.notin_([str(MatchStatus.GEANNULEERD)]),
            )
        )
        return len(list(resultaat.scalars().all()))

    async def _bedrijf_naam(self, sessie: AsyncSession, bedrijf_id: int) -> str:
        from app.db.models import Bedrijf

        bedrijf = await sessie.get(Bedrijf, bedrijf_id)
        return bedrijf.naam if bedrijf else f"bedrijf {bedrijf_id}"

    async def _werk_shiftstatus_bij(self, sessie: AsyncSession, shift: Shift) -> None:
        open_plekken = await self._open_plekken(sessie, shift)
        if open_plekken == 0:
            shift.status = str(ShiftStatus.GEMATCHT)
        elif open_plekken < shift.aantal_gevraagd:
            shift.status = str(ShiftStatus.DEELS_GEMATCHT)
        else:
            shift.status = str(ShiftStatus.OPEN)


# ---------------------------------------------------------------------------
# Uitvoerders — wat de tier-engine daadwerkelijk uitvoert
# ---------------------------------------------------------------------------


@registreer_uitvoerder("matching.bevestig_match")
async def _bevestig_match(
    sessie: AsyncSession, params: dict[str, Any], _beslissing: Beslissing | None
) -> str:
    match = Match(
        shift_id=params["shift_id"],
        medewerker_id=params["medewerker_id"],
        status=str(MatchStatus.BEVESTIGD),
        onderbouwing=params.get("onderbouwing"),
        door_llm=bool(params.get("door_llm", False)),
    )
    sessie.add(match)
    await sessie.flush()

    # De reactie is nu ingelost; hij hoeft niet nog een keer meegewogen te worden.
    gereageerd = await sessie.execute(
        select(Reactie).where(
            Reactie.shift_id == match.shift_id,
            Reactie.medewerker_id == match.medewerker_id,
            Reactie.status == str(ReactieStatus.OPEN),
        )
    )
    for reactie in gereageerd.scalars().all():
        reactie.status = str(ReactieStatus.GEHONOREERD)

    medewerker = await sessie.get(User, params["medewerker_id"])
    naam = medewerker.naam if medewerker else f"medewerker {params['medewerker_id']}"
    bedrijf = params.get("bedrijf_naam", "")
    onderbouwing = params.get("onderbouwing") or ""
    kop = f"Shift bij {bedrijf} gematcht met {naam}" if bedrijf else f"Shift gematcht met {naam}"
    return f"{kop} — {onderbouwing}" if onderbouwing else kop


@registreer_uitvoerder("matching.schors_medewerker")
async def _schors_medewerker(
    sessie: AsyncSession, params: dict[str, Any], _beslissing: Beslissing | None
) -> str:
    medewerker = await sessie.get(User, params["medewerker_id"])
    if medewerker is None:
        raise LookupError(f"Medewerker {params['medewerker_id']} bestaat niet")
    medewerker.geschorst = True
    return f"{medewerker.naam} geschorst voor nieuwe shifts na herhaalde no-shows"


@registreer_uitvoerder("matching.corrigeer_uren")
async def _corrigeer_uren(
    sessie: AsyncSession, params: dict[str, Any], _beslissing: Beslissing | None
) -> str:
    match = await sessie.get(Match, params["match_id"])
    if match is None:
        raise LookupError(f"Match {params['match_id']} bestaat niet")
    uren = float(params["uren"])
    match.uren_gewerkt = uren
    match.status = str(MatchStatus.GEWERKT)

    shift = await sessie.get(Shift, match.shift_id)
    if shift is not None:
        from app.core.events import publiceer

        await publiceer(
            sessie,
            UrenGewerkt(
                match_id=match.id,
                medewerker_id=match.medewerker_id,
                bedrijf_id=shift.bedrijf_id,
                uren=uren,
                datum=shift.datum.isoformat(),
            ),
        )
    return f"Urengeschil beslecht op {uren:.1f} uur en doorgegeven aan Financieel"


@registreer_uitvoerder("matching.geen_actie")
async def _geen_actie(
    _sessie: AsyncSession, params: dict[str, Any], _beslissing: Beslissing | None
) -> str:
    return str(params.get("reden", ""))
