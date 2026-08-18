"""Domeinbegrippen die door alle lagen heen gedeeld worden."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import IntEnum, StrEnum


def nu() -> datetime:
    """Huidig tijdstip, altijd timezone-aware in UTC."""
    return datetime.now(timezone.utc)


def als_aware(waarde: datetime | None) -> datetime | None:
    """Maak een datetime timezone-aware.

    SQLite geeft naive datetimes terug waar PostgreSQL aware datetimes geeft.
    Deze helper zorgt dat vergelijkingen (bijv. tier 2-deadlines) op beide
    databases identiek werken.
    """
    if waarde is None:
        return None
    if waarde.tzinfo is None:
        return waarde.replace(tzinfo=timezone.utc)
    return waarde


class Afdeling(StrEnum):
    """De vier afdelingsagents plus de coordinerende directielaag.

    De vier eerste waarden komen exact overeen met de sleutels van ``DEPT_LABEL``
    in wosz-app.html, zodat de frontend ze zonder vertaalslag kan tonen.
    """

    MARKETING = "marketing"
    MATCHING = "matching"
    SUPPORT = "support"
    FINANCIEEL = "financieel"
    DIRECTIE = "directie"


#: Afdelingen die de frontend als filterbare feed toont.
AFDELINGSAGENTS: tuple[Afdeling, ...] = (
    Afdeling.MARKETING,
    Afdeling.MATCHING,
    Afdeling.SUPPORT,
    Afdeling.FINANCIEEL,
)


class Tier(IntEnum):
    """Escalatieniveau volgens hoofdstuk 3 van de bouwopdracht.

    ZELFSTANDIG  tier 1 — de agent handelt zelf af.
    TENZIJ       tier 2 — de agent voert uit, tenzij Sebas binnen X uur ingrijpt.
    WACHT        tier 3 — de agent doet niets tot Sebas expliciet kiest.
    """

    ZELFSTANDIG = 1
    TENZIJ = 2
    WACHT = 3


class Urgentie(StrEnum):
    """Urgentielabel zoals de frontend het rendert (``decision-badge``)."""

    DRINGEND = "dringend"
    DEZE_WEEK = "deze-week"


class BeslissingStatus(StrEnum):
    OPEN = "open"
    UITGEVOERD = "uitgevoerd"
    AFGEWEZEN = "afgewezen"
    VERLOPEN_UITGEVOERD = "verlopen-uitgevoerd"


class ShiftStatus(StrEnum):
    OPEN = "open"
    DEELS_GEMATCHT = "deels-gematcht"
    GEMATCHT = "gematcht"
    GEANNULEERD = "geannuleerd"


class MatchStatus(StrEnum):
    VOORGESTELD = "voorgesteld"
    BEVESTIGD = "bevestigd"
    GEWERKT = "gewerkt"
    NO_SHOW = "no-show"
    GEANNULEERD = "geannuleerd"


class ReactieStatus(StrEnum):
    """Wat er met een zelf geplaatste reactie op een shift is gebeurd."""

    OPEN = "open"
    GEHONOREERD = "gehonoreerd"
    VERVALLEN = "vervallen"
    INGETROKKEN = "ingetrokken"


class EventStatus(StrEnum):
    PENDING = "pending"
    VERWERKT = "verwerkt"
    MISLUKT = "mislukt"


class Kanaal(StrEnum):
    """Kanalen waarlangs Support berichten verstuurt."""

    WHATSAPP = "whatsapp"
    EMAIL = "email"


class BerichtStatus(StrEnum):
    """Status van een uitgaand bericht.

    In Fase 2 is er nog geen WhatsApp- of e-mailkoppeling. Berichten worden
    gerenderd en als ``KLAAR`` in de outbox gezet, zodat Sebas de teksten kan
    beoordelen voordat er ooit iets echt de deur uitgaat. Het aansluiten van een
    kanaal is dan alleen nog het invullen van de verzendstap.
    """

    KLAAR = "klaar"
    VERSTUURD = "verstuurd"
    GEANNULEERD = "geannuleerd"


class SocialKanaal(StrEnum):
    """Kanalen waarop Marketing content plant."""

    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    FACEBOOK = "facebook"


class ContentStatus(StrEnum):
    """Status van een item op de content-kalender.

    Let op wat hier ontbreekt: er is geen status die het systeem zelf zet nadat
    het iets heeft gepubliceerd. Publiceren gebeurt buiten dit systeem om.
    ``GEPUBLICEERD`` legt achteraf vast dat Sebas het heeft geplaatst.
    """

    VOORSTEL = "voorstel"
    GEPLAND = "gepland"
    GEPUBLICEERD = "gepubliceerd"
    AFGEWEZEN = "afgewezen"


class CampagneStatus(StrEnum):
    ACTIEF = "actief"
    GEPAUZEERD = "gepauzeerd"
    CONCEPT = "concept"


class BudgetmutatieStatus(StrEnum):
    """Status van een voorgestelde budgetwijziging.

    Net als bij uitbetalingen kan het systeem dit niet zelf doorvoeren: er is
    geen Meta Ads-koppeling. ``KLAAR_VOOR_UITVOERING`` betekent dat Sebas de
    wijziging zelf in Ads Manager doorvoert; ``DOORGEVOERD`` legt vast dat hij
    dat gedaan heeft.
    """

    KLAAR_VOOR_UITVOERING = "klaar-voor-uitvoering"
    DOORGEVOERD = "doorgevoerd"
    GEANNULEERD = "geannuleerd"


class VraagUitkomst(StrEnum):
    """Hoe de Support-agent een binnengekomen vraag heeft afgehandeld."""

    BEANTWOORD = "beantwoord"
    GEESCALEERD = "geescaleerd"


class UitbetalingStatus(StrEnum):
    """Statussen van een uitbetalingsopdracht.

    Let op wat hier ontbreekt: er is geen status "betaald door het systeem".
    Het systeem kan geen geld verplaatsen. ``KLAAR_VOOR_EXPORT`` betekent dat
    Sebas het bedrag zelf bij de bank overmaakt; ``HANDMATIG_VOLDAAN`` legt
    achteraf vast dat hij dat gedaan heeft.
    """

    CONCEPT = "concept"
    KLAAR_VOOR_EXPORT = "klaar-voor-export"
    GEEXPORTEERD = "geexporteerd"
    HANDMATIG_VOLDAAN = "handmatig-voldaan"
    GEANNULEERD = "geannuleerd"


#: Levelsysteem — drempels en bonussen exact zoals wosz-app.html ze toont.
LEVELS: tuple[dict, ...] = (
    {"level": 1, "naam": "Beach Starter", "vanaf": 0, "bonus": 0, "icon": "\U0001f3d6️"},
    {"level": 2, "naam": "Shift Regular", "vanaf": 25, "bonus": 10, "icon": "⭐"},
    {"level": 3, "naam": "Vaste Kracht", "vanaf": 60, "bonus": 20, "icon": "\U0001f525"},
    {"level": 4, "naam": "Kern van het Team", "vanaf": 120, "bonus": 35, "icon": "\U0001f4aa"},
    {"level": 5, "naam": "WOSZ Legend", "vanaf": 200, "bonus": 50, "icon": "\U0001f451"},
    {"level": 6, "naam": "Seizoenslegende", "vanaf": 300, "bonus": 75, "icon": "\U0001f3c6"},
)


def level_voor_uren(seizoen_uren: float) -> dict:
    """Bepaal het level dat hoort bij het aantal gewerkte seizoensuren."""
    huidig = LEVELS[0]
    for lv in LEVELS:
        if seizoen_uren >= lv["vanaf"]:
            huidig = lv
    return huidig
