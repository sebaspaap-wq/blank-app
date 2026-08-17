"""Tijdelijke ontvangers voor Financieel en Marketing (Fase 1).

De Matching-agent publiceert al events naar Financieel (gewerkte uren, behaalde
levels) en Marketing (wervingstekort). Die agents worden pas in Fase 2 en 3
gebouwd. Zonder ontvanger zou de event-bus die berichten na drie pogingen als
mislukt wegzetten.

Deze module registreert daarom minimale ontvangers die het event vastleggen in
het activiteitenlog van de juiste afdeling. Ze nemen geen beslissingen, zetten
geen bedragen klaar en versturen niets — dat komt met de echte agents.

Bij Fase 2 en 3 vervangen de echte agents deze handlers.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.activity import log_activiteit
from app.core.domein import Afdeling, Tier
from app.core.events import LevelBereikt, UrenGewerkt, WervingstekortGemeld, handelt
from app.db.models import AgentEvent


@handelt(UrenGewerkt)
async def _op_uren_gewerkt(
    sessie: AsyncSession, event: UrenGewerkt, bron: AgentEvent
) -> None:
    await log_activiteit(
        sessie,
        afdeling=Afdeling.FINANCIEEL,
        tekst=f"{event.uren:.0f} uur toegevoegd aan het weekoverzicht ({event.datum})",
        tier=Tier.ZELFSTANDIG,
        event_id=bron.id,
    )


@handelt(LevelBereikt)
async def _op_level_bereikt(
    sessie: AsyncSession, event: LevelBereikt, bron: AgentEvent
) -> None:
    bedrag = event.bonus_bedrag_cent / 100
    await log_activiteit(
        sessie,
        afdeling=Afdeling.FINANCIEEL,
        tekst=(
            f"Levelbonus van €{bedrag:.0f} genoteerd voor {event.medewerker_naam} "
            f"({event.level_naam}) — nog niet klaargezet ter goedkeuring"
        ),
        tier=Tier.ZELFSTANDIG,
        event_id=bron.id,
    )


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
