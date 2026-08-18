"""Wat een kanaaldriver moet kunnen.

Bewust klein gehouden: een driver krijgt een afgeronde tekst en levert een
verwijzing terug waarmee je later kunt nazoeken wat er is vertrokken. Hij kiest
niet wat er verstuurd wordt, formuleert niets, en kan niets opzoeken in de
database. Dat is de reden dat een verkeerd geconfigureerde driver hoogstens een
bericht niet verstuurt, en nooit het verkeerde bericht.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class Verzendfout(RuntimeError):
    """Het bericht is niet verstuurd.

    De outbox laat het bericht dan op ``klaar`` staan, zodat de volgende ronde
    het opnieuw probeert. Een bericht raakt dus nooit zoek doordat de mailserver
    even niet bereikbaar was.
    """


class Kanaalfout(RuntimeError):
    """De driver is niet bruikbaar met de huidige instellingen."""


@dataclass(frozen=True)
class Uitgaand:
    """Eén te versturen bericht, los van hoe het in de database staat."""

    ontvanger: str
    ontvanger_naam: str
    onderwerp: str
    inhoud: str


@dataclass(frozen=True)
class Post:
    """Eén te publiceren social post."""

    kanaal: str
    haak: str
    tekst: str
    geplande_datum: str


class Berichtdriver(Protocol):
    """Verstuurt een bericht aan één persoon."""

    naam: str

    async def verstuur(self, uitgaand: Uitgaand) -> str:
        """Verstuur en geef een verwijzing terug (message-id, log-regel, ...)."""
        ...


class Socialdriver(Protocol):
    """Publiceert een post op een social kanaal."""

    naam: str

    async def publiceer(self, post: Post) -> str:
        ...


__all__ = [
    "Berichtdriver",
    "Kanaalfout",
    "Post",
    "Socialdriver",
    "Uitgaand",
    "Verzendfout",
]
