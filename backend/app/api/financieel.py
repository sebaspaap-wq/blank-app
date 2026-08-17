"""Endpoints van de Financieel-agent.

Let op wat hier ontbreekt: er is geen endpoint dat uitbetaalt. Goedkeuren
gebeurt via ``POST /api/directie/beslissingen/{id}/kies``, en het geld gaat de
deur uit doordat Sebas het zelf overmaakt. Zie app/payouts/README.md.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.financieel import FinancieelAgent
from app.api.schemas import FactuurUit
from app.db.models import Bedrijf, Factuur
from app.db.session import get_sessie

router = APIRouter(prefix="/api/financieel", tags=["financieel"])


@router.get("/facturen", response_model=list[FactuurUit])
async def lees_facturen(
    periode: str | None = None, sessie: AsyncSession = Depends(get_sessie)
) -> list[FactuurUit]:
    """Factuurconcepten, eventueel gefilterd op periode (bijv. ``2026-08``)."""
    query = select(Factuur).order_by(Factuur.periode.desc(), Factuur.id)
    if periode:
        query = query.where(Factuur.periode == periode)
    resultaat = await sessie.execute(query)

    facturen: list[FactuurUit] = []
    for factuur in resultaat.scalars().all():
        bedrijf = await sessie.get(Bedrijf, factuur.bedrijf_id)
        facturen.append(
            FactuurUit(
                id=factuur.id,
                bedrijf=bedrijf.naam if bedrijf else f"bedrijf {factuur.bedrijf_id}",
                periode=factuur.periode,
                uren=factuur.uren,
                bedrag_eur=factuur.bedrag_cent / 100,
                status=factuur.status,
            )
        )
    return facturen


@router.post("/periodes/{periode}/afsluiten")
async def sluit_periode_af(
    periode: str, sessie: AsyncSession = Depends(get_sessie)
) -> dict[str, Any]:
    """Rond de factuurconcepten van een periode af (tier 1).

    Een factuur sturen is geen uitbetaling: er komt geld binnen, er gaat niets
    uit. Daarom mag de agent dit zelfstandig doen.
    """
    verslag = await FinancieelAgent().sluit_periode_af(sessie, periode)
    await sessie.commit()
    return {"periode": periode, "facturen": verslag}
