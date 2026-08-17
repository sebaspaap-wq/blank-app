"""Financieel-agent (paragraaf 3.4 van de bouwopdracht).

Verantwoordelijk voor: uren berekenen, facturen opstellen, en bonussen
(vrienden + levels) berekenen en klaarzetten.

Escalatie:
  tier 1  uren verwerken en factuurconcepten opstellen
  tier 3  élke uitbetaling, zonder uitzondering

Deze agent kan geen geld verplaatsen, en dat is geen kwestie van
terughoudendheid: hij kan de uitbetalingsmodule niet eens importeren. Wat hij
doet is een bedrag berekenen en een conceptrecord aanmaken met status
``concept``. Pas als Sebas in het dashboard op "Goedkeuren" klikt, draait de
uitvoerder ``directie.keur_uitbetaling_goed`` — en die is geregistreerd vanuit
``app.payouts``, buiten het bereik van deze agent. Zie app/payouts/README.md.

Let op de richting van de afhankelijkheid: deze agent verwijst naar die
uitvoerder alleen bij naam, als string in de beslissing. Hij importeert hem
niet. ``tests/test_betaalscheiding.py`` bewaakt dat.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base import BaseAgent
from app.core.domein import (
    Afdeling,
    Tier,
    UitbetalingStatus,
    Urgentie,
    nu,
)
from app.core.events import LevelBereikt, UrenGewerkt, handelt
from app.core.tiers import Optie, Voorstel, registreer_uitvoerder
from app.db.models import (
    AgentEvent,
    Bedrijf,
    Beslissing,
    Factuur,
    Referral,
    Uitbetalingsopdracht,
    User,
)

#: Uren die een aangebrachte vriend moet maken voordat de vriendenbonus geldt.
VRIENDENBONUS_DREMPEL_UREN = 50.0

#: Naam van de uitvoerder die een uitbetaling klaarzet. Bewust een string:
#: deze agent importeert de uitbetalingsmodule niet.
UITVOERDER_GOEDKEUREN = "directie.keur_uitbetaling_goed"
UITVOERDER_AFWIJZEN = "directie.wijs_uitbetaling_af"


class FinancieelAgent(BaseAgent):
    afdeling = Afdeling.FINANCIEEL
    systeemprompt = (
        "Je bent de Financieel-agent van WOSZ. Je berekent gewerkte uren, stelt "
        "factuurconcepten op en zet bonussen klaar ter goedkeuring. Je keurt zelf "
        "nooit een uitbetaling goed en je verplaatst geen geld — dat doet Sebas."
    )

    # -- uren en facturen (tier 1) ----------------------------------------

    async def verwerk_uren(
        self, sessie: AsyncSession, event: UrenGewerkt, bron: AgentEvent | None = None
    ) -> dict[str, Any]:
        """Boek gewerkte uren op het factuurconcept van het bedrijf."""
        bedrijf = await sessie.get(Bedrijf, event.bedrijf_id)
        if bedrijf is None:
            raise LookupError(f"Bedrijf {event.bedrijf_id} bestaat niet")

        periode = event.datum[:7]  # "2026-08"
        factuur = await self._factuur(sessie, bedrijf, periode)

        await self.voer_uit(
            sessie,
            Voorstel(
                afdeling=self.afdeling,
                tier=Tier.ZELFSTANDIG,
                logtekst=(
                    f"{event.uren:.0f} uur bijgeboekt op het factuurconcept van "
                    f"{bedrijf.naam} ({periode})"
                ),
                actie={
                    "uitvoerder": "financieel.boek_uren",
                    "params": {
                        "factuur_id": factuur.id,
                        "uren": event.uren,
                        "bedrijf_naam": bedrijf.naam,
                        "periode": periode,
                    },
                },
            ),
        )

        # Telt deze medewerker als aangebrachte vriend? Dan de teller bijwerken.
        await self._werk_referral_bij(sessie, event.medewerker_id, event.uren)

        return {
            "factuur_id": factuur.id,
            "bedrijf": bedrijf.naam,
            "periode": periode,
            "uren": factuur.uren,
            "bedrag_eur": factuur.bedrag_cent / 100,
        }

    async def _factuur(
        self, sessie: AsyncSession, bedrijf: Bedrijf, periode: str
    ) -> Factuur:
        resultaat = await sessie.execute(
            select(Factuur).where(
                Factuur.bedrijf_id == bedrijf.id,
                Factuur.periode == periode,
                Factuur.status == "concept",
            )
        )
        factuur = resultaat.scalars().first()
        if factuur is None:
            factuur = Factuur(
                bedrijf_id=bedrijf.id, periode=periode, uren=0.0, bedrag_cent=0
            )
            sessie.add(factuur)
            await sessie.flush()
        return factuur

    # -- bonussen (tier 3) -------------------------------------------------

    async def zet_levelbonus_klaar(
        self, sessie: AsyncSession, event: LevelBereikt, bron: AgentEvent | None = None
    ) -> int | None:
        """Bereken de levelbonus en leg hem voor aan Sebas.

        Tier 3. Er wordt niets uitbetaald en niets toegezegd: er ontstaat een
        conceptrecord plus een beslissing in het dashboard.
        """
        if event.bonus_bedrag_cent <= 0:
            return None

        opdracht = Uitbetalingsopdracht(
            soort="levelbonus",
            begunstigde_naam=event.medewerker_naam,
            begunstigde_user_id=event.medewerker_id,
            bedrag_cent=event.bonus_bedrag_cent,
            omschrijving=(
                f"Levelbonus {event.level_naam} (level {event.nieuw_level}) — "
                f"{event.seizoen_uren:.0f} uur dit seizoen"
            ),
            status=str(UitbetalingStatus.CONCEPT),
        )
        sessie.add(opdracht)
        await sessie.flush()

        bedrag = event.bonus_bedrag_cent / 100
        return await self._leg_uitbetaling_voor(
            sessie,
            opdracht=opdracht,
            titel=f"Levelbonus uitbetalen aan {event.medewerker_naam}",
            situatie=(
                f"{event.medewerker_naam} heeft level {event.nieuw_level} "
                f"({event.level_naam}) bereikt met {event.seizoen_uren:.0f} uur dit "
                f"seizoen. Daar hoort een bonus van €{bedrag:.2f} bij. Het bedrag "
                "staat klaar maar is niet uitbetaald — dat doe jij zelf."
            ),
            aanbeveling=(
                "AI-advies: goedkeuren — de uren zijn opgebouwd uit geregistreerde "
                "shifts."
            ),
            logtekst=(
                f"Levelbonus van €{bedrag:.2f} voor {event.medewerker_naam} "
                "klaargezet ter goedkeuring"
            ),
        )

    async def _werk_referral_bij(
        self, sessie: AsyncSession, vriend_id: int, uren: float
    ) -> None:
        """Tel uren mee voor de vriendenbonus en leg hem voor bij de drempel."""
        resultaat = await sessie.execute(
            select(Referral).where(
                Referral.vriend_id == vriend_id, Referral.bonus_status == "bezig"
            )
        )
        referral = resultaat.scalars().first()
        if referral is None:
            return

        referral.uren_vriend += uren
        if referral.uren_vriend < VRIENDENBONUS_DREMPEL_UREN:
            return

        aanbrenger = await sessie.get(User, referral.medewerker_id)
        vriend = await sessie.get(User, referral.vriend_id)
        if aanbrenger is None or vriend is None:
            return

        referral.bonus_status = "ter-goedkeuring"
        opdracht = Uitbetalingsopdracht(
            soort="vriendenbonus",
            begunstigde_naam=aanbrenger.naam,
            begunstigde_user_id=aanbrenger.id,
            bedrag_cent=referral.bonus_bedrag_cent,
            omschrijving=(
                f"Vriendenbonus voor het aanbrengen van {vriend.naam} "
                f"({referral.uren_vriend:.0f} uur gewerkt)"
            ),
            status=str(UitbetalingStatus.CONCEPT),
        )
        sessie.add(opdracht)
        await sessie.flush()

        bedrag = referral.bonus_bedrag_cent / 100
        await self._leg_uitbetaling_voor(
            sessie,
            opdracht=opdracht,
            titel=f"Vriendenbonus uitbetalen aan {aanbrenger.naam}",
            situatie=(
                f"{vriend.naam}, aangemeld door {aanbrenger.naam}, heeft de "
                f"{VRIENDENBONUS_DREMPEL_UREN:.0f}-uursgrens gehaald "
                f"({referral.uren_vriend:.0f} uur). De bonus van €{bedrag:.2f} staat "
                "klaar maar is niet uitbetaald."
            ),
            aanbeveling=(
                "AI-advies: goedkeuren — de uren komen overeen met de "
                "shift-registraties."
            ),
            logtekst=(
                f"Vriendenbonus van €{bedrag:.2f} voor {aanbrenger.naam} klaargezet "
                "ter goedkeuring"
            ),
        )

    async def _leg_uitbetaling_voor(
        self,
        sessie: AsyncSession,
        *,
        opdracht: Uitbetalingsopdracht,
        titel: str,
        situatie: str,
        aanbeveling: str,
        logtekst: str,
    ) -> int | None:
        """Maak de tier 3-beslissing voor een uitbetaling.

        Altijd tier 3 — paragraaf 3.4 kent hier geen uitzondering, en deze
        methode is het enige pad waarlangs deze agent een uitbetaling voorlegt.
        """
        uitkomst = await self.voer_uit(
            sessie,
            Voorstel(
                afdeling=self.afdeling,
                tier=Tier.WACHT,
                urgentie=Urgentie.DRINGEND,
                titel=titel,
                situatie=situatie,
                aanbeveling=aanbeveling,
                opties=[
                    Optie(
                        naam="Goedkeuren",
                        gevolg=(
                            "Het bedrag komt op je uitbetaallijst; je maakt het zelf over"
                        ),
                        actie={
                            "uitvoerder": UITVOERDER_GOEDKEUREN,
                            "params": {"uitbetaling_id": opdracht.id},
                        },
                    ),
                    Optie(
                        naam="Nu niet uitbetalen",
                        gevolg="Het concept vervalt; je kunt het later opnieuw laten opvoeren",
                        actie={
                            "uitvoerder": UITVOERDER_AFWIJZEN,
                            "params": {"uitbetaling_id": opdracht.id},
                        },
                    ),
                ],
                logtekst=logtekst,
            ),
        )
        return uitkomst.beslissing_id

    # -- periode afsluiten -------------------------------------------------

    async def sluit_periode_af(
        self, sessie: AsyncSession, periode: str
    ) -> list[dict[str, Any]]:
        """Zet factuurconcepten van een periode op 'klaar ter goedkeuring'.

        Tier 1: een factuur naar een bedrijf sturen is geen uitbetaling. Er gaat
        geld naar WOSZ toe, niet vanaf.
        """
        resultaat = await sessie.execute(
            select(Factuur).where(Factuur.periode == periode, Factuur.status == "concept")
        )
        facturen = list(resultaat.scalars().all())
        verslag: list[dict[str, Any]] = []

        for factuur in facturen:
            bedrijf = await sessie.get(Bedrijf, factuur.bedrijf_id)
            naam = bedrijf.naam if bedrijf else f"bedrijf {factuur.bedrijf_id}"
            await self.voer_uit(
                sessie,
                Voorstel(
                    afdeling=self.afdeling,
                    tier=Tier.ZELFSTANDIG,
                    logtekst=(
                        f"Factuurconcept {periode} voor {naam} afgerond: "
                        f"{factuur.uren:.0f} uur, €{factuur.bedrag_cent / 100:.2f}"
                    ),
                    actie={
                        "uitvoerder": "financieel.rond_factuur_af",
                        "params": {"factuur_id": factuur.id, "bedrijf_naam": naam},
                    },
                ),
            )
            verslag.append(
                {
                    "factuur_id": factuur.id,
                    "bedrijf": naam,
                    "uren": factuur.uren,
                    "bedrag_eur": factuur.bedrag_cent / 100,
                }
            )
        return verslag


# ---------------------------------------------------------------------------
# Event-handlers
# ---------------------------------------------------------------------------


@handelt(UrenGewerkt)
async def _op_uren_gewerkt(
    sessie: AsyncSession, event: UrenGewerkt, bron: AgentEvent
) -> None:
    await FinancieelAgent().verwerk_uren(sessie, event, bron)


@handelt(LevelBereikt)
async def _op_level_bereikt(
    sessie: AsyncSession, event: LevelBereikt, bron: AgentEvent
) -> None:
    await FinancieelAgent().zet_levelbonus_klaar(sessie, event, bron)


# ---------------------------------------------------------------------------
# Uitvoerders
# ---------------------------------------------------------------------------


@registreer_uitvoerder("financieel.boek_uren")
async def _boek_uren(
    sessie: AsyncSession, params: dict[str, Any], _beslissing: Beslissing | None
) -> str:
    factuur = await sessie.get(Factuur, params["factuur_id"])
    if factuur is None:
        raise LookupError(f"Factuur {params['factuur_id']} bestaat niet")

    bedrijf = await sessie.get(Bedrijf, factuur.bedrijf_id)
    tarief = bedrijf.tarief_per_uur if bedrijf else 2.0

    factuur.uren += float(params["uren"])
    factuur.bedrag_cent = round(factuur.uren * tarief * 100)

    return (
        f"{float(params['uren']):.0f} uur bijgeboekt op het factuurconcept van "
        f"{params['bedrijf_naam']} ({params['periode']}) — nu {factuur.uren:.0f} uur, "
        f"€{factuur.bedrag_cent / 100:.2f}"
    )


@registreer_uitvoerder("financieel.rond_factuur_af")
async def _rond_factuur_af(
    sessie: AsyncSession, params: dict[str, Any], _beslissing: Beslissing | None
) -> str:
    factuur = await sessie.get(Factuur, params["factuur_id"])
    if factuur is None:
        raise LookupError(f"Factuur {params['factuur_id']} bestaat niet")
    factuur.status = "klaar-ter-goedkeuring"
    return (
        f"Factuurconcept {factuur.periode} voor {params['bedrijf_naam']} afgerond: "
        f"{factuur.uren:.0f} uur, €{factuur.bedrag_cent / 100:.2f}"
    )
