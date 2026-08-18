"""De klok van de organisatie.

Zonder deze module gebeurt er alleen iets als iemand op een knop drukt. Met
deze module draait de organisatie door terwijl niemand kijkt: shifts worden
gematcht, uren opgevolgd, content gepland, campagnes beoordeeld en facturen
afgesloten.

Wat hier bewust *niet* gebeurt: er wordt niets verstuurd, betaald of
gepubliceerd dat een mens nog had moeten zien. De taken hieronder roepen
uitsluitend agentmethodes aan, en die lopen allemaal via de tier-engine. Een
taak kan dus nooit meer dan de agent zelf mag:

  tier 1  gebeurt meteen en komt in het activiteitenlog
  tier 2  krijgt een termijn; de sweep in ``main.py`` voert hem daarna uit
  tier 3  blijft staan tot Sebas kiest

Elke taak draait in zijn eigen sessie en vangt zijn eigen fouten af. Eén taak
die omvalt, mag de rest van de organisatie niet stilzetten.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.financieel import FinancieelAgent
from app.agents.marketing import MarketingAgent
from app.agents.matching import MatchingAgent
from app.config import get_settings
from app.core.domein import nu
from app.core.events import verwerk_pending
from app.db.session import sessie

logger = logging.getLogger(__name__)

MINUUT = 60
UUR = 60 * MINUUT


@dataclass(frozen=True)
class Taak:
    """Eén terugkerende opdracht.

    ``interval`` is de tijd tussen twee rondes. ``eerste_pauze`` bepaalt hoe
    lang er na het opstarten wordt gewacht; taken die dagelijks werk doen hoeven
    niet meteen bij elke herstart af te gaan.
    """

    naam: str
    interval: int
    werk: Callable[[AsyncSession], Awaitable[str | None]]
    eerste_pauze: int = 0


# ---------------------------------------------------------------------------
# Het werk zelf
# ---------------------------------------------------------------------------


async def match_open_shifts(s: AsyncSession) -> str | None:
    """Vul openstaande shifts.

    Een aanvraag wordt al gematcht op het moment dat hij binnenkomt. Deze ronde
    is voor wat er daarna verandert: iemand meldt zich aan, past zijn
    beschikbaarheid aan, of zegt een shift af. Zonder deze taak zou zo'n shift
    open blijven staan tot er toevallig weer iemand een knop indrukt.
    """
    verslag = await MatchingAgent().match_open_shifts(s)
    gematcht = sum(len(r["gematcht"]) for r in verslag)
    return f"{gematcht} plek(ken) gevuld" if gematcht else None


async def volg_afgelopen_shifts_op(s: AsyncSession) -> str | None:
    """Herinner aan ontbrekende uren en leg hardnekkige gevallen voor."""
    verslag = await MatchingAgent().volg_afgelopen_shifts_op(s)
    delen = []
    if verslag["herinnerd"]:
        delen.append(f"{len(verslag['herinnerd'])} herinnering(en)")
    if verslag["geescaleerd"]:
        delen.append(f"{len(verslag['geescaleerd'])} voorgelegd aan Sebas")
    return ", ".join(delen) or None


async def plan_content(s: AsyncSession) -> str | None:
    """Houd de content-kalender gevuld (tier 1, binnen de bestaande huisstijl)."""
    gepland = await MarketingAgent().plan_week(s, aantal=3)
    return f"{len(gepland)} post(s) ingepland" if gepland else None


async def beoordeel_campagnes(s: AsyncSession) -> str | None:
    """Kijk of de campagnes van gisteren binnen de verwachting bleven."""
    bevindingen = await MarketingAgent().beoordeel_resultaten(s)
    if not bevindingen:
        return None
    voorgelegd = sum(1 for b in bevindingen if b.get("beslissing_id"))
    return (
        f"{len(bevindingen)} campagne(s) beoordeeld"
        + (f", {voorgelegd} voorgelegd aan Sebas" if voorgelegd else "")
    )


async def sluit_vorige_maand_af(s: AsyncSession) -> str | None:
    """Rond op de eerste van de maand de facturen van de vorige maand af.

    De taak draait dagelijks maar doet alleen op de eerste iets. Dat is
    eenvoudiger en betrouwbaarder dan een maandelijkse timer die een herstart
    van de server niet overleeft.
    """
    vandaag = date.today()
    if vandaag.day != 1:
        return None
    vorige = vandaag - timedelta(days=1)
    periode = f"{vorige.year:04d}-{vorige.month:02d}"
    verslag = await FinancieelAgent().sluit_periode_af(s, periode)
    return f"{len(verslag)} factuur/facturen van {periode} afgerond" if verslag else None


#: De vaste dienstregeling. De intervallen zijn ruim gekozen: de agents werken
#: in minuten, niet in seconden, en elke ronde die niets vindt is verspilde
#: databasetijd.
TAKEN: tuple[Taak, ...] = (
    Taak("matching", interval=10 * MINUUT, werk=match_open_shifts, eerste_pauze=MINUUT),
    Taak(
        "uren-opvolging",
        interval=6 * UUR,
        werk=volg_afgelopen_shifts_op,
        eerste_pauze=2 * MINUUT,
    ),
    Taak("contentplanning", interval=24 * UUR, werk=plan_content, eerste_pauze=5 * MINUUT),
    Taak(
        "campagnebeoordeling",
        interval=24 * UUR,
        werk=beoordeel_campagnes,
        eerste_pauze=6 * MINUUT,
    ),
    Taak(
        "facturen",
        interval=24 * UUR,
        werk=sluit_vorige_maand_af,
        eerste_pauze=7 * MINUUT,
    ),
)


# ---------------------------------------------------------------------------
# Draaien
# ---------------------------------------------------------------------------


async def draai_taak(taak: Taak) -> str | None:
    """Voer één ronde uit, in een eigen sessie.

    De events die de agent onderweg publiceert worden hier meteen afgehandeld.
    De losse event-worker zou dat ook doen, maar dan staat het resultaat van
    één ronde verspreid over twee transacties en is een logregel lastiger terug
    te lezen.
    """
    async with sessie() as s:
        uitkomst = await taak.werk(s)
        await verwerk_pending(s, get_settings().event_max_pogingen)
        await s.commit()
        return uitkomst


async def _lus(taak: Taak) -> None:
    if taak.eerste_pauze:
        await asyncio.sleep(taak.eerste_pauze)
    while True:
        try:
            uitkomst = await draai_taak(taak)
            if uitkomst:
                logger.info("[%s] %s", taak.naam, uitkomst)
        except asyncio.CancelledError:
            raise
        except Exception:  # noqa: BLE001 — een taak mag de rest niet meeslepen
            logger.exception("Fout in geplande taak '%s'", taak.naam)
        await asyncio.sleep(taak.interval)


def start(taken: tuple[Taak, ...] = TAKEN) -> list[asyncio.Task[None]]:
    """Start alle taken als achtergrondtaken."""
    return [
        asyncio.create_task(_lus(taak), name=f"wosz-{taak.naam}") for taak in taken
    ]


def volgende_rondes(
    taken: tuple[Taak, ...] = TAKEN, *, vanaf: datetime | None = None
) -> list[dict[str, str]]:
    """Wat er gepland staat, voor het dashboard.

    Geeft geen echte kloktijden terug maar het ritme: de scheduler heeft geen
    persistente agenda, dus na een herstart begint alles opnieuw te tellen.
    """
    vanaf = vanaf or nu()
    return [
        {
            "naam": taak.naam,
            "elke": _leesbaar(taak.interval),
            "eerste": (vanaf + timedelta(seconds=taak.eerste_pauze)).strftime("%H:%M"),
        }
        for taak in taken
    ]


DAG = 24 * UUR


def _leesbaar(seconden: int) -> str:
    if seconden % DAG == 0:
        dagen = seconden // DAG
        return "elke dag" if dagen == 1 else f"elke {dagen} dagen"
    if seconden % UUR == 0:
        uren = seconden // UUR
        return "elk uur" if uren == 1 else f"elke {uren} uur"
    minuten = seconden // MINUUT
    return "elke minuut" if minuten == 1 else f"elke {minuten} minuten"


__all__ = ["TAKEN", "Taak", "draai_taak", "start", "volgende_rondes"]
