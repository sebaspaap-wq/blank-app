"""Zet de agents één keer aan het werk, zodat het dashboard niet leeg opent.

Na ``app.db.seed`` staan er wel gegevens in de database, maar heeft nog geen
enkele agent iets gedaan — het dashboard toont dan overal nullen. Dit script
laat Matching de openstaande shifts vullen en Marketing de week inplannen, en
handelt de events daartussen af.

Draai met:  python -m app.db.demo
"""

from __future__ import annotations

import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.marketing import MarketingAgent
from app.agents.matching import MatchingAgent
from app.core.events import verwerk_pending
from app.db.session import maak_tabellen, sessie

# Deze imports registreren de event-handlers van de andere afdelingen.
import app.agents.financieel  # noqa: F401
import app.agents.support  # noqa: F401


async def draai_demo(s: AsyncSession) -> dict[str, int]:
    """Laat de agents één ronde werk doen."""
    shifts = await MatchingAgent().match_open_shifts(s)
    gematcht = sum(len(shift["gematcht"]) for shift in shifts)

    # Events afhandelen: hierdoor waarschuwt Support, boekt Financieel de uren
    # en plant Marketing content voor de shifts die niet gevuld raakten.
    await verwerk_pending(s)

    posts = await MarketingAgent().plan_week(s, aantal=3)

    await s.commit()
    return {"gematcht": gematcht, "posts": len(posts)}


async def main() -> None:
    await maak_tabellen()
    async with sessie() as s:
        resultaat = await draai_demo(s)
    print(
        f"Agents gedraaid: {resultaat['gematcht']} shift(s) gematcht, "
        f"{resultaat['posts']} post(s) ingepland."
    )


if __name__ == "__main__":
    asyncio.run(main())
