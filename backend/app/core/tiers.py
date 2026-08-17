"""Escalatiemotor volgens hoofdstuk 3 van de bouwopdracht.

Drie niveaus, met elk een eigen mechanisme:

tier 1  De agent handelt zelfstandig af. De actie wordt direct uitgevoerd en
        gelogd; er komt geen beslissing in het dashboard.
tier 2  De agent voert uit, tenzij Sebas binnen X uur ingrijpt. Er komt een
        beslissing in het dashboard met een ``deadline_at``. Verstrijkt die
        zonder keuze, dan voert de sweep de standaardoptie alsnog uit.
tier 3  De agent wacht altijd op een expliciete keuze. Er komt een beslissing
        zonder deadline; er gebeurt niets tot Sebas kiest.

Twee ontwerpkeuzes die dit betrouwbaar maken:

1. Wat er moet gebeuren staat als *data* in ``Beslissing.actie`` (een
   uitvoerder-naam plus parameters), niet als vrije tekst. Uitvoeren hangt dus
   niet af van hoe een LLM een zin interpreteert.
2. De sweep die verlopen tier 2-beslissingen uitvoert, filtert hard op
   ``tier == 2``. Een tier 3-beslissing kan langs dit pad nooit vanzelf
   uitgevoerd worden, ook niet als de deadline per ongeluk gevuld zou zijn.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_agent_settings
from app.core.activity import log_activiteit
from app.core.domein import (
    Afdeling,
    BeslissingStatus,
    Tier,
    Urgentie,
    als_aware,
    nu,
)
from app.db.models import Beslissing

#: Een uitvoerder krijgt de sessie, de actieparameters en de beslissing (indien
#: aanwezig) en geeft de logtekst terug die beschrijft wat er is gebeurd.
Uitvoerder = Callable[[AsyncSession, dict[str, Any], Beslissing | None], Awaitable[str]]

_UITVOERDERS: dict[str, Uitvoerder] = {}


class OnbekendeUitvoerderError(RuntimeError):
    """Er is een actie geregistreerd waarvoor geen uitvoerder bestaat."""


def registreer_uitvoerder(naam: str) -> Callable[[Uitvoerder], Uitvoerder]:
    """Decorator om een actie-uitvoerder te registreren."""

    def _wrap(fn: Uitvoerder) -> Uitvoerder:
        _UITVOERDERS[naam] = fn
        return fn

    return _wrap


def uitvoerder_bestaat(naam: str) -> bool:
    return naam in _UITVOERDERS


async def _voer_actie_uit(
    sessie: AsyncSession, actie: dict[str, Any], beslissing: Beslissing | None
) -> str:
    naam = actie.get("uitvoerder", "")
    fn = _UITVOERDERS.get(naam)
    if fn is None:
        raise OnbekendeUitvoerderError(f"Geen uitvoerder geregistreerd onder '{naam}'")
    return await fn(sessie, actie.get("params", {}), beslissing)


@dataclass(slots=True)
class Optie:
    """Eén keuzemogelijkheid zoals de frontend die rendert."""

    naam: str
    gevolg: str
    actie: dict[str, Any] = field(default_factory=dict)

    def als_frontend_dict(self) -> dict[str, str]:
        return {"naam": self.naam, "gevolg": self.gevolg}


@dataclass(slots=True)
class Voorstel:
    """Wat een agent wil doen, plus onder welk tier dat valt.

    Een agent produceert een ``Voorstel``; de tier-engine bepaalt wat ermee
    gebeurt. De agent voert dus nooit zelf iets uit buiten dit pad om.
    """

    afdeling: Afdeling
    tier: Tier
    logtekst: str
    titel: str = ""
    situatie: str = ""
    opties: list[Optie] = field(default_factory=list)
    aanbeveling: str | None = None
    urgentie: Urgentie = Urgentie.DEZE_WEEK
    actie: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.tier is Tier.ZELFSTANDIG:
            if not self.actie:
                raise ValueError("Een tier 1-voorstel moet een uitvoerbare actie hebben.")
        else:
            if not self.titel or not self.situatie:
                raise ValueError("Een tier 2/3-voorstel heeft een titel en situatie nodig.")
            if len(self.opties) < 2:
                raise ValueError("Een beslissing moet minimaal twee opties bieden.")


@dataclass(slots=True)
class Uitkomst:
    """Resultaat van het aanbieden van een voorstel aan de tier-engine."""

    tier: Tier
    uitgevoerd: bool
    beslissing_id: int | None = None
    logtekst: str = ""


async def behandel_voorstel(sessie: AsyncSession, voorstel: Voorstel) -> Uitkomst:
    """Voer een voorstel uit, of leg het aan Sebas voor — afhankelijk van het tier."""
    if voorstel.tier is Tier.ZELFSTANDIG:
        return await _tier1(sessie, voorstel)
    if voorstel.tier is Tier.TENZIJ:
        return await _tier2(sessie, voorstel)
    return await _tier3(sessie, voorstel)


async def _tier1(sessie: AsyncSession, voorstel: Voorstel) -> Uitkomst:
    resultaat = await _voer_actie_uit(sessie, voorstel.actie, None)
    tekst = resultaat or voorstel.logtekst
    await log_activiteit(
        sessie, afdeling=voorstel.afdeling, tekst=tekst, tier=Tier.ZELFSTANDIG
    )
    return Uitkomst(tier=Tier.ZELFSTANDIG, uitgevoerd=True, logtekst=tekst)


async def _tier2(sessie: AsyncSession, voorstel: Voorstel) -> Uitkomst:
    uren = get_agent_settings().tier2_deadline_uren
    beslissing = await _maak_beslissing(
        sessie, voorstel, deadline=nu() + timedelta(hours=uren)
    )
    tekst = f"{voorstel.logtekst} — wordt over {uren} uur uitgevoerd tenzij je ingrijpt"
    await log_activiteit(
        sessie,
        afdeling=voorstel.afdeling,
        tekst=tekst,
        tier=Tier.TENZIJ,
        beslissing_id=beslissing.id,
    )
    return Uitkomst(
        tier=Tier.TENZIJ, uitgevoerd=False, beslissing_id=beslissing.id, logtekst=tekst
    )


async def _tier3(sessie: AsyncSession, voorstel: Voorstel) -> Uitkomst:
    beslissing = await _maak_beslissing(sessie, voorstel, deadline=None)
    tekst = f"{voorstel.logtekst} — wacht op jouw keuze"
    await log_activiteit(
        sessie,
        afdeling=voorstel.afdeling,
        tekst=tekst,
        tier=Tier.WACHT,
        beslissing_id=beslissing.id,
    )
    return Uitkomst(
        tier=Tier.WACHT, uitgevoerd=False, beslissing_id=beslissing.id, logtekst=tekst
    )


async def _maak_beslissing(
    sessie: AsyncSession, voorstel: Voorstel, *, deadline
) -> Beslissing:
    # Valideer vooraf dat elke optie uitvoerbaar is. Beter nu falen dan straks
    # bij het verwerken van Sebas' keuze.
    for optie in voorstel.opties:
        naam = optie.actie.get("uitvoerder")
        if naam and not uitvoerder_bestaat(naam):
            raise OnbekendeUitvoerderError(
                f"Optie '{optie.naam}' verwijst naar onbekende uitvoerder '{naam}'"
            )

    beslissing = Beslissing(
        titel=voorstel.titel,
        situatie=voorstel.situatie,
        opties=[
            {"naam": o.naam, "gevolg": o.gevolg, "actie": o.actie} for o in voorstel.opties
        ],
        urgentie=str(voorstel.urgentie),
        status=str(BeslissingStatus.OPEN),
        afdeling_bron=str(voorstel.afdeling),
        aanbeveling=voorstel.aanbeveling,
        tier=int(voorstel.tier),
        deadline_at=deadline,
        actie=voorstel.actie,
    )
    sessie.add(beslissing)
    await sessie.flush()
    return beslissing


async def verwerk_keuze(
    sessie: AsyncSession, beslissing_id: int, optie_index: int
) -> Beslissing:
    """Verwerk de expliciete keuze van Sebas uit het directiedashboard."""
    beslissing = await sessie.get(Beslissing, beslissing_id)
    if beslissing is None:
        raise LookupError(f"Beslissing {beslissing_id} bestaat niet")
    if beslissing.status != BeslissingStatus.OPEN:
        raise ValueError(f"Beslissing {beslissing_id} is al afgehandeld")
    if not 0 <= optie_index < len(beslissing.opties):
        raise IndexError(f"Optie {optie_index} bestaat niet voor beslissing {beslissing_id}")

    optie = beslissing.opties[optie_index]
    actie = optie.get("actie") or {}

    if actie:
        resultaat = await _voer_actie_uit(sessie, actie, beslissing)
    else:
        resultaat = ""

    beslissing.gekozen_optie = optie["naam"]
    beslissing.status = str(BeslissingStatus.UITGEVOERD)
    beslissing.afgehandeld_op = nu()

    # Deze regel verschijnt in het activiteitenlog van de frontend zonder
    # afdelingslabel — precies zoals resolveDecision() dat nu ook doet.
    await log_activiteit(
        sessie,
        afdeling=Afdeling.DIRECTIE,
        tekst=f'Jouw keuze verwerkt: "{beslissing.titel}" → {optie["naam"]}',
        beslissing_id=beslissing.id,
    )
    if resultaat:
        await log_activiteit(
            sessie,
            afdeling=Afdeling(beslissing.afdeling_bron),
            tekst=resultaat,
            tier=Tier(beslissing.tier),
            beslissing_id=beslissing.id,
        )
    return beslissing


async def sweep_verlopen_tier2(sessie: AsyncSession) -> list[Beslissing]:
    """Voer tier 2-beslissingen uit waarvan de deadline is verstreken.

    Filtert hard op ``tier == 2``. Tier 3 komt hier nooit doorheen: die
    beslissingen hebben geen deadline én worden door deze query uitgesloten.
    """
    resultaat = await sessie.execute(
        select(Beslissing).where(
            Beslissing.status == str(BeslissingStatus.OPEN),
            Beslissing.tier == int(Tier.TENZIJ),
            Beslissing.deadline_at.is_not(None),
        )
    )
    uitgevoerd: list[Beslissing] = []
    moment = nu()

    for beslissing in resultaat.scalars().all():
        deadline = als_aware(beslissing.deadline_at)
        if deadline is None or deadline > moment:
            continue

        standaard = beslissing.opties[0]
        actie = standaard.get("actie") or {}
        tekst = ""
        if actie:
            tekst = await _voer_actie_uit(sessie, actie, beslissing)

        beslissing.gekozen_optie = standaard["naam"]
        beslissing.status = str(BeslissingStatus.VERLOPEN_UITGEVOERD)
        beslissing.afgehandeld_op = moment

        await log_activiteit(
            sessie,
            afdeling=Afdeling(beslissing.afdeling_bron),
            tekst=tekst
            or f'Termijn verstreken zonder ingrijpen: "{beslissing.titel}" → {standaard["naam"]}',
            tier=Tier.TENZIJ,
            beslissing_id=beslissing.id,
        )
        uitgevoerd.append(beslissing)

    return uitgevoerd
