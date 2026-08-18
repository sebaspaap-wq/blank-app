"""SMTP-driver: verstuurt berichten echt, per e-mail.

De gegevens komen uit ``Settings`` en dus uit environment variables. Ze staan
nergens in code en zijn voor agents onbereikbaar — ``AgentSettings`` kent deze
velden niet.

De driver weigert te bestaan zonder complete configuratie. Dat is bewust: een
half ingevulde mailserver levert anders berichten op die nergens aankomen en
waarvan niemand merkt dat ze weg zijn.
"""

from __future__ import annotations

import logging
from email.message import EmailMessage

from app.config import Settings
from app.kanalen.basis import Kanaalfout, Uitgaand, Verzendfout

logger = logging.getLogger(__name__)


class EmailBerichtdriver:
    naam = "email"

    def __init__(self, instellingen: Settings) -> None:
        ontbreekt = [
            veld
            for veld, waarde in (
                ("WOSZ_SMTP_HOST", instellingen.smtp_host),
                ("WOSZ_AFZENDER_EMAIL", instellingen.afzender_email),
            )
            if not waarde.strip()
        ]
        if ontbreekt:
            raise Kanaalfout(
                "E-mailkanaal is gekozen maar niet compleet ingesteld. "
                f"Ontbreekt: {', '.join(ontbreekt)}."
            )
        self._instellingen = instellingen

    async def verstuur(self, uitgaand: Uitgaand) -> str:
        if not uitgaand.ontvanger.strip():
            raise Verzendfout(
                f"Geen e-mailadres bekend voor {uitgaand.ontvanger_naam or 'ontvanger'}"
            )

        bericht = EmailMessage()
        bericht["From"] = self._afzender()
        bericht["To"] = uitgaand.ontvanger
        bericht["Subject"] = uitgaand.onderwerp
        bericht.set_content(uitgaand.inhoud)

        # Versturen is blokkerend I/O; in een thread zodat de rest van de
        # applicatie ondertussen door kan.
        import asyncio

        try:
            await asyncio.to_thread(self._verstuur_synchroon, bericht)
        except Verzendfout:
            raise
        except Exception as fout:  # noqa: BLE001 — elk SMTP-probleem is hetzelfde probleem
            raise Verzendfout(f"SMTP-fout: {fout}") from fout

        return bericht["Message-ID"] or uitgaand.ontvanger

    def _afzender(self) -> str:
        naam = self._instellingen.afzender_naam.strip()
        adres = self._instellingen.afzender_email.strip()
        return f"{naam} <{adres}>" if naam else adres

    def _verstuur_synchroon(self, bericht: EmailMessage) -> None:
        import smtplib

        s = self._instellingen
        verbinding = (
            smtplib.SMTP_SSL(s.smtp_host, s.smtp_poort, timeout=30)
            if s.smtp_ssl
            else smtplib.SMTP(s.smtp_host, s.smtp_poort, timeout=30)
        )
        with verbinding as server:
            if not s.smtp_ssl and s.smtp_starttls:
                server.starttls()
            if s.smtp_gebruiker.strip():
                server.login(s.smtp_gebruiker, s.smtp_wachtwoord)
            server.send_message(bericht)


__all__ = ["EmailBerichtdriver"]
