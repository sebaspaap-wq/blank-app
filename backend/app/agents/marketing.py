"""Marketing-agent (paragraaf 3.1 van de bouwopdracht).

Verantwoordelijk voor: social content plannen, advertentiebudget bijsturen
binnen een vooraf ingestelde bandbreedte, en A/B-testresultaten interpreteren.

Escalatie:
  tier 1  contentplanning binnen de bestaande huisstijl, kleine budgetschuiven
          binnen de bandbreedte
  tier 3  nieuw budget aanvragen, een nieuwe hoek of campagne-richting, en
          resultaten die meer dan 25% van de verwachting afwijken

Drie grenzen zijn architecturaal opgelost:

**Er is geen Meta Ads-koppeling.** Het systeem kan geen advertentie publiceren
en geen budget in Ads Manager wijzigen. Een budgetschuif levert een
``Budgetmutatie`` op: een werkinstructie die Sebas zelf uitvoert, net zoals bij
uitbetalingen. Dat is niet alleen omdat de Meta Business-verificatie nog loopt —
het houdt de onomkeerbare stap bij een mens.

**Een budgetschuif kan geen nieuw geld maken.** ``verschuif_budget`` is een
overboeking tussen twee campagnes: het haalt hetzelfde bedrag ergens vandaan als
het ergens neerzet. Het totaal is behouden per constructie. "Nieuw budget
aanvragen" is daarom een aparte methode, en die is tier 3.

**De agent verzint geen nieuwe hoek.** Content plannen kan alleen op een hoek
die in ``huisstijl_hoeken`` staat en is goedgekeurd. Claude schrijft binnen zo'n
hoek een concepttekst; een nieuwe richting voorstellen loopt via tier 3. En
publiceren bestaat niet: items landen op de kalender, Sebas plaatst ze.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base import BaseAgent
from app.agents.llm import vraag_gestructureerd_besluit
from app.core.domein import (
    Afdeling,
    BudgetmutatieStatus,
    CampagneStatus,
    ContentStatus,
    SocialKanaal,
    Tier,
    Urgentie,
    nu,
)
from app.core.events import WervingstekortGemeld, handelt
from app.core.tiers import Optie, Voorstel, registreer_uitvoerder
from app.db.models import (
    AgentEvent,
    Beslissing,
    Budgetmutatie,
    Campagne,
    CampagneResultaat,
    Contentitem,
    Hoek,
)

#: Afwijking van de verwachting waarboven de agent altijd escaleert (§3.1).
AFWIJKING_DREMPEL_PCT = 25.0

#: Aantal openstaande plekken waarboven een wervingstekort ook om budget vraagt.
BUDGET_BIJSTUREN_VANAF_PLEKKEN = 2


class BandbreedteOverschredenError(ValueError):
    """Een budgetschuif is groter dan de campagne zelfstandig mag verschuiven."""


SYSTEEMPROMPT = """Je bent de Marketing-agent van WOSZ, een horecapersoneelsplatform in Zandvoort.

WOSZ koppelt horecamedewerkers aan shifts bij strandtenten. Je doelgroep is
jongeren en studenten in de regio Zandvoort/Haarlem die bij willen verdienen aan
het strand.

Je schrijft een korte social post binnen een bestaande, goedgekeurde invalshoek.
Die hoek krijg je mee, inclusief de toon die erbij hoort. Blijf daarbinnen: je
bedenkt geen nieuwe hoek en geen nieuwe belofte.

Harde regels voor je tekst:
- Noem geen bedragen, uurlonen, tarieven of bonussen. Wat iemand verdient
  verschilt per shift en per bedrijf.
- Doe geen toezeggingen over voorwaarden, contracten of gegarandeerd werk.
- Schrijf in het Nederlands, spreektaal, kort. Eén haak en een paar regels.

