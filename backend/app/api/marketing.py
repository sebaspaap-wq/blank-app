"""Endpoints van de Marketing-agent.

Let op wat hier ontbreekt: er is geen endpoint dat publiceert of dat een budget
in Meta Ads Manager wijzigt. De kalender en de budgetmutaties zijn werklijsten;
Sebas voert ze zelf uit.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.marketing import (
    BandbreedteOverschredenError,
    MarketingAgent,
    markeer_mutatie_doorgevoerd,
)
from app.api.schemas import (
    BudgetmutatieUit,
    BudgetverhogingIn,
    BudgetverschuivingIn,
    CampagneUit,
    ContentitemUit,
    ContentplanningIn,
    NieuweHoekIn,
    ResultaatIn,
)
from app.core.domein import BudgetmutatieStatus, ContentStatus, nu
from app.db.models import Budgetmutatie, Campagne, CampagneResultaat, Contentitem, Hoek
from app.db.session import get_sessie

router = APIRouter(prefix="/api/marketing", tags=["marketing"])


# ---------------------------------------------------------------------------
# Content-kalender
# ---------------------------------------------------------------------------


@router.get("/kalender", response_model=list[ContentitemUit])
async def lees_kalender(
    vanaf: date | None = None,
    tot: date | None = None,
    sessie: AsyncSession = Depends(get_sessie),
) -> list[ContentitemUit]:
    """De content-kalender, standaard vanaf vandaag."""
    query = select(Contentitem).order_by(Contentitem.geplande_datum, Contentitem.id)
    query = query.where(Contentitem.geplande_datum >= (vanaf or nu().date()))
    if tot:
        query = query.where(Contentitem.geplande_datum <= tot)

    resultaat = await sessie.execute(query)
    items: list[ContentitemUit] = []
    for item in resultaat.scalars().all():
        hoek = await sessie.get(Hoek, item.hoek_id)
        items.append(ContentitemUit.van_model(item, hoek.naam if hoek else ""))
    return items


@router.post("/kalender", response_model=dict)
async def plan_content(
    invoer: ContentplanningIn, sessie: AsyncSession = Depends(get_sessie)
) -> dict[str, Any]:
    """Plan één item in (tier 1, alleen op een goedgekeurde hoek)."""
    try:
        resultaat = await MarketingAgent().plan_content(
            sessie,
            hoek_id=invoer.hoek_id,
            geplande_datum=invoer.geplande_datum,
            kanaal=invoer.kanaal,
            aanleiding=invoer.aanleiding,
        )
    except LookupError as fout:
        raise HTTPException(status_code=404, detail=str(fout)) from fout
    except PermissionError as fout:
        raise HTTPException(status_code=409, detail=str(fout)) from fout
    await sessie.commit()
    return resultaat


@router.post("/kalender/weekplanning")
async def plan_week(
    aantal: int = 3, sessie: AsyncSession = Depends(get_sessie)
) -> dict[str, Any]:
    """Vul de komende week met content op de bestaande hoeken (tier 1)."""
    verslag = await MarketingAgent().plan_week(sessie, aantal=max(1, min(aantal, 14)))
    await sessie.commit()
    return {"gepland": verslag}


@router.post("/kalender/{item_id}/gepubliceerd", response_model=ContentitemUit)
async def markeer_gepubliceerd(
    item_id: int, sessie: AsyncSession = Depends(get_sessie)
) -> ContentitemUit:
    """Leg vast dat Sebas de post daadwerkelijk heeft geplaatst.

    Het systeem publiceert niet zelf; er is geen social-koppeling.
    """
    item = await sessie.get(Contentitem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail=f"Contentitem {item_id} bestaat niet")

    item.status = str(ContentStatus.GEPUBLICEERD)
    item.gepubliceerd_op = nu()
    await sessie.commit()

    hoek = await sessie.get(Hoek, item.hoek_id)
    return ContentitemUit.van_model(item, hoek.naam if hoek else "")


@router.post("/kalender/{item_id}/afwijzen", response_model=ContentitemUit)
async def wijs_item_af(
    item_id: int, sessie: AsyncSession = Depends(get_sessie)
) -> ContentitemUit:
    """Haal een gepland item van de kalender."""
    item = await sessie.get(Contentitem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail=f"Contentitem {item_id} bestaat niet")

    item.status = str(ContentStatus.AFGEWEZEN)
    await sessie.commit()

    hoek = await sessie.get(Hoek, item.hoek_id)
    return ContentitemUit.van_model(item, hoek.naam if hoek else "")


# ---------------------------------------------------------------------------
# Campagnes en budget
# ---------------------------------------------------------------------------


@router.get("/campagnes", response_model=list[CampagneUit])
async def lees_campagnes(sessie: AsyncSession = Depends(get_sessie)) -> list[CampagneUit]:
    resultaat = await sessie.execute(select(Campagne).order_by(Campagne.id))
    campagnes = list(resultaat.scalars().all())
    return [
        CampagneUit(
            id=c.id,
            naam=c.naam,
            kanaal=c.kanaal,
            status=c.status,
            dagbudget_eur=c.dagbudget_cent / 100,
            bandbreedte_pct=c.bandbreedte_pct,
            max_verschuiving_eur=MarketingAgent.maximale_verschuiving_cent(c) / 100,
            verwachte_kosten_per_aanmelding_eur=(
                c.verwachte_kosten_per_aanmelding_cent / 100
            ),
        )
        for c in campagnes
    ]


@router.post("/campagnes/budget/verschuiven")
async def verschuif_budget(
    invoer: BudgetverschuivingIn, sessie: AsyncSession = Depends(get_sessie)
) -> dict[str, Any]:
    """Verschuif budget tussen twee campagnes (tier 1 binnen de bandbreedte).

    Buiten de bandbreedte geeft dit een 409: die schuif hoort langs Sebas, en de
    agent kan hem niet zelfstandig forceren.
    """
    try:
        resultaat = await MarketingAgent().verschuif_budget(
            sessie,
            van_campagne_id=invoer.van_campagne_id,
            naar_campagne_id=invoer.naar_campagne_id,
            bedrag_cent=round(invoer.bedrag_eur * 100),
            reden=invoer.reden,
        )
    except BandbreedteOverschredenError as fout:
        raise HTTPException(status_code=409, detail=str(fout)) from fout
    except LookupError as fout:
        raise HTTPException(status_code=404, detail=str(fout)) from fout
    except ValueError as fout:
        raise HTTPException(status_code=422, detail=str(fout)) from fout
    await sessie.commit()
    return resultaat


@router.post("/campagnes/budget/verhogen")
async def vraag_budgetverhoging(
    invoer: BudgetverhogingIn, sessie: AsyncSession = Depends(get_sessie)
) -> dict[str, Any]:
    """Vraag om nieuw budget (tier 3 — altijd langs Sebas)."""
    try:
        beslissing_id = await MarketingAgent().vraag_budgetverhoging(
            sessie,
            campagne_id=invoer.campagne_id,
            extra_cent=round(invoer.extra_eur * 100),
            reden=invoer.reden,
        )
    except LookupError as fout:
        raise HTTPException(status_code=404, detail=str(fout)) from fout
    await sessie.commit()
    return {"beslissing_id": beslissing_id, "status": "wacht op keuze van Sebas"}


@router.get("/budgetmutaties", response_model=list[BudgetmutatieUit])
async def lees_budgetmutaties(
    sessie: AsyncSession = Depends(get_sessie),
) -> list[BudgetmutatieUit]:
    """De werklijst voor Ads Manager: wijzigingen die Sebas nog moet doorvoeren."""
    resultaat = await sessie.execute(
        select(Budgetmutatie)
        .where(Budgetmutatie.status == str(BudgetmutatieStatus.KLAAR_VOOR_UITVOERING))
        .order_by(Budgetmutatie.aangemaakt_op)
    )

    mutaties: list[BudgetmutatieUit] = []
    for mutatie in resultaat.scalars().all():
        van = (
            await sessie.get(Campagne, mutatie.van_campagne_id)
            if mutatie.van_campagne_id
            else None
        )
        naar = (
            await sessie.get(Campagne, mutatie.naar_campagne_id)
            if mutatie.naar_campagne_id
            else None
        )
        mutaties.append(
            BudgetmutatieUit(
                id=mutatie.id,
                soort=mutatie.soort,
                van_campagne=van.naam if van else None,
                naar_campagne=naar.naam if naar else None,
                bedrag_eur=mutatie.bedrag_cent / 100,
                reden=mutatie.reden,
                status=mutatie.status,
            )
        )
    return mutaties


@router.post("/budgetmutaties/{mutatie_id}/doorgevoerd")
async def markeer_doorgevoerd(
    mutatie_id: int, sessie: AsyncSession = Depends(get_sessie)
) -> dict[str, Any]:
    """Leg vast dat de wijziging in Ads Manager is doorgevoerd."""
    try:
        mutatie = await markeer_mutatie_doorgevoerd(sessie, mutatie_id)
    except LookupError as fout:
        raise HTTPException(status_code=404, detail=str(fout)) from fout
    await sessie.commit()
    return {"id": mutatie.id, "status": mutatie.status}


# ---------------------------------------------------------------------------
# Hoeken en resultaten
# ---------------------------------------------------------------------------


@router.post("/hoeken/voorstellen")
async def stel_hoek_voor(
    invoer: NieuweHoekIn, sessie: AsyncSession = Depends(get_sessie)
) -> dict[str, Any]:
    """Stel een nieuwe campagne-hoek voor (tier 3)."""
    beslissing_id = await MarketingAgent().stel_nieuwe_hoek_voor(
        sessie,
        naam=invoer.naam,
        omschrijving=invoer.omschrijving,
        reden=invoer.reden,
    )
    await sessie.commit()
    return {"beslissing_id": beslissing_id, "status": "wacht op keuze van Sebas"}


@router.post("/resultaten")
async def registreer_resultaat(
    invoer: ResultaatIn, sessie: AsyncSession = Depends(get_sessie)
) -> dict[str, Any]:
    """Voer de dagcijfers van een campagne in.

    Handmatig, of straks vanuit een import. Er is geen Meta Ads-koppeling die
    dit zelf ophaalt.
    """
    campagne = await sessie.get(Campagne, invoer.campagne_id)
    if campagne is None:
        raise HTTPException(
            status_code=404, detail=f"Campagne {invoer.campagne_id} bestaat niet"
        )

    resultaat = CampagneResultaat(
        campagne_id=campagne.id,
        datum=invoer.datum,
        uitgaven_cent=round(invoer.uitgaven_eur * 100),
        vertoningen=invoer.vertoningen,
        klikken=invoer.klikken,
        aanmeldingen=invoer.aanmeldingen,
    )
    sessie.add(resultaat)
    await sessie.commit()
    return {"id": resultaat.id, "campagne": campagne.naam}


@router.post("/resultaten/beoordelen")
async def beoordeel_resultaten(
    datum: date | None = None, sessie: AsyncSession = Depends(get_sessie)
) -> dict[str, Any]:
    """Vergelijk de resultaten met de verwachting.

    Binnen 25% stuurt de agent zelf bij; daarboven gaat het naar Sebas (tier 3).
    """
    bevindingen = await MarketingAgent().beoordeel_resultaten(sessie, datum=datum)
    await sessie.commit()
    return {"bevindingen": bevindingen}
