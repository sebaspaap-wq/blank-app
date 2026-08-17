"""Endpoints van de Support-agent."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.support import SupportAgent, markeer_bericht_verstuurd
from app.agents.sjablonen import alle_sjablonen
from app.api.schemas import BerichtUit, OnboardingIn, SjabloonUit, VraagIn
from app.config import get_settings
from app.core.domein import BerichtStatus
from app.core.events import verwerk_pending
from app.db.models import Bericht
from app.db.session import get_sessie

router = APIRouter(prefix="/api/support", tags=["support"])


@router.post("/vragen")
async def stel_vraag(
    invoer: VraagIn, sessie: AsyncSession = Depends(get_sessie)
) -> dict[str, Any]:
    """Laat de Support-agent een binnengekomen vraag afhandelen.

    Antwoordt zelfstandig als er een goedgekeurd kennisbankantwoord op past
    (tier 1), en escaleert anders naar Sebas (tier 3). De agent gokt nooit.
    """
    try:
        resultaat = await SupportAgent().beantwoord_vraag(
            sessie, invoer.vraag, invoer.medewerker_id
        )
    except LookupError as fout:
        raise HTTPException(status_code=404, detail=str(fout)) from fout
    await verwerk_pending(sessie, get_settings().event_max_pogingen)
    await sessie.commit()
    return resultaat


@router.post("/onboarding")
async def verstuur_onboarding(
    invoer: OnboardingIn, sessie: AsyncSession = Depends(get_sessie)
) -> dict[str, Any]:
    """Stuur het welkomstbericht naar een nieuwe medewerker (tier 1)."""
    try:
        resultaat = await SupportAgent().verstuur_onboarding(sessie, invoer.medewerker_id)
    except LookupError as fout:
        raise HTTPException(status_code=404, detail=str(fout)) from fout
    await sessie.commit()
    return resultaat


@router.get("/berichten", response_model=list[BerichtUit])
async def lees_berichten(
    alleen_klaar: bool = True, sessie: AsyncSession = Depends(get_sessie)
) -> list[BerichtUit]:
    """De outbox: berichten die klaarstaan, met hun volledige tekst.

    Zolang er geen WhatsApp- of e-mailkoppeling is, kan Sebas hier nalezen wat
    er verstuurd zou worden.
    """
    query = select(Bericht).order_by(Bericht.aangemaakt_op.desc()).limit(100)
    if alleen_klaar:
        query = query.where(Bericht.status == str(BerichtStatus.KLAAR))
    resultaat = await sessie.execute(query)
    return [BerichtUit.van_model(b) for b in resultaat.scalars().all()]


@router.post("/berichten/{bericht_id}/verstuurd", response_model=BerichtUit)
async def markeer_verstuurd(
    bericht_id: int, sessie: AsyncSession = Depends(get_sessie)
) -> BerichtUit:
    """Leg vast dat een bericht daadwerkelijk is verstuurd."""
    try:
        bericht = await markeer_bericht_verstuurd(sessie, bericht_id)
    except LookupError as fout:
        raise HTTPException(status_code=404, detail=str(fout)) from fout
    await sessie.commit()
    return BerichtUit.van_model(bericht)


@router.get("/sjablonen", response_model=list[SjabloonUit])
async def lees_sjablonen() -> list[SjabloonUit]:
    """Alles wat Support kan versturen — meer is er niet.

    Handig om te controleren: dit is de volledige verzameling teksten die ooit
    namens WOSZ naar een medewerker gaat, op de kennisbankantwoorden na.
    """
    return [
        SjabloonUit(
            naam=s.naam,
            kanaal=str(s.kanaal),
            onderwerp=s.onderwerp,
            body=s.body,
            variabelen=sorted(s.variabelen),
        )
        for s in alle_sjablonen().values()
    ]
