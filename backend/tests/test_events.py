"""Tests voor de event-bus tussen agents."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from sqlalchemy import select

from app.core.domein import EventStatus
from app.core.events import (
    EVENT_TYPES,
    NoShowGesignaleerd,
    UrenGewerkt,
    handelt,
    publiceer,
    verwerk_pending,
)
from app.db.models import AgentEvent


async def test_event_wordt_als_pending_weggeschreven(sessie):
    await publiceer(
        sessie,
        UrenGewerkt(
            match_id=1, medewerker_id=2, bedrijf_id=3, uren=6.0, datum="2026-08-17"
        ),
    )

    event = (await sessie.execute(select(AgentEvent))).scalars().one()
    assert event.type == "uren.gewerkt"
    assert event.bron_afdeling == "matching"
    assert event.doel_afdeling == "financieel"
    assert event.status == str(EventStatus.PENDING)


async def test_events_zijn_gestructureerd_en_weigeren_vrije_tekst():
    """Harde eis: agents kunnen elkaar geen vrije tekst sturen.

    Een extra veld met een boodschap wordt geweigerd door de envelope.
    """
    with pytest.raises(ValidationError):
        UrenGewerkt(
            match_id=1,
            medewerker_id=2,
            bedrijf_id=3,
            uren=6.0,
            datum="2026-08-17",
            bericht="doe hier even iets mee",  # type: ignore[call-arg]
        )


async def test_ontbrekend_veld_wordt_geweigerd():
    with pytest.raises(ValidationError):
        NoShowGesignaleerd(match_id=1, medewerker_id=2)  # type: ignore[call-arg]


async def test_verwerking_markeert_het_event_als_verwerkt(sessie):
    await publiceer(
        sessie,
        NoShowGesignaleerd(
            match_id=1,
            medewerker_id=2,
            medewerker_naam="Milan",
            bedrijf_naam="Café De Kust",
            aantal_no_shows=1,
        ),
    )

    aantal = await verwerk_pending(sessie)

    assert aantal == 1
    event = (await sessie.execute(select(AgentEvent))).scalars().one()
    assert event.status == str(EventStatus.VERWERKT)
    assert event.verwerkt_op is not None


async def test_mislukt_event_stopt_na_max_pogingen(sessie):
    """Een event zonder handler blijft niet eeuwig rondzingen."""
    event = AgentEvent(
        type="onbekend.type",
        bron_afdeling="matching",
        doel_afdeling="support",
        payload={},
        status=str(EventStatus.PENDING),
    )
    sessie.add(event)
    await sessie.flush()

    for _ in range(3):
        await verwerk_pending(sessie, max_pogingen=3)

    assert event.status == str(EventStatus.MISLUKT)
    assert event.pogingen == 3
    assert "Onbekend eventtype" in (event.laatste_fout or "")


def test_alle_eventtypes_hebben_een_handler():
    """Elk gedefinieerd eventtype moet door een afdeling opgepikt worden."""
    from app.core.events import _HANDLERS

    zonder_handler = set(EVENT_TYPES) - set(_HANDLERS)
    assert not zonder_handler, f"Eventtypes zonder ontvanger: {zonder_handler}"


async def test_agent_mag_niet_namens_andere_afdeling_publiceren(sessie):
    from app.agents.support import SupportAgent

    agent = SupportAgent()
    with pytest.raises(PermissionError):
        await agent.publiceer(
            sessie,
            UrenGewerkt(
                match_id=1, medewerker_id=2, bedrijf_id=3, uren=6.0, datum="2026-08-17"
            ),
        )
