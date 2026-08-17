"""Tijdelijke ontvanger voor Marketing (tot Fase 3).

De Matching-agent publiceert een ``werving.tekort``-event zodra een shift niet
gevuld raakt. De Marketing-agent wordt pas in Fase 3 gebouwd; zonder ontvanger
zou de bus die berichten na drie pogingen als mislukt wegzetten.

Deze handler legt het tekort vast in het activiteitenlog van Marketing. Hij
neemt geen beslissingen, verschuift geen budget en plant geen content — dat komt
met de echte agent.

De tegenhangers voor Financieel zijn in Fase 2 vervangen door de echte
Financieel-agent (app/agents/financieel.py).
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.activity import log_activiteit
from app.core.domein import Afdeling, Tier
from app.core.events import WervingstekortGemeld, handelt
from app.db.models import AgentEvent


@handelt(WervingstekortGemeld)
async def _op_wervingstekort(
    sessie: AsyncSession, event: WervingstekortGemeld, bron: AgentEvent
) -> None:
    await log_activiteit(
        sessie,
        afdeling=Afdeling.MARKETING,
        tekst=(
            f"Wervingstekort doorgegeven: {event.open_plekken}x {event.functie} "
            f"open op {event.datum}"
        ),
        tier=Tier.ZELFSTANDIG,
        event_id=bron.id,
    )
