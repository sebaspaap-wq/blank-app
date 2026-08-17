"""Async database-engine en sessiebeheer."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings
from app.db.models import Base

_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        _engine = create_async_engine(get_settings().database_url, future=True)
    return _engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    global _sessionmaker
    if _sessionmaker is None:
        _sessionmaker = async_sessionmaker(
            get_engine(), expire_on_commit=False, class_=AsyncSession
        )
    return _sessionmaker


def configureer_engine(engine: AsyncEngine) -> None:
    """Vervang de engine (gebruikt door de tests, die op SQLite draaien)."""
    global _engine, _sessionmaker
    _engine = engine
    _sessionmaker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def maak_tabellen() -> None:
    async with get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def sessie() -> AsyncIterator[AsyncSession]:
    """Contextmanager voor achtergrondtaken (scheduler, event-worker)."""
    async with get_sessionmaker()() as s:
        yield s


async def get_sessie() -> AsyncIterator[AsyncSession]:
    """FastAPI-dependency."""
    async with get_sessionmaker()() as s:
        yield s
