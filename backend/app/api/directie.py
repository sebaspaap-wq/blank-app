"""Endpoints voor het directiedashboard.

Deze routes vervangen de gesimuleerde arrays in wosz-app.html:

``activityLog``   -> GET  /api/directie/activiteiten
``decisions``     -> GET  /api/directie/beslissingen
``resolveDecision`` -> POST /api/directie/beslissingen/{id}/kies
``dailyReport``   -> GET  /api/directie/dagrapport
de vier tellers   -> GET  /api/directie/dashboard
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.directie import DirectieAgent
from app.api.schemas import (
    ActiviteitUit,
    BeslissingUit,
    BeslissingenUit,
    DagrapportUit,
    DashboardUit,
    KeuzeIn,
    UitbetalingUit,
)
from app.core import tiers
from app.core.activity import activiteiten_van_afdeling, recente_activiteiten
from app.core.domein import Afdeling
from app.db.session import get_sessie
from app.payouts import (
    exporteer_openstaande_opdrachten,
    markeer_handmatig_voldaan,
    openstaande_opdrachten,
)

router = APIRouter(prefix="/api/directie", tags=["directie"])


@router.get("/activiteiten", response_model=list[ActiviteitUit])
async def lees_activiteiten(
    limiet: int = 40, sessie: AsyncSession = Depends(get_sessie)
) -> list[ActiviteitUit]:
    """De laatste activiteiten, nieuwste eerst.

    Standaard 40 — hetzelfde aantal als ``activityLog.slice(0, 40)`` toont.
    """
    limiet = max(1, min(limiet, 200))
    activiteiten = await recente_activiteiten(sessie, limiet)
    return [ActiviteitUit.van_model(a) for a in activiteiten]


@router.get("/activiteiten/{afdeling}", response_model=list[ActiviteitUit])
async def lees_activiteiten_van_afdeling(
    afdeling: Afdeling, limiet: int = 8, sessie: AsyncSession = Depends(get_sessie)
) -> list[ActiviteitUit]:
    """Feed van één afdeling — voedt de 'Live activiteit'-kaarten."""
    limiet = max(1, min(limiet, 100))
    activiteiten = await activiteiten_van_afdeling(sessie, afdeling, limiet)
    return [ActiviteitUit.van_model(a) for a in activiteiten]


@router.get("/beslissingen", response_model=BeslissingenUit)
async def lees_beslissingen(sessie: AsyncSession = Depends(get_sessie)) -> BeslissingenUit:
    openstaand, afgehandeld = await DirectieAgent().beslissingen(sessie)
    return BeslissingenUit(
        open=[BeslissingUit.van_model(b) for b in openstaand],
        afgehandeld=[BeslissingUit.van_model(b) for b in afgehandeld],
    )


@router.post("/beslissingen/{beslissing_id}/kies", response_model=BeslissingUit)
async def kies_optie(
    beslissing_id: int, keuze: KeuzeIn, sessie: AsyncSession = Depends(get_sessie)
) -> BeslissingUit:
    """Verwerk de expliciete keuze van Sebas.

    Dit is het enige pad waarlangs een tier 3-beslissing uitgevoerd kan worden —
    en dus ook het enige pad waarlangs een uitbetaling klaargezet wordt.
    """
    try:
        beslissing = await tiers.verwerk_keuze(sessie, beslissing_id, keuze.optie_index)
    # IndexError is een subklasse van LookupError en moet dus eerst worden
    # afgevangen: een niet-bestaande optie is geen ontbrekende beslissing.
    except IndexError as fout:
        raise HTTPException(status_code=422, detail=str(fout)) from fout
    except LookupError as fout:
        raise HTTPException(status_code=404, detail=str(fout)) from fout
    except ValueError as fout:
        raise HTTPException(status_code=409, detail=str(fout)) from fout

    await sessie.commit()
    return BeslissingUit.van_model(beslissing)


@router.get("/dagrapport", response_model=DagrapportUit)
async def lees_dagrapport(sessie: AsyncSession = Depends(get_sessie)) -> DagrapportUit:
    rapport = await DirectieAgent().dagrapport(sessie)
    return DagrapportUit.van_dict(rapport)


@router.get("/dashboard", response_model=DashboardUit)
async def lees_dashboard(sessie: AsyncSession = Depends(get_sessie)) -> DashboardUit:
    cijfers = await DirectieAgent().dashboardcijfers(sessie)
    return DashboardUit(
        acties_vandaag=cijfers["actiesVandaag"],
        nieuwe_matches=cijfers["nieuweMatches"],
        aanmeldingen_vandaag=cijfers["aanmeldingenVandaag"],
        open_beslissingen=cijfers["openBeslissingen"],
    )


@router.get("/planning")
async def lees_planning() -> list[dict[str, str]]:
    """Welke rondes er vanzelf draaien, en hoe vaak.

    Geen database-aanroep: dit is de dienstregeling uit ``app/scheduler.py``.
    Hij staat in het dashboard zodat zichtbaar is wat er buiten beeld gebeurt —
    automatisering die je niet kunt zien, kun je ook niet vertrouwen.
    """
    from app.scheduler import volgende_rondes

    return volgende_rondes()


# ---------------------------------------------------------------------------
# Uitbetalingen — administratie, geen betalingen
# ---------------------------------------------------------------------------


@router.get("/uitbetalingen", response_model=list[UitbetalingUit])
async def lees_uitbetalingen(
    sessie: AsyncSession = Depends(get_sessie),
) -> list[UitbetalingUit]:
    """Goedgekeurde uitbetalingen die Sebas nog zelf moet overmaken."""
    opdrachten = await openstaande_opdrachten(sessie)
    return [
        UitbetalingUit(
            id=o.id,
            soort=o.soort,
            begunstigde=o.begunstigde_naam,
            bedrag_eur=o.bedrag_cent / 100,
            omschrijving=o.omschrijving,
            status=o.status,
        )
        for o in opdrachten
    ]


@router.post("/uitbetalingen/export")
async def exporteer_uitbetalingen(sessie: AsyncSession = Depends(get_sessie)) -> Response:
    """Download de werklijst voor de bank.

    Dit bestand is geen betaalopdracht: Sebas voert de overboekingen zelf uit.
    """
    inhoud, aantal = await exporteer_openstaande_opdrachten(sessie)
    await sessie.commit()
    return Response(
        content=inhoud,
        media_type="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="uitbetalingen.csv"',
            "X-Aantal-Opdrachten": str(aantal),
        },
    )


@router.post("/uitbetalingen/{opdracht_id}/voldaan", response_model=UitbetalingUit)
async def markeer_voldaan(
    opdracht_id: int, sessie: AsyncSession = Depends(get_sessie)
) -> UitbetalingUit:
    """Leg vast dat Sebas de betaling heeft gedaan."""
    try:
        opdracht = await markeer_handmatig_voldaan(sessie, opdracht_id)
    except LookupError as fout:
        raise HTTPException(status_code=404, detail=str(fout)) from fout
    await sessie.commit()
    return UitbetalingUit(
        id=opdracht.id,
        soort=opdracht.soort,
        begunstigde=opdracht.begunstigde_naam,
        bedrag_eur=opdracht.bedrag_cent / 100,
        omschrijving=opdracht.omschrijving,
        status=opdracht.status,
    )
