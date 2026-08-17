"""Testfixtures.

De hele suite draait op SQLite in het geheugen en zonder netwerk: er is geen
``ANTHROPIC_API_KEY`` gezet, dus de agents draaien in hun deterministische
regelmodus. Dat maakt de tests reproduceerbaar en houdt ze snel.
"""

from __future__ import annotations

import os
from datetime import date, timedelta

import pytest
import pytest_asyncio

# Vóór het importeren van app.config zetten, anders leest de settings-cache
# eventuele echte waarden uit de omgeving.
os.environ["WOSZ_DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["ANTHROPIC_API_KEY"] = ""
os.environ["WOSZ_TIER2_DEADLINE_UREN"] = "24"

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.domein import ShiftStatus, level_voor_uren
from app.db.models import Base, Bedrijf, Doelstelling, Level, Shift, User
from app.db.session import configureer_engine

# Bijwerkingen: vullen de registries van de tier-engine en de event-bus.
import app.agents.financieel  # noqa: F401,E402
import app.agents.matching  # noqa: F401,E402
import app.agents.ontvangst_marketing  # noqa: F401,E402
import app.agents.support  # noqa: F401,E402
import app.payouts  # noqa: F401,E402


@pytest_asyncio.fixture
async def engine():
    motor = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with motor.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    configureer_engine(motor)
    yield motor
    await motor.dispose()


@pytest_asyncio.fixture
async def sessie(engine) -> AsyncSession:
    maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with maker() as s:
        yield s


@pytest.fixture
def zaterdag() -> date:
    """Een zaterdag in de nabije toekomst — handig voor beschikbaarheidstests."""
    vandaag = date.today()
    return vandaag + timedelta(days=(5 - vandaag.weekday()) % 7 + 7)


@pytest_asyncio.fixture
async def bedrijf(sessie) -> Bedrijf:
    b = Bedrijf(naam="Strandtent Zuid", plaats="Zandvoort")
    sessie.add(b)
    await sessie.flush()
    return b


async def maak_medewerker(
    sessie: AsyncSession,
    naam: str,
    *,
    functies: list[str],
    dagen: list[str],
    seizoen_uren: float = 0.0,
) -> User:
    gebruiker = User(
        naam=naam, rol="medewerker", functies=functies, beschikbare_dagen=dagen
    )
    sessie.add(gebruiker)
    await sessie.flush()
    sessie.add(
        Level(
            medewerker_id=gebruiker.id,
            seizoen_uren=seizoen_uren,
            huidig_level=level_voor_uren(seizoen_uren)["level"],
        )
    )
    await sessie.flush()
    return gebruiker


async def maak_shift(
    sessie: AsyncSession,
    bedrijf: Bedrijf,
    *,
    datum: date,
    functie: str = "bediening",
    aantal: int = 1,
) -> Shift:
    shift = Shift(
        bedrijf_id=bedrijf.id,
        datum=datum,
        tijd="17:00-23:00",
        functie=functie,
        aantal_gevraagd=aantal,
        duur_uren=6.0,
        status=str(ShiftStatus.OPEN),
    )
    sessie.add(shift)
    await sessie.flush()
    return shift


async def maak_doelstelling(sessie: AsyncSession) -> Doelstelling:
    doel = Doelstelling(
        label="Aanmeldingen deze week", waarde=128, doel=200, is_euro=False, volgorde=1
    )
    sessie.add(doel)
    await sessie.flush()
    return doel