Je schrijft één haak (de openingszin die iemand laat stoppen met scrollen) en
een korte begeleidende tekst."""

CONTENT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "haak": {
            "type": "string",
            "description": "De openingszin. Kort, spreektaal, maximaal ongeveer 80 tekens.",
        },
        "tekst": {
            "type": "string",
            "description": (
                "De begeleidende tekst onder de haak. Een paar regels, Nederlands, "
                "zonder bedragen of toezeggingen."
            ),
        },
    },
    "required": ["haak", "tekst"],
    "additionalProperties": False,
}


class MarketingAgent(BaseAgent):
    afdeling = Afdeling.MARKETING
    systeemprompt = SYSTEEMPROMPT

    # -- content plannen (tier 1) ------------------------------------------

    async def plan_content(
        self,
        sessie: AsyncSession,
        *,
        hoek_id: int,
        geplande_datum: date,
        kanaal: SocialKanaal = SocialKanaal.INSTAGRAM,
        aanleiding: str = "",
        campagne_id: int | None = None,
    ) -> dict[str, Any]:
        """Zet één item op de content-kalender (tier 1).

        Werkt alleen op een goedgekeurde hoek. Wil je iets buiten de huisstijl,
        dan is dat een nieuwe richting en loopt het via ``stel_nieuwe_hoek_voor``.
        """
        hoek = await sessie.get(Hoek, hoek_id)
        if hoek is None:
            raise LookupError(f"Hoek {hoek_id} bestaat niet")
        if not hoek.goedgekeurd:
            raise PermissionError(
                f"Hoek '{hoek.naam}' is niet goedgekeurd; contentplanning hierop is "
                "geen tier 1-actie. Gebruik stel_nieuwe_hoek_voor()."
            )

        haak, tekst, door_llm = await self._schrijf_concept(hoek, aanleiding)

        uitkomst = await self.voer_uit(
            sessie,
            Voorstel(
                afdeling=self.afdeling,
                tier=Tier.ZELFSTANDIG,
                logtekst=(
                    f"Post ingepland voor {geplande_datum.isoformat()} op "
                    f"{kanaal} — hoek '{hoek.naam}'"
                ),
                actie={
                    "uitvoerder": "marketing.plan_contentitem",
                    "params": {
                        "hoek_id": hoek.id,
                        "hoek_naam": hoek.naam,
                        "geplande_datum": geplande_datum.isoformat(),
                        "kanaal": str(kanaal),
                        "campagne_id": campagne_id,
                        "haak": haak,
                        "concepttekst": tekst,
                        "aanleiding": aanleiding,
                        "door_llm": door_llm,
                    },
                },
            ),
        )
        return {"logtekst": uitkomst.logtekst, "haak": haak, "door_llm": door_llm}

    async def plan_week(
        self, sessie: AsyncSession, *, vanaf: date | None = None, aantal: int = 3
    ) -> list[dict[str, Any]]:
        """Vul de komende week met content op de bestaande hoeken (tier 1)."""
        vanaf = vanaf or nu().date()
        hoeken = await self._goedgekeurde_hoeken(sessie)
        if not hoeken:
            return []

        verslag: list[dict[str, Any]] = []
        for index in range(aantal):
            hoek = hoeken[index % len(hoeken)]
            datum = vanaf + timedelta(days=index * 2 + 1)
            if await self._al_gepland(sessie, datum):
                continue
            verslag.append(
                await self.plan_content(
                    sessie,
                    hoek_id=hoek.id,
                    geplande_datum=datum,
                    aanleiding="weekplanning",
                )
            )
        return verslag

    async def _schrijf_concept(self, hoek: Hoek, aanleiding: str) -> tuple[str, str, bool]:
        """Laat Claude een concepttekst schrijven binnen de gegeven hoek.

        Zonder API-key valt de agent terug op de voorbeelden die bij de hoek
        horen — teksten die Sebas zelf heeft aangeleverd. Er wordt dus nooit
        niets gepland omdat het model niet beschikbaar is.
        """
        situatie = (
            f"Invalshoek: {hoek.naam}\n"
            f"Waar die over gaat: {hoek.omschrijving}\n"
            f"Toon: {hoek.toon}\n"
        )
        if hoek.voorbeelden:
            situatie += "Eerdere posts op deze hoek:\n" + "\n".join(
                f"- {v}" for v in hoek.voorbeelden
            )
        if aanleiding:
            situatie += f"\n\nAanleiding voor deze post: {aanleiding}"
        situatie += "\n\nSchrijf één nieuwe post binnen deze hoek."

        besluit = await vraag_gestructureerd_besluit(
            systeemprompt=self.systeemprompt,
            situatie=situatie,
            tool_naam="schrijf_post",
            tool_beschrijving=(
                "Leg de haak en de begeleidende tekst van één social post vast, "
                "binnen de opgegeven invalshoek."
            ),
            schema=CONTENT_SCHEMA,
        )

        if besluit:
            haak = str(besluit.get("haak", "")).strip()
            tekst = str(besluit.get("tekst", "")).strip()
            if haak and tekst and not _bevat_bedrag(f"{haak} {tekst}"):
                return haak, tekst, True
            # Het model noemde een bedrag of leverde niets bruikbaars: niet
            # gebruiken. Een post met een bedrag erin is een toezegging.

        voorbeeld = hoek.voorbeelden[0] if hoek.voorbeelden else hoek.naam
        return (
            voorbeeld,
            f"{hoek.omschrijving} Reageer op de shifts in de app.",
            False,
        )

    # -- budget verschuiven (tier 1) ---------------------------------------

    async def verschuif_budget(
        self,
        sessie: AsyncSession,
        *,
        van_campagne_id: int,
        naar_campagne_id: int,
        bedrag_cent: int,
        reden: str,
    ) -> dict[str, Any]:
        """Verschuif budget tussen twee campagnes (tier 1 binnen de bandbreedte).

        Dit is een overboeking: hetzelfde bedrag gaat er bij de ene campagne af
        als er bij de andere bij komt. Het totale dagbudget verandert dus niet —
        niet omdat de agent zich inhoudt, maar omdat deze functie geen andere
        vorm kent. Meer budget vragen kan alleen via ``vraag_budgetverhoging``,
        en dat is tier 3.
        """
        van = await sessie.get(Campagne, van_campagne_id)
        naar = await sessie.get(Campagne, naar_campagne_id)
        if van is None or naar is None:
            raise LookupError("Onbekende campagne bij budgetverschuiving")
        if van.id == naar.id:
            raise ValueError("Bron- en doelcampagne zijn hetzelfde")
        if bedrag_cent <= 0:
            raise ValueError("Een verschuiving moet een positief bedrag zijn")

        maximum = self.maximale_verschuiving_cent(van)
        if bedrag_cent > maximum:
            raise BandbreedteOverschredenError(
                f"€{bedrag_cent / 100:.2f} is meer dan de bandbreedte van "
                f"'{van.naam}' toelaat (max €{maximum / 100:.2f} per dag, "
                f"{van.bandbreedte_pct:.0f}% van €{van.dagbudget_cent / 100:.2f}). "
                "Leg dit voor aan Sebas in plaats van het zelfstandig te doen."
            )

        uitkomst = await self.voer_uit(
            sessie,
            Voorstel(
                afdeling=self.afdeling,
                tier=Tier.ZELFSTANDIG,
                logtekst=(
                    f"€{bedrag_cent / 100:.2f} verschoven van '{van.naam}' naar "
                    f"'{naar.naam}' — {reden}"
                ),
                actie={
                    "uitvoerder": "marketing.verschuif_budget",
                    "params": {
                        "van_campagne_id": van.id,
                        "naar_campagne_id": naar.id,
                        "bedrag_cent": bedrag_cent,
                        "reden": reden,
                    },
                },
            ),
        )
        return {"logtekst": uitkomst.logtekst, "bedrag_cent": bedrag_cent}

    @staticmethod
    def maximale_verschuiving_cent(campagne: Campagne) -> int:
        """Hoeveel deze campagne per dag zelfstandig mag afstaan."""
        return int(campagne.dagbudget_cent * campagne.bandbreedte_pct / 100)

    # -- tier 3: nieuw budget, nieuwe hoek, tegenvallende resultaten -------

    async def vraag_budgetverhoging(
        self, sessie: AsyncSession, *, campagne_id: int, extra_cent: int, reden: str
    ) -> int | None:
        """Vraag om méér budget dan er nu is (tier 3).

        Dit is de enige weg naar een hoger totaalbudget, en die loopt altijd
        langs Sebas.
        """
        campagne = await sessie.get(Campagne, campagne_id)
        if campagne is None:
            raise LookupError(f"Campagne {campagne_id} bestaat niet")

        nieuw = campagne.dagbudget_cent + extra_cent
        uitkomst = await self.voer_uit(
            sessie,
            Voorstel(
                afdeling=self.afdeling,
                tier=Tier.WACHT,
                urgentie=Urgentie.DEZE_WEEK,
                titel=f"Advertentiebudget verhogen voor '{campagne.naam}'",
                situatie=(
                    f"{reden}\n\n"
                    f"Voorstel: dagbudget van €{campagne.dagbudget_cent / 100:.2f} naar "
                    f"€{nieuw / 100:.2f} (+€{extra_cent / 100:.2f} per dag, "
                    f"circa €{extra_cent * 30 / 100:.2f} per maand). Er is nog niets "
                    "gewijzigd; dat doe je zelf in Ads Manager."
                ),
                aanbeveling=(
                    "AI-advies: dit is nieuw geld, geen verschuiving — beoordeel het "
                    "tegen je maandbudget."
                ),
                opties=[
                    Optie(
                        naam="Goedkeuren",
                        gevolg="Komt op je werklijst; je past het zelf aan in Ads Manager",
                        actie={
                            "uitvoerder": "marketing.keur_budgetverhoging_goed",
                            "params": {
                                "campagne_id": campagne.id,
                                "extra_cent": extra_cent,
                                "reden": reden,
                            },
                        },
                    ),
                    Optie(
                        naam="Niet verhogen",
                        gevolg="Budget blijft gelijk; de agent stuurt bij binnen de bandbreedte",
                        actie={
                            "uitvoerder": "marketing.noteer",
                            "params": {
                                "tekst": (
                                    f"Budgetverhoging voor '{campagne.naam}' afgewezen"
                                )
                            },
                        },
                    ),
                ],
                logtekst=(
                    f"Budgetverhoging van €{extra_cent / 100:.2f}/dag voorgesteld voor "
                    f"'{campagne.naam}'"
                ),
            ),
        )
        return uitkomst.beslissing_id

    async def stel_nieuwe_hoek_voor(
        self, sessie: AsyncSession, *, naam: str, omschrijving: str, reden: str
    ) -> int | None:
        """Stel een nieuwe invalshoek voor (tier 3).

        Een nieuwe hoek is een nieuwe campagne-richting. De agent kan hem niet
        zelf goedkeuren: pas als Sebas kiest, komt de hoek in de huisstijl en
        mag er content op gepland worden.
        """
        uitkomst = await self.voer_uit(
            sessie,
            Voorstel(
                afdeling=self.afdeling,
                tier=Tier.WACHT,
                urgentie=Urgentie.DEZE_WEEK,
                titel=f"Nieuwe campagne-hoek: '{naam}'",
                situatie=(
                    f"{reden}\n\nVoorgestelde hoek: {omschrijving}\n\n"
                    "Er is nog geen content op deze hoek gepland; dat gebeurt pas "
                    "als je hem goedkeurt."
                ),
                aanbeveling=(
                    "AI-advies: een nieuwe hoek verandert hoe WOSZ overkomt — die keuze "
                    "hoort bij jou."
                ),
                opties=[
                    Optie(
                        naam="Hoek toevoegen aan de huisstijl",
                        gevolg="De agent mag hier voortaan zelfstandig content op plannen",
                        actie={
                            "uitvoerder": "marketing.voeg_hoek_toe",
                            "params": {"naam": naam, "omschrijving": omschrijving},
                        },
                    ),
                    Optie(
                        naam="Niet doen",
                        gevolg="We blijven bij de bestaande hoeken",
                        actie={
                            "uitvoerder": "marketing.noteer",
                            "params": {"tekst": f"Nieuwe hoek '{naam}' afgewezen"},
                        },
                    ),
                ],
                logtekst=f"Nieuwe campagne-hoek '{naam}' voorgesteld",
            ),
        )
        return uitkomst.beslissing_id

    async def beoordeel_resultaten(
        self, sessie: AsyncSession, *, datum: date | None = None
    ) -> list[dict[str, Any]]:
        """Vergelijk de resultaten met de verwachting.

        Wijkt een campagne meer dan 25% af, dan gaat het naar Sebas (tier 3).
        Binnen die marge stuurt de agent zelf bij met een verschuiving.
        """
        datum = datum or (nu().date() - timedelta(days=1))
        campagnes = await self._actieve_campagnes(sessie)
        bevindingen: list[dict[str, Any]] = []

        for campagne in campagnes:
            uitgaven, aanmeldingen = await self._dagcijfers(sessie, campagne.id, datum)
            if not aanmeldingen:
                continue
            verwacht = campagne.verwachte_kosten_per_aanmelding_cent
            if verwacht <= 0:
                continue

            werkelijk = round(uitgaven / aanmeldingen)
            afwijking = (werkelijk - verwacht) / verwacht * 100

            bevinding = {
                "campagne": campagne.naam,
                "verwacht_cent": verwacht,
                "werkelijk_cent": werkelijk,
                "afwijking_pct": round(afwijking, 1),
                "beslissing_id": None,
            }

            if afwijking > AFWIJKING_DREMPEL_PCT:
                bevinding["beslissing_id"] = await self._meld_tegenvaller(
                    sessie, campagne, verwacht, werkelijk, afwijking
                )
            else:
                await self.rapporteer(
                    sessie,
                    (
                        f"'{campagne.naam}' presteert binnen verwachting: "
                        f"€{werkelijk / 100:.2f} per aanmelding "
                        f"({afwijking:+.0f}% t.o.v. verwacht)"
                    ),
                    tier=Tier.ZELFSTANDIG,
                )
            bevindingen.append(bevinding)

        return bevindingen

    async def _meld_tegenvaller(
        self,
        sessie: AsyncSession,
        campagne: Campagne,
        verwacht: int,
        werkelijk: int,
        afwijking: float,
    ) -> int | None:
        uitkomst = await self.voer_uit(
            sessie,
            Voorstel(
                afdeling=self.afdeling,
                tier=Tier.WACHT,
                urgentie=Urgentie.DEZE_WEEK,
                titel=f"'{campagne.naam}' wijkt {afwijking:.0f}% af van de verwachting",
                situatie=(
                    f"De kosten per aanmelding zijn €{werkelijk / 100:.2f}, terwijl we "
                    f"€{verwacht / 100:.2f} verwachtten — {afwijking:.0f}% duurder. "
                    "Dat is meer dan de agent zelfstandig mag bijsturen, dus er is "
                    "niets gewijzigd."
                ),
                aanbeveling=(
                    "AI-advies: pauzeer of herzie deze campagne; bij deze afwijking "
                    "loopt de werving achter terwijl het budget wel wegloopt."
                ),
                opties=[
                    Optie(
                        naam="Campagne pauzeren",
                        gevolg="Komt op je werklijst; je pauzeert hem zelf in Ads Manager",
                        actie={
                            "uitvoerder": "marketing.pauzeer_campagne",
                            "params": {"campagne_id": campagne.id},
                        },
                    ),
                    Optie(
                        naam="Laten lopen",
                        gevolg="Campagne blijft actief; de agent blijft meten",
                        actie={
                            "uitvoerder": "marketing.noteer",
                            "params": {
                                "tekst": f"'{campagne.naam}' blijft actief op jouw verzoek"
                            },
                        },
                    ),
                ],
                logtekst=(
                    f"'{campagne.naam}' wijkt {afwijking:.0f}% af van de verwachting"
                ),
            ),
        )
        return uitkomst.beslissing_id

    # -- reageren op een wervingstekort ------------------------------------

    async def reageer_op_wervingstekort(
        self, sessie: AsyncSession, event: WervingstekortGemeld, bron: AgentEvent | None = None
    ) -> None:
        """Matching meldt open plekken; Marketing plant er extra content op.

        Hiermee is de pijl Matching → Marketing uit het architectuurdiagram voor
        het eerst functioneel: het tekort leidt tot echte actie in plaats van
        alleen een logregel.
        """
        hoeken = await self._goedgekeurde_hoeken(sessie)
        if not hoeken:
            await self.rapporteer(
                sessie,
                (
                    f"Wervingstekort gemeld ({event.open_plekken}x {event.functie}) maar "
                    "er is geen goedgekeurde hoek om content op te plannen"
                ),
            )
            return

        # Een openstaande shift levert bij elke matching-run opnieuw een event op.
        # Zonder deze controle plant de agent er telkens weer content voor, en
        # loopt de kalender vol met dezelfde post zodra de scheduler draait.
        if await self._al_content_voor_tekort(sessie, event.functie, event.datum):
            await self.rapporteer(
                sessie,
                (
                    f"Wervingstekort voor {event.functie} op {event.datum} stond al "
                    "op de kalender — geen extra post gepland"
                ),
            )
            return

        # Plan de post ruim vóór de shift, anders komt de werving te laat.
        shiftdatum = date.fromisoformat(event.datum)
        geplande_datum = max(nu().date(), shiftdatum - timedelta(days=3))

        await self.plan_content(
            sessie,
            hoek_id=hoeken[0].id,
            geplande_datum=geplande_datum,
            aanleiding=(
                f"{event.open_plekken} open plek(ken) voor {event.functie} "
                f"op {event.datum}"
            ),
        )

        if event.open_plekken >= BUDGET_BIJSTUREN_VANAF_PLEKKEN:
            await self._stuur_budget_bij(sessie, event)

    async def _stuur_budget_bij(
        self, sessie: AsyncSession, event: WervingstekortGemeld
    ) -> None:
        """Verschuif budget naar de best presterende campagne, binnen de bandbreedte."""
        campagnes = await self._actieve_campagnes(sessie)
        if len(campagnes) < 2:
            return

        gerangschikt = await self._rangschik_op_prestatie(sessie, campagnes)
        if len(gerangschikt) < 2:
            return

        beste = gerangschikt[0]
        slechtste = gerangschikt[-1]
        if beste.id == slechtste.id:
            return

        bedrag = self.maximale_verschuiving_cent(slechtste)
        if bedrag <= 0:
            return

        try:
            await self.verschuif_budget(
                sessie,
                van_campagne_id=slechtste.id,
                naar_campagne_id=beste.id,
                bedrag_cent=bedrag,
                reden=(
                    f"tekort van {event.open_plekken}x {event.functie}; "
                    f"'{beste.naam}' levert nu de goedkoopste aanmeldingen"
                ),
            )
        except BandbreedteOverschredenError:
            # Kan hier niet gebeuren (we vragen exact het maximum), maar als de
            # bandbreedte ooit verandert, escaleren we in plaats van te forceren.
            await self.vraag_budgetverhoging(
                sessie,
                campagne_id=beste.id,
                extra_cent=bedrag,
                reden=f"Wervingstekort van {event.open_plekken}x {event.functie}.",
            )

    # -- hulpfuncties ------------------------------------------------------

    async def _goedgekeurde_hoeken(self, sessie: AsyncSession) -> list[Hoek]:
        resultaat = await sessie.execute(
            select(Hoek).where(Hoek.goedgekeurd.is_(True)).order_by(Hoek.id)
        )
        return list(resultaat.scalars().all())

    async def _actieve_campagnes(self, sessie: AsyncSession) -> list[Campagne]:
        resultaat = await sessie.execute(
            select(Campagne)
            .where(Campagne.status == str(CampagneStatus.ACTIEF))
            .order_by(Campagne.id)
        )
        return list(resultaat.scalars().all())

    async def _dagcijfers(
        self, sessie: AsyncSession, campagne_id: int, datum: date
    ) -> tuple[int, int]:
        """Totale uitgaven en aanmeldingen van één campagnedag.

        Telt alle rijen voor die dag op in plaats van er één te pakken. Cijfers
        kunnen in delen binnenkomen (of per ongeluk dubbel worden ingevoerd);
        dan hoort de dagconclusie op het totaal te zijn gebaseerd, niet op de
        eerste rij die de database toevallig teruggeeft.
        """
        resultaat = await sessie.execute(
            select(CampagneResultaat).where(
                CampagneResultaat.campagne_id == campagne_id,
                CampagneResultaat.datum == datum,
            )
        )
        rijen = list(resultaat.scalars().all())
        return (
            sum(r.uitgaven_cent for r in rijen),
            sum(r.aanmeldingen for r in rijen),
        )

    async def _rangschik_op_prestatie(
        self, sessie: AsyncSession, campagnes: list[Campagne]
    ) -> list[Campagne]:
        """Sorteer op kosten per aanmelding over de laatste zeven dagen, best eerst."""
        vanaf = nu().date() - timedelta(days=7)
        scores: list[tuple[float, Campagne]] = []

        for campagne in campagnes:
            resultaat = await sessie.execute(
                select(CampagneResultaat).where(
                    CampagneResultaat.campagne_id == campagne.id,
                    CampagneResultaat.datum >= vanaf,
                )
            )
            rijen = list(resultaat.scalars().all())
            uitgaven = sum(r.uitgaven_cent for r in rijen)
            aanmeldingen = sum(r.aanmeldingen for r in rijen)
            if not aanmeldingen:
                # Geen aanmeldingen: achteraan in de rangschikking.
                scores.append((float("inf"), campagne))
            else:
                scores.append((uitgaven / aanmeldingen, campagne))

        scores.sort(key=lambda paar: (paar[0], paar[1].id))
        return [campagne for _, campagne in scores]

    async def _al_content_voor_tekort(
        self, sessie: AsyncSession, functie: str, shiftdatum: str
    ) -> bool:
        """Staat er al een post op de kalender voor dit tekort?

        Herkent het tekort aan functie én shiftdatum, niet aan het aantal open
        plekken: dat verandert zodra er iemand gematcht wordt, terwijl het om
        hetzelfde tekort gaat.
        """
        resultaat = await sessie.execute(
            select(Contentitem).where(
                Contentitem.status == str(ContentStatus.GEPLAND),
                Contentitem.aanleiding.like(f"%voor {functie} op {shiftdatum}%"),
            )
        )
        return resultaat.scalars().first() is not None

    async def _al_gepland(self, sessie: AsyncSession, datum: date) -> bool:
        resultaat = await sessie.execute(
            select(Contentitem).where(Contentitem.geplande_datum == datum)
        )
        return resultaat.scalars().first() is not None


def _bevat_bedrag(tekst: str) -> bool:
    """Bevat de tekst een bedrag of tariefbelofte?

    Dezelfde gedachte als bij de Support-sjablonen: een post die een bedrag
    noemt, is een toezegging. Wat iemand verdient verschilt per shift, dus dat
    hoort niet in een advertentie die WOSZ zelf plaatst.
    """
    import re

    patronen = (r"€", r"\beuro\b", r"\bper uur\b", r"\buurloon\b", r"\btarief\b", r"\d+\s*p/u")
    return any(re.search(p, tekst, flags=re.IGNORECASE) for p in patronen)


# ---------------------------------------------------------------------------
# Event-handler — vervangt de tijdelijke ontvanger uit Fase 1
# ---------------------------------------------------------------------------


@handelt(WervingstekortGemeld)
async def _op_wervingstekort(
    sessie: AsyncSession, event: WervingstekortGemeld, bron: AgentEvent
) -> None:
    await MarketingAgent().reageer_op_wervingstekort(sessie, event, bron)


# ---------------------------------------------------------------------------
# Uitvoerders
# ---------------------------------------------------------------------------


@registreer_uitvoerder("marketing.plan_contentitem")
async def _plan_contentitem(
    sessie: AsyncSession, params: dict[str, Any], _beslissing: Beslissing | None
) -> str:
    item = Contentitem(
        geplande_datum=date.fromisoformat(params["geplande_datum"]),
        kanaal=params["kanaal"],
        hoek_id=params["hoek_id"],
        campagne_id=params.get("campagne_id"),
        haak=params["haak"],
        concepttekst=params["concepttekst"],
        aanleiding=params.get("aanleiding", ""),
        status=str(ContentStatus.GEPLAND),
        door_llm=bool(params.get("door_llm", False)),
    )
    sessie.add(item)
    await sessie.flush()

    aanleiding = params.get("aanleiding")
    staart = f" ({aanleiding})" if aanleiding else ""
    return (
        f"Post ingepland voor {params['geplande_datum']} op {params['kanaal']} — "
        f"hoek '{params['hoek_naam']}'{staart}: “{params['haak']}”"
    )


@registreer_uitvoerder("marketing.verschuif_budget")
async def _verschuif_budget(
    sessie: AsyncSession, params: dict[str, Any], _beslissing: Beslissing | None
) -> str:
    van = await sessie.get(Campagne, params["van_campagne_id"])
    naar = await sessie.get(Campagne, params["naar_campagne_id"])
    if van is None or naar is None:
        raise LookupError("Onbekende campagne bij budgetverschuiving")

    bedrag = int(params["bedrag_cent"])
    # Overboeking: het totaal blijft per constructie gelijk.
    van.dagbudget_cent -= bedrag
    naar.dagbudget_cent += bedrag

    mutatie = Budgetmutatie(
        van_campagne_id=van.id,
        naar_campagne_id=naar.id,
        bedrag_cent=bedrag,
        reden=params.get("reden", ""),
        soort="verschuiving",
        status=str(BudgetmutatieStatus.KLAAR_VOOR_UITVOERING),
    )
    sessie.add(mutatie)
    await sessie.flush()

    return (
        f"€{bedrag / 100:.2f} verschoven van '{van.naam}' naar '{naar.naam}' — "
        f"{params.get('reden', '')}. Voer dit door in Ads Manager."
    )


@registreer_uitvoerder("marketing.keur_budgetverhoging_goed")
async def _keur_budgetverhoging_goed(
    sessie: AsyncSession, params: dict[str, Any], beslissing: Beslissing | None
) -> str:
    campagne = await sessie.get(Campagne, params["campagne_id"])
    if campagne is None:
        raise LookupError(f"Campagne {params['campagne_id']} bestaat niet")

    extra = int(params["extra_cent"])
    campagne.dagbudget_cent += extra

    mutatie = Budgetmutatie(
        naar_campagne_id=campagne.id,
        bedrag_cent=extra,
        reden=params.get("reden", ""),
        soort="verhoging",
        status=str(BudgetmutatieStatus.KLAAR_VOOR_UITVOERING),
        beslissing_id=beslissing.id if beslissing else None,
    )
    sessie.add(mutatie)
    await sessie.flush()

    return (
        f"Budget van '{campagne.naam}' verhoogd met €{extra / 100:.2f}/dag naar "
        f"€{campagne.dagbudget_cent / 100:.2f} — voer dit door in Ads Manager"
    )


@registreer_uitvoerder("marketing.voeg_hoek_toe")
async def _voeg_hoek_toe(
    sessie: AsyncSession, params: dict[str, Any], _beslissing: Beslissing | None
) -> str:
    hoek = Hoek(
        naam=params["naam"],
        omschrijving=params.get("omschrijving", ""),
        goedgekeurd=True,
    )
    sessie.add(hoek)
    await sessie.flush()
    return f"Hoek '{hoek.naam}' toegevoegd aan de huisstijl"


@registreer_uitvoerder("marketing.pauzeer_campagne")
async def _pauzeer_campagne(
    sessie: AsyncSession, params: dict[str, Any], _beslissing: Beslissing | None
) -> str:
    campagne = await sessie.get(Campagne, params["campagne_id"])
    if campagne is None:
        raise LookupError(f"Campagne {params['campagne_id']} bestaat niet")
    campagne.status = str(CampagneStatus.GEPAUZEERD)
    return f"'{campagne.naam}' op pauze gezet — pauzeer hem ook in Ads Manager"


@registreer_uitvoerder("marketing.noteer")
async def _noteer(
    _sessie: AsyncSession, params: dict[str, Any], _beslissing: Beslissing | None
) -> str:
    return str(params.get("tekst", ""))


async def markeer_mutatie_doorgevoerd(
    sessie: AsyncSession, mutatie_id: int
) -> Budgetmutatie:
    """Leg vast dat Sebas de budgetwijziging in Ads Manager heeft doorgevoerd."""
    mutatie = await sessie.get(Budgetmutatie, mutatie_id)
    if mutatie is None:
        raise LookupError(f"Budgetmutatie {mutatie_id} bestaat niet")
    mutatie.status = str(BudgetmutatieStatus.DOORGEVOERD)
    mutatie.doorgevoerd_op = nu()
    return mutatie
