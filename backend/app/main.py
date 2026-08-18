"""FastAPI-applicatie voor de WOSZ AI-organisatie.

Startvolgorde is hier belangrijk: de imports onderaan registreren de agents,
hun uitvoerders en hun event-handlers. Zonder die imports staat de tier-engine
er wel, maar weet hij niet wat hij moet uitvoeren.

De uitbetalingsmodule wordt hier geïmporteerd — vanuit de applicatielaag, niet
vanuit een agent. Die richting is de kern van de betaalscheiding.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import directie as directie_api
from app.api import financieel as financieel_api
from app.api import horeca as horeca_api
from app.api import marketing as marketing_api
from app.api import matching as matching_api
from app.api import medewerker as medewerker_api
from app.api import support as support_api
from app import scheduler
from app.config import get_settings
from app.core.events import verwerk_pending
from app.core.tiers import sweep_verlopen_tier2
from app.db.session import maak_tabellen, sessie

# Deze imports hebben bijwerkingen: ze vullen de registries van de tier-engine
# en de event-bus. Niet verwijderen omdat een linter ze "ongebruikt" noemt.
from app.agents import financieel as _financieel_agent  # noqa: F401
from app.agents import matching as _matching_agent  # noqa: F401
from app.agents import marketing as _marketing_agent  # noqa: F401
from app.agents import support as _support_agent  # noqa: F401
from app import payouts as _payouts  # noqa: F401

logger = logging.getLogger(__name__)


def _zet_logging_aan() -> None:
    """Laat het werk van de achtergrondtaken in het venster zien.

    Zonder dit blijft de logger van ``app.*`` op WARNING staan en zie je in de
    terminal alleen webverkeer. Dan lijkt het alsof er niets gebeurt — terwijl
    de agents doorwerken — en de console-driver, die berichten juist naar het
    log schrijft in plaats van te versturen, zou helemaal onzichtbaar zijn.
    """
    app_logger = logging.getLogger("app")
    if app_logger.handlers:
        return
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s  %(message)s", "%H:%M:%S"))
    app_logger.addHandler(handler)
    app_logger.setLevel(logging.INFO)
    app_logger.propagate = False

#: Hoe vaak de tier 2-sweep draait (seconden). Deadlines zijn in uren, dus
#: elke vijf minuten kijken is ruim voldoende.
SWEEP_INTERVAL = 300


async def _event_worker() -> None:
    """Handelt wachtende events tussen agents af."""
    instellingen = get_settings()
    while True:
        try:
            async with sessie() as s:
                aantal = await verwerk_pending(s, instellingen.event_max_pogingen)
                await s.commit()
                if aantal:
                    logger.info("%d event(s) tussen agents afgehandeld", aantal)
        except asyncio.CancelledError:
            raise
        except Exception:  # noqa: BLE001 — de worker mag nooit omvallen
            logger.exception("Fout in de event-worker")
        await asyncio.sleep(instellingen.event_poll_seconden)


async def _tier2_worker() -> None:
    """Voert tier 2-beslissingen uit waarvan de termijn is verstreken."""
    while True:
        await asyncio.sleep(SWEEP_INTERVAL)
        try:
            async with sessie() as s:
                uitgevoerd = await sweep_verlopen_tier2(s)
                await s.commit()
                for beslissing in uitgevoerd:
                    logger.info(
                        "Tier 2-termijn verstreken, uitgevoerd: %s", beslissing.titel
                    )
        except asyncio.CancelledError:
            raise
        except Exception:  # noqa: BLE001
            logger.exception("Fout in de tier 2-sweep")


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    _zet_logging_aan()
    await maak_tabellen()
    # De twee workers hieronder houden de bestaande afspraken lopend (events en
    # verlopen tier 2-termijnen); scheduler.start() zet de organisatie zelf aan
    # het werk. Zonder dat laatste gebeurt er alleen iets als iemand klikt.
    taken = [
        asyncio.create_task(_event_worker(), name="wosz-event-worker"),
        asyncio.create_task(_tier2_worker(), name="wosz-tier2-sweep"),
        *scheduler.start(),
    ]
    try:
        yield
    finally:
        for taak in taken:
            taak.cancel()
        for taak in taken:
            with contextlib.suppress(asyncio.CancelledError):
                await taak


def maak_app() -> FastAPI:
    instellingen = get_settings()
    app = FastAPI(
        title="WOSZ AI-organisatie",
        description=(
            "Backend voor de vier afdelingsagents en de coordinerende Directie-agent. "
            "Uitbetalingen worden nooit door het systeem uitgevoerd; zie "
            "app/payouts/README.md."
        ),
        version="0.1.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=instellingen.cors_origin_lijst,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(directie_api.router)
    app.include_router(matching_api.router)
    app.include_router(support_api.router)
    app.include_router(financieel_api.router)
    app.include_router(marketing_api.router)
    app.include_router(medewerker_api.router)
    app.include_router(horeca_api.router)

    @app.get("/health", tags=["systeem"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = maak_app()
