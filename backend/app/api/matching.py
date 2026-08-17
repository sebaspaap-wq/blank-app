"""Endpoints van de Matching-agent.

Deze routes zijn de handmatige tegenhanger van de scheduler: ze laten je de
agent gericht aansturen vanuit het dashboard of tijdens het testen.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.matching import MatchingAgent
from app.api.schemas import UrengeschilIn, UrenIn
from app.core.events import verwerk_pending
from app.config import get_settings
from app.db.session import get_sessie

router = APIRouter(prefix="/api/matching", tags=["matching"])


async def _verwerk_events(sessie: AsyncSession) -> None:
    """Handel de events af die de actie zojuist heeft opgeleverd.

    In productie doet de achtergrondworker dit; hier draaien we hem meteen even
    mee zodat een API-aanroep een compleet resultaat teruggeeft (bijvoorbeeld
    de support-waarschuwing na een no-show).
    """
    await verwerk_pending(sessie, get_settings().event_max_pogingen)


@router.post("/run")
async def draai_matching(sessie: AsyncSession = Depends(get_sessie)) -> dict[str, Any]:
    """Match alle openstaande shifts."""
    verslag = await MatchingAgent().match_open_shifts(sessie)
    await _verwerk_events(sessie)
    await sessie.commit()
    return {"shifts": verslag}


@router.post("/matches/{match_id}/uren")
async def registreer_uren(
    match_id: int, invoer: UrenIn, sessie: AsyncSession = Depends(get_sessie)
) -> dict[str, Any]:
    """Boek gewerkte uren en werk het levelsysteem bij."""
    try:
        resultaat = await MatchingAgent().registreer_gewerkte_uren(
            sessie, match_id, invoer.uren
        )
    except LookupError as fout:
        raise HTTPException(status_code=404, detail=str(fout)) from fout
    await _verwerk_events(sessie)
    await sessie.commit()
    return resultaat


@router.post("/matches/{match_id}/no-show")
async def meld_no_show(
    match_id: int, sessie: AsyncSession = Depends(get_sessie)
) -> dict[str, Any]:
    """Signaleer een no-show.

    Levert twee logregels op: één van Matching en één van Support, die de
    waarschuwing verstuurt na het oppikken van het event.
    """
    try:
        resultaat = await MatchingAgent().signaleer_no_show(sessie, match_id)
    except LookupError as fout:
        raise HTTPException(status_code=404, detail=str(fout)) from fout
    await _verwerk_events(sessie)
    await sessie.commit()
    return resultaat


@router.post("/matches/{match_id}/urengeschil")
async def meld_urengeschil(
    match_id: int, invoer: UrengeschilIn, sessie: AsyncSession = Depends(get_sessie)
) -> dict[str, Any]:
    """Leg een urengeschil voor aan Sebas (tier 3 — er gebeurt niets tot hij kiest)."""
    try:
        beslissing_id = await MatchingAgent().meld_urengeschil(
            sessie,
            match_id,
            uren_medewerker=invoer.uren_medewerker,
            uren_bedrijf=invoer.uren_bedrijf,
        )
    except LookupError as fout:
        raise HTTPException(status_code=404, detail=str(fout)) from fout
    await sessie.commit()
    return {"beslissing_id": beslissing_id, "status": "wacht op keuze van Sebas"}
