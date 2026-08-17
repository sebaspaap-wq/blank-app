"""Activiteitenlog — de audit-trail van het hele systeem.

Randvoorwaarde 6.4 van de bouwopdracht: elke actie van elke agent komt hier
terecht. Dat is hier geen afspraak maar een constructie: agents voeren acties
uit via ``BaseAgent.voer_uit``, en dat pad schrijft altijd eerst een logregel
weg. Zie app/agents/base.py.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.domein import Afdeling, Tier, nu
from app.db.models import Activiteit


async def log_activiteit(
    sessie: AsyncSession,
    *,
    afdeling: Afdeling,
    tekst: str,
    tier: Tier | None = None,
    beslissing_id: int | None = None,
    event_id: int | None = None,
) -> Activiteit:
    """Schrijf één regel naar het activiteitenlog.

    ``tier`` is optioneel omdat niet elke actie een tier-classificatie heeft
    (bijvoorbeeld een puur informatieve rapportageregel). Waar een actie wel
    onder een tier valt, wordt die altijd meegeschreven.
    """
    activiteit = Activiteit(
        tijd=nu(),
        tekst=tekst,
        afdeling=str(afdeling),
        tier=int(tier) if tier is not None else None,
        beslissing_id=beslissing_id,
        event_id=event_id,
    )
    sessie.add(activiteit)
    await sessie.flush()
    return activiteit


async def recente_activiteiten(sessie: AsyncSession, limiet: int = 40) -> list[Activiteit]:
    """Laatste activiteiten, nieuwste eerst — de volgorde die de frontend toont."""
    resultaat = await sessie.execute(
        select(Activiteit).order_by(Activiteit.tijd.desc(), Activiteit.id.desc()).limit(limiet)
    )
    return list(resultaat.scalars().all())


async def activiteiten_van_afdeling(
    sessie: AsyncSession, afdeling: Afdeling, limiet: int = 8
) -> list[Activiteit]:
    resultaat = await sessie.execute(
        select(Activiteit)
        .where(Activiteit.afdeling == str(afdeling))
        .order_by(Activiteit.tijd.desc(), Activiteit.id.desc())
        .limit(limiet)
    )
    return list(resultaat.scalars().all())
