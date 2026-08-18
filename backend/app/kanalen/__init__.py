"""De outbox legen: berichten versturen en posts publiceren.

Zie README.md in deze map voor waarom dit buiten de agents staat.
"""

from __future__ import annotations

import logging
from collections.abc import Callable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.core.activity import log_activiteit
from app.core.domein import Afdeling, BerichtStatus, ContentStatus, Kanaal, Tier, nu
from app.db.models import Bericht, Contentitem, Hoek, User
from app.kanalen.basis import (
    Berichtdriver,
    Kanaalfout,
    Post,
    Socialdriver,
    Uitgaand,
    Verzendfout,
)
from app.kanalen.console import ConsoleBerichtdriver, ConsoleSocialdriver
from app.kanalen.email import EmailBerichtdriver

logger = logging.getLogger(__name__)

#: Welke driver hoort bij welke instelling. Een kanaal aansluiten is een regel
#: hier plus een klasse; aan de agents verandert er niets.
BERICHTDRIVERS: dict[str, Callable[[Settings], Berichtdriver]] = {
    "console": lambda _: ConsoleBerichtdriver(),
    "email": EmailBerichtdriver,
}

SOCIALDRIVERS: dict[str, Callable[[Settings], Socialdriver]] = {
    "console": lambda _: ConsoleSocialdriver(),
}


def kies_berichtdriver(instellingen: Settings | None = None) -> Berichtdriver:
    instellingen = instellingen or get_settings()
    maak = BERICHTDRIVERS.get(instellingen.bericht_driver)
    if maak is None:
        raise Kanaalfout(
            f"Onbekend berichtkanaal '{instellingen.bericht_driver}'. "
            f"Kies uit: {', '.join(sorted(BERICHTDRIVERS))}."
        )
    return maak(instellingen)


def kies_socialdriver(instellingen: Settings | None = None) -> Socialdriver:
    instellingen = instellingen or get_settings()
    maak = SOCIALDRIVERS.get(instellingen.social_driver)
    if maak is None:
        raise Kanaalfout(
            f"Onbekend social kanaal '{instellingen.social_driver}'. "
            f"Kies uit: {', '.join(sorted(SOCIALDRIVERS))}."
        )
    return maak(instellingen)


# ---------------------------------------------------------------------------
# Berichten
# ---------------------------------------------------------------------------


async def verstuur_outbox(
    sessie: AsyncSession, *, driver: Berichtdriver | None = None, maximum: int = 50
) -> dict[str, int]:
    """Verstuur alles wat klaarstaat.

    Een bericht dat niet verstuurd kan worden, blijft op ``klaar`` staan. De
    volgende ronde probeert het opnieuw — een mailserver die even plat ligt mag
    geen bericht kosten. Alleen als er structureel iets mis is (geen adres),
    blijft het staan en zie je dat terug in het log.
    """
    driver = driver or kies_berichtdriver()

    resultaat = await sessie.execute(
        select(Bericht)
        .where(Bericht.status == str(BerichtStatus.KLAAR))
        .order_by(Bericht.id)
        .limit(maximum)
    )
    berichten = list(resultaat.scalars().all())

    verstuurd = 0
    mislukt = 0
    for bericht in berichten:
        adres = await _adres(sessie, bericht)
        try:
            await driver.verstuur(
                Uitgaand(
                    ontvanger=adres,
                    ontvanger_naam=bericht.ontvanger_naam,
                    onderwerp=bericht.onderwerp,
                    inhoud=bericht.inhoud,
                )
            )
        except Verzendfout as fout:
            mislukt += 1
            logger.warning(
                "Bericht %s aan %s niet verstuurd: %s",
                bericht.id,
                bericht.ontvanger_naam or adres,
                fout,
            )
            continue

        bericht.status = str(BerichtStatus.VERSTUURD)
        bericht.verstuurd_op = nu()
        verstuurd += 1

    if verstuurd:
        await log_activiteit(
            sessie,
            afdeling=Afdeling.SUPPORT,
            tekst=f"{verstuurd} bericht(en) verstuurd via {driver.naam}",
            tier=Tier.ZELFSTANDIG,
        )

    return {"verstuurd": verstuurd, "mislukt": mislukt}


async def _adres(sessie: AsyncSession, bericht: Bericht) -> str:
    """Waar het bericht naartoe moet.

    Sjablonen kiezen een kanaal (WhatsApp of e-mail), maar er is nog geen
    WhatsApp-koppeling. Zolang die er niet is, gaat alles naar het e-mailadres
    van de ontvanger — beter op één werkende manier bezorgd dan op een tweede
    manier die niet bestaat.
    """
    if bericht.ontvanger_user_id is None:
        return ""
    gebruiker = await sessie.get(User, bericht.ontvanger_user_id)
    if gebruiker is None:
        return ""
    if bericht.kanaal == str(Kanaal.EMAIL):
        return gebruiker.email or ""
    return gebruiker.email or gebruiker.telefoon or ""


# ---------------------------------------------------------------------------
# Social posts
# ---------------------------------------------------------------------------


async def publiceer_geplande_posts(
    sessie: AsyncSession,
    *,
    driver: Socialdriver | None = None,
    tot_en_met: object | None = None,
) -> list[str]:
    """Publiceer content waarvan de geplande datum is aangebroken.

    Alleen items met status ``gepland``. Een item dat nog als ``voorstel``
    klaarstaat wacht op de keuze van Sebas; die staat als beslissing in het
    dashboard. Publiceren is onomkeerbaar, dus dat onderscheid is het hele punt.
    """
    from datetime import date

    driver = driver or kies_socialdriver()
    grens = tot_en_met or date.today()

    resultaat = await sessie.execute(
        select(Contentitem)
        .where(
            Contentitem.status == str(ContentStatus.GEPLAND),
            Contentitem.geplande_datum <= grens,
        )
        .order_by(Contentitem.geplande_datum, Contentitem.id)
    )

    gepubliceerd: list[str] = []
    for item in resultaat.scalars().all():
        hoek = await sessie.get(Hoek, item.hoek_id)
        try:
            await driver.publiceer(
                Post(
                    kanaal=item.kanaal,
                    haak=item.haak,
                    tekst=item.concepttekst,
                    geplande_datum=item.geplande_datum.isoformat(),
                )
            )
        except Verzendfout as fout:
            logger.warning("Post %s niet gepubliceerd: %s", item.id, fout)
            continue

        item.status = str(ContentStatus.GEPUBLICEERD)
        item.gepubliceerd_op = nu()
        gepubliceerd.append(item.haak)

        await log_activiteit(
            sessie,
            afdeling=Afdeling.MARKETING,
            tekst=(
                f"Post gepubliceerd op {item.kanaal}"
                + (f" ({hoek.naam})" if hoek else "")
                + f": {item.haak}"
            ),
            tier=Tier.ZELFSTANDIG,
        )

    return gepubliceerd


__all__ = [
    "BERICHTDRIVERS",
    "SOCIALDRIVERS",
    "Kanaalfout",
    "Verzendfout",
    "kies_berichtdriver",
    "kies_socialdriver",
    "publiceer_geplande_posts",
    "verstuur_outbox",
]
