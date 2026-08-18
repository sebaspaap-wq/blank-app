"""De standaarddriver: schrijft naar het log en verstuurt niets.

Dit is met opzet de standaard. Wie het systeem voor het eerst start, of eraan
ontwikkelt, wil dat alles werkt — inclusief de automatische opvolging die uit
zichzelf berichten produceert — zonder dat er iets bij een echte medewerker
aankomt. Een kanaal aanzetten is een bewuste handeling, geen vergeten instelling.
"""

from __future__ import annotations

import logging

from app.kanalen.basis import Post, Uitgaand

logger = logging.getLogger(__name__)


class ConsoleBerichtdriver:
    naam = "console"

    async def verstuur(self, uitgaand: Uitgaand) -> str:
        logger.info(
            "[niet verstuurd — console] aan %s <%s>: %s\n%s",
            uitgaand.ontvanger_naam or "onbekend",
            uitgaand.ontvanger or "geen adres",
            uitgaand.onderwerp,
            uitgaand.inhoud,
        )
        return "console"


class ConsoleSocialdriver:
    naam = "console"

    async def publiceer(self, post: Post) -> str:
        logger.info(
            "[niet gepubliceerd — console] %s op %s: %s\n%s",
            post.kanaal,
            post.geplande_datum,
            post.haak,
            post.tekst,
        )
        return "console"


__all__ = ["ConsoleBerichtdriver", "ConsoleSocialdriver"]
