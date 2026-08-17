"""Directie-agent — de coordinator.

Verzamelt wat de afdelingen hebben gedaan, stelt het dagrapport samen en houdt
bij welke beslissingen op Sebas wachten. De agent heeft leestoegang tot alle
afdelingsdata en schrijftoegang tot de beslissingen-tabel; hij voert zelf geen
afdelingsacties uit.

De vorm van wat hier uitkomt is niet vrij gekozen: het volgt exact de
datastructuren die de renderfuncties in wosz-app.html al verwachten
(``dailyReport``, ``decisions``, ``activityLog``). Zie app/api/schemas.py.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.domein import (
    AFDELINGSAGENTS,
    Afdeling,
    BeslissingStatus,
    Urgentie,
    nu,
)
from app.db.models import Activiteit, Beslissing, Doelstelling, Match, User

WEEKDAGEN = (
    "Maandag",
    "Dinsdag",
    "Woensdag",
    "Donderdag",
    "Vrijdag",
    "Zaterdag",
    "Zondag",
)
MAANDEN = (
    "januari",
    "februari",
    "maart",
    "april",
    "mei",
    "juni",
    "juli",
    "augustus",
    "september",
    "oktober",
    "november",
    "december",
)

#: Iconen en titels per afdeling, zoals de frontend ze in het dagrapport toont.
SECTIES: tuple[tuple[Afdeling, str, str], ...] = (
    (Afdeling.MARKETING, "Marketing", "\U0001f3af"),
    (Afdeling.MATCHING, "Matching", "\U0001f517"),
    (Afdeling.SUPPORT, "Support", "\U0001f4ac"),
    (Afdeling.FINANCIEEL, "Financieel", "€"),
)


def nederlandse_datum(dag: date) -> str:
    """Bijvoorbeeld 'Maandag 17 augustus 2026'."""
    return f"{WEEKDAGEN[dag.weekday()]} {dag.day} {MAANDEN[dag.month - 1]} {dag.year}"


class DirectieAgent:
    """Coordinator. Geen ``BaseAgent``: deze laag voert geen afdelingsacties uit."""

    afdeling = Afdeling.DIRECTIE

    # -- dagrapport --------------------------------------------------------

    async def dagrapport(self, sessie: AsyncSession, dag: date | None = None) -> dict[str, Any]:
        dag = dag or nu().date()
        return {
            "datum": nederlandse_datum(dag),
            "secties": await self._secties(sessie, dag),
            "voortgang": await self._voortgang(sessie),
            "aandacht": await self._aandachtspunten(sessie),
        }

    async def _secties(self, sessie: AsyncSession, dag: date) -> list[dict[str, Any]]:
        secties: list[dict[str, Any]] = []
        for afdeling, titel, icon in SECTIES:
            regels = await self._samenvatting_van_afdeling(sessie, afdeling, dag)
            secties.append({"titel": titel, "icon": icon, "items": regels})
        return secties

    async def _samenvatting_van_afdeling(
        self, sessie: AsyncSession, afdeling: Afdeling, dag: date
    ) -> list[str]:
        """Vat samen wat een afdeling vandaag heeft gedaan.

        Neemt de meest recente regels uit het activiteitenlog. Dat houdt het
        rapport eerlijk: er staat alleen in wat er echt is gebeurd, niet wat een
        model erover zou kunnen schrijven.
        """
        start, eind = _dagvenster(dag)
        resultaat = await sessie.execute(
            select(Activiteit)
            .where(
                Activiteit.afdeling == str(afdeling),
                Activiteit.tijd >= start,
                Activiteit.tijd < eind,
            )
            .order_by(Activiteit.tijd.desc(), Activiteit.id.desc())
            .limit(4)
        )
        regels = [a.tekst for a in resultaat.scalars().all()]
        return regels or ["Nog geen activiteit vandaag."]

    async def _voortgang(self, sessie: AsyncSession) -> list[dict[str, Any]]:
        resultaat = await sessie.execute(
            select(Doelstelling).order_by(Doelstelling.volgorde, Doelstelling.id)
        )
        return [
            {
                "label": d.label,
                "waarde": d.waarde,
                "doel": d.doel,
                "isEuro": d.is_euro,
            }
            for d in resultaat.scalars().all()
        ]

    async def _aandachtspunten(self, sessie: AsyncSession) -> list[str]:
        """Openstaande beslissingen, dringend eerst, als leesbare zinnen."""
        resultaat = await sessie.execute(
            select(Beslissing)
            .where(Beslissing.status == str(BeslissingStatus.OPEN))
            .order_by(Beslissing.aangemaakt_op.desc())
        )
        beslissingen = list(resultaat.scalars().all())
        beslissingen.sort(key=lambda b: 0 if b.urgentie == str(Urgentie.DRINGEND) else 1)

        punten: list[str] = []
        for b in beslissingen[:5]:
            if b.tier == 2 and b.deadline_at is not None:
                punten.append(
                    f"{b.titel} — wordt uitgevoerd als je niet ingrijpt. Zie beslissingen."
                )
            else:
                punten.append(f"{b.titel} — wacht op jouw keuze.")
        return punten

    # -- dashboardcijfers --------------------------------------------------

    async def dashboardcijfers(
        self, sessie: AsyncSession, dag: date | None = None
    ) -> dict[str, int]:
        """De vier tellers boven aan het directiedashboard."""
        dag = dag or nu().date()
        start, eind = _dagvenster(dag)

        acties = await sessie.scalar(
            select(func.count())
            .select_from(Activiteit)
            .where(Activiteit.tijd >= start, Activiteit.tijd < eind)
        )
        matches = await sessie.scalar(
            select(func.count())
            .select_from(Match)
            .where(Match.aangemaakt_op >= start, Match.aangemaakt_op < eind)
        )
        aanmeldingen = await sessie.scalar(
            select(func.count())
            .select_from(User)
            .where(
                User.rol == "medewerker",
                User.aangemaakt_op >= start,
                User.aangemaakt_op < eind,
            )
        )
        open_beslissingen = await sessie.scalar(
            select(func.count())
            .select_from(Beslissing)
            .where(Beslissing.status == str(BeslissingStatus.OPEN))
        )
        return {
            "actiesVandaag": int(acties or 0),
            "nieuweMatches": int(matches or 0),
            "aanmeldingenVandaag": int(aanmeldingen or 0),
            "openBeslissingen": int(open_beslissingen or 0),
        }

    # -- beslissingen ------------------------------------------------------

    async def beslissingen(
        self, sessie: AsyncSession
    ) -> tuple[list[Beslissing], list[Beslissing]]:
        """Geeft (open, afgehandeld) terug — de twee lijsten die het dashboard toont."""
        open_resultaat = await sessie.execute(
            select(Beslissing)
            .where(Beslissing.status == str(BeslissingStatus.OPEN))
            .order_by(Beslissing.aangemaakt_op.desc())
        )
        openstaand = list(open_resultaat.scalars().all())
        openstaand.sort(key=lambda b: 0 if b.urgentie == str(Urgentie.DRINGEND) else 1)

        afgehandeld_resultaat = await sessie.execute(
            select(Beslissing)
            .where(Beslissing.status != str(BeslissingStatus.OPEN))
            .order_by(Beslissing.afgehandeld_op.desc())
            .limit(20)
        )
        return openstaand, list(afgehandeld_resultaat.scalars().all())


def _dagvenster(dag: date):
    """Start en eind van een kalenderdag als timezone-aware datetimes."""
    from datetime import datetime, time, timezone

    start = datetime.combine(dag, time.min, tzinfo=timezone.utc)
    return start, start + timedelta(days=1)
