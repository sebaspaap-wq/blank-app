"""Basis voor alle afdelingsagents — de lichte eigen orchestratielaag.

Elke agent heeft een eigen afdeling, een eigen systeemprompt en een eigen set
tools. Wat ze delen is het uitvoerpad: een agent doet nooit rechtstreeks iets,
maar levert een ``Voorstel`` in bij ``voer_uit``. Die methode stuurt het
voorstel door de tier-engine, en de tier-engine schrijft in élke tak een regel
naar het activiteitenlog.

Dat is de reden dat loggen hier geen losse aanroep is: een agent kan een actie
niet uitvoeren zonder erlangs te komen. "Log alles" (randvoorwaarde 6.4) is
daarmee een eigenschap van de constructie, niet een instructie die een model
moet onthouden.
"""

from __future__ import annotations

from abc import ABC
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core import events
from app.core.activity import log_activiteit
from app.core.domein import Afdeling, Tier
from app.core.tiers import Uitkomst, Voorstel, behandel_voorstel


class BaseAgent(ABC):
    """Gemeenschappelijk gedrag voor Marketing, Matching, Support en Financieel."""

    #: De afdeling waaronder deze agent logt en events publiceert.
    afdeling: Afdeling

    #: Systeemprompt voor de LLM-beslissingen van deze agent.
    systeemprompt: str = ""

    def __init__(self) -> None:
        if not getattr(self, "afdeling", None):
            raise TypeError(f"{type(self).__name__} moet een afdeling declareren")

    # -- uitvoeren ---------------------------------------------------------

    async def voer_uit(self, sessie: AsyncSession, voorstel: Voorstel) -> Uitkomst:
        """Het enige pad waarlangs een agent iets kan laten gebeuren.

        Bewaakt dat een agent alleen namens de eigen afdeling handelt: een
        Matching-agent kan geen voorstel indienen dat als Financieel geboekt
        wordt. Dat is de codeversie van "gescheiden verantwoordelijkheden".
        """
        if voorstel.afdeling is not self.afdeling:
            raise PermissionError(
                f"{type(self).__name__} ({self.afdeling}) mag geen voorstel indienen "
                f"namens afdeling {voorstel.afdeling}"
            )
        return await behandel_voorstel(sessie, voorstel)

    async def rapporteer(
        self, sessie: AsyncSession, tekst: str, *, tier: Tier | None = None
    ) -> None:
        """Schrijf een puur informatieve regel naar het activiteitenlog."""
        await log_activiteit(sessie, afdeling=self.afdeling, tekst=tekst, tier=tier)

    # -- communiceren met andere agents ------------------------------------

    async def publiceer(self, sessie: AsyncSession, envelope: events.Envelope) -> Any:
        """Stuur een gestructureerd event naar een andere afdeling.

        Weigert events die niet vanuit deze afdeling horen te komen, zodat een
        agent geen berichten kan versturen namens een collega.
        """
        if envelope.BRON is not self.afdeling:
            raise PermissionError(
                f"{type(self).__name__} ({self.afdeling}) mag geen event publiceren "
                f"namens afdeling {envelope.BRON}"
            )
        return await events.publiceer(sessie, envelope)
