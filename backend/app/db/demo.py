"""Zet de agents één keer aan het werk, zodat het dashboard niet leeg opent.

Na ``app.db.seed`` staan er wel gegevens in de database, maar heeft nog geen
enkele agent iets gedaan — het dashboard toont dan overal nullen. Dit script
laat Matching de openstaande shifts vullen en Marketing de week inplannen, en
handelt de events daartussen af.

Draai met:  python -m app.db.demo
"""

from __future__ import annotations

import asyncio
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.marketing import MarketingAgent
from app.agents.matching import MatchingAgent
from app.core.domein import MatchStatus
from app.core.events import verwerk_pending
from app.db.models import Match, Shift
from app.db.session import maak_tabellen, sessie

# Deze imports registreren de event-handlers van de andere afdelingen.
import app.agents.financieel  # noqa: F401
import app.agents.support  # noqa: F401


async def draai_demo(s: AsyncSession) -> dict[str, int]:
    """Laat de agents één ronde werk doen."""
    agent = MatchingAgent()
    shifts = await agent.match_open_shifts(s)
    gematcht = sum(len(shift["gematcht"]) for shift in shifts)

    # Uren boeken van shifts die al voorbij zijn. Dit is de stap die in de
    # praktijk het meeste in gang zet: het level gaat omhoog, Financieel maakt
    # het factuurconcept en de vriendenbonus schuift op.
    geboekt = await _boek_gewerkte_uren(s, agent)

    # Events afhandelen: hierdoor waarschuwt Support, boekt Financieel de uren
    # en plant Marketing content voor de shifts die niet gevuld raakten.
    await verwerk_pending(s)

    posts = await MarketingAgent().plan_week(s, aantal=3)

    await s.commit()
    return {"gematcht": gematcht, "posts": len(posts), "geboekt": geboekt}


async def _boek_gewerkte_uren(s: AsyncSession, agent: MatchingAgent) -> int:
    """Boek de uren van bevestigde shifts waarvan de datum al voorbij is."""
    resultaat = await s.execute(
        select(Match, Shift)
        .join(Shift, Shift.id == Match.shift_id)
        .where(Match.status == str(MatchStatus.BEVESTIGD), Shift.datum < date.today())
    )
    rijen = list(resultaat.all())
    for match, shift in rijen:
        await agent.registreer_gewerkte_uren(s, match.id, shift.duur_uren)
    if rijen:
        await verwerk_pending(s)
    return len(rijen)


async def main() -> None:
    await maak_tabellen()
    async with sessie() as s:
        resultaat = await draai_demo(s)
    print(
        f"Agents gedraaid: {resultaat['gematcht']} shift(s) gematcht, "
        f"{resultaat['geboekt']} shift(s) afgerekend, "
        f"{resultaat['posts']} post(s) ingepland."
    )


if __name__ == "__main__":
    asyncio.run(main())
