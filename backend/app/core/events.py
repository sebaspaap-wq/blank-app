"""Gestructureerde event-bus tussen de agents.

Harde eis uit de opdracht: agents communiceren nooit rechtstreeks met elkaar via
vrije tekst. Dat wordt hier afgedwongen doordat het enige communicatiekanaal
deze bus is, en de bus uitsluitend gevalideerde Pydantic-envelopes accepteert.
Een agent kan dus geen zin naar een andere agent sturen — alleen een event met
vastgelegde velden.

Transport is een Postgres-tabel met polling (``agent_events``), zoals hoofdstuk 2
voorschrijft voor de MVP. Redis is pas bij schaal nodig; de interface hieronder
verandert daar niet van.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.domein import Afdeling, EventStatus, nu
from app.db.models import AgentEvent


class Envelope(BaseModel):
    """Basis voor elk event tussen agents.

    ``model_config`` staat geen onbekende velden toe: een agent die extra
    informatie wil meesmokkelen, krijgt een validatiefout in plaats van een
    doorgegeven vrije tekst.
    """

    model_config = ConfigDict(extra="forbid")

    EVENT_TYPE: ClassVar[str]
    BRON: ClassVar[Afdeling]
    DOEL: ClassVar[Afdeling]


# ---------------------------------------------------------------------------
# Eventtypes — de pijlen uit het architectuurdiagram, in code
# ---------------------------------------------------------------------------


class UrenGewerkt(Envelope):
    """Matching meldt gewerkte uren aan Financieel."""

    EVENT_TYPE: ClassVar[str] = "uren.gewerkt"
    BRON: ClassVar[Afdeling] = Afdeling.MATCHING
    DOEL: ClassVar[Afdeling] = Afdeling.FINANCIEEL

    match_id: int
    medewerker_id: int
    bedrijf_id: int
    uren: float
    datum: str


class NoShowGesignaleerd(Envelope):
    """Matching meldt een no-show aan Support, die de medewerker waarschuwt."""

    EVENT_TYPE: ClassVar[str] = "medewerker.no_show"
    BRON: ClassVar[Afdeling] = Afdeling.MATCHING
    DOEL: ClassVar[Afdeling] = Afdeling.SUPPORT

    match_id: int
    medewerker_id: int
    medewerker_naam: str
    bedrijf_naam: str
    aantal_no_shows: int


class WervingstekortGemeld(Envelope):
    """Matching meldt aan Marketing dat er te weinig kandidaten zijn."""

    EVENT_TYPE: ClassVar[str] = "werving.tekort"
    BRON: ClassVar[Afdeling] = Afdeling.MATCHING
    DOEL: ClassVar[Afdeling] = Afdeling.MARKETING

    functie: str
    open_plekken: int
    datum: str


class LevelBereikt(Envelope):
    """Matching meldt aan Financieel dat een bonusdrempel is gehaald."""

    EVENT_TYPE: ClassVar[str] = "medewerker.level_bereikt"
    BRON: ClassVar[Afdeling] = Afdeling.MATCHING
    DOEL: ClassVar[Afdeling] = Afdeling.FINANCIEEL

    medewerker_id: int
    medewerker_naam: str
    nieuw_level: int
    level_naam: str
    bonus_bedrag_cent: int
    seizoen_uren: float


EVENT_TYPES: dict[str, type[Envelope]] = {
    cls.EVENT_TYPE: cls
    for cls in (UrenGewerkt, NoShowGesignaleerd, WervingstekortGemeld, LevelBereikt)
}


# ---------------------------------------------------------------------------
# Publiceren en afhandelen
# ---------------------------------------------------------------------------

Handler = Callable[[AsyncSession, Any, AgentEvent], Awaitable[None]]

_HANDLERS: dict[str, Handler] = {}


class GeenHandlerError(RuntimeError):
    """Er is een event gepubliceerd waarvoor geen agent zich heeft aangemeld."""


class DubbeleHandlerError(RuntimeError):
    """Twee modules melden zich aan voor hetzelfde eventtype."""


def handelt(event_type: type[Envelope]) -> Callable[[Handler], Handler]:
    """Meld een agent aan als afhandelaar van één eventtype.

    Weigert een tweede aanmelding voor hetzelfde type. Zonder die controle zou
    de laatst geïmporteerde module stilletjes winnen — precies het soort fout
    dat pas in productie opvalt, bijvoorbeeld wanneer een echte agent een
    tijdelijke ontvanger vervangt maar die oude import blijft staan.
    """

    def _wrap(fn: Handler) -> Handler:
        bestaand = _HANDLERS.get(event_type.EVENT_TYPE)
        if bestaand is not None and bestaand is not fn:
            raise DubbeleHandlerError(
                f"Eventtype '{event_type.EVENT_TYPE}' heeft al een handler "
                f"({bestaand.__module__}.{bestaand.__qualname__}); "
                f"{fn.__module__}.{fn.__qualname__} probeert die te overschrijven. "
                "Verwijder de oude ontvanger in plaats van er een naast te zetten."
            )
        _HANDLERS[event_type.EVENT_TYPE] = fn
        return fn

    return _wrap


async def publiceer(sessie: AsyncSession, envelope: Envelope) -> AgentEvent:
    """Zet een event op de queue voor de doelafdeling."""
    event = AgentEvent(
        type=envelope.EVENT_TYPE,
        bron_afdeling=str(envelope.BRON),
        doel_afdeling=str(envelope.DOEL),
        payload=envelope.model_dump(mode="json"),
        status=str(EventStatus.PENDING),
    )
    sessie.add(event)
    await sessie.flush()
    return event


async def pending_events(sessie: AsyncSession, limiet: int = 50) -> list[AgentEvent]:
    resultaat = await sessie.execute(
        select(AgentEvent)
        .where(AgentEvent.status == str(EventStatus.PENDING))
        .order_by(AgentEvent.id)
        .limit(limiet)
    )
    return list(resultaat.scalars().all())


async def verwerk_pending(sessie: AsyncSession, max_pogingen: int = 3) -> int:
    """Handel alle wachtende events af. Geeft het aantal verwerkte events terug."""
    verwerkt = 0
    for event in await pending_events(sessie):
        event.pogingen += 1
        try:
            model = EVENT_TYPES.get(event.type)
            if model is None:
                raise GeenHandlerError(f"Onbekend eventtype '{event.type}'")
            handler = _HANDLERS.get(event.type)
            if handler is None:
                raise GeenHandlerError(f"Geen handler voor eventtype '{event.type}'")

            envelope = model.model_validate(event.payload)
            await handler(sessie, envelope, event)

            event.status = str(EventStatus.VERWERKT)
            event.verwerkt_op = nu()
            event.laatste_fout = None
            verwerkt += 1
        except Exception as fout:  # noqa: BLE001 — fout hoort in de audit-trail
            event.laatste_fout = f"{type(fout).__name__}: {fout}"
            if event.pogingen >= max_pogingen:
                event.status = str(EventStatus.MISLUKT)
    return verwerkt
