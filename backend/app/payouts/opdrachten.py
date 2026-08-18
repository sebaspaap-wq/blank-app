"""Beheer van uitbetalingsopdrachten.

Wat deze module doet: een goedgekeurde uitbetaling vastleggen, exporteren naar
een CSV die Sebas meeneemt naar zijn bank, en achteraf registreren dat hij is
voldaan.

Wat deze module niet doet, en ook niet kán: betalen. Er is geen betaal-API in
dit systeem. Zie README.md in deze map.
"""

from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.activity import log_activiteit
from app.core.domein import Afdeling, Tier, UitbetalingStatus, nu
from app.core.tiers import registreer_uitvoerder
from app.db.models import Beslissing, Referral, Uitbetalingsopdracht


@registreer_uitvoerder("directie.keur_uitbetaling_goed")
async def keur_uitbetaling_goed(
    sessie: AsyncSession, params: dict[str, Any], beslissing: Beslissing | None
) -> str:
    """Zet een uitbetaling klaar voor handmatige uitvoering door Sebas.

    Dit is de uitvoerder achter de knop "Goedkeuren" in het directiedashboard.
    Hij verplaatst geen geld: hij zet de status op ``klaar-voor-export``, zodat
    het bedrag in de eerstvolgende export terechtkomt.

    Deze uitvoerder is met opzet geregistreerd vanuit ``app.payouts`` en niet
    vanuit een agent. De afhankelijkheid wijst dus van uitbetalingen naar de
    tier-engine, nooit andersom — daardoor kan een agent hier niet bij.
    """
    opdracht_id = params.get("uitbetaling_id")
    if opdracht_id is not None:
        opdracht = await sessie.get(Uitbetalingsopdracht, int(opdracht_id))
        if opdracht is None:
            raise LookupError(f"Uitbetalingsopdracht {opdracht_id} bestaat niet")
    else:
        opdracht = Uitbetalingsopdracht(
            soort=params.get("soort", "bonus"),
            begunstigde_naam=params["begunstigde_naam"],
            begunstigde_user_id=params.get("begunstigde_user_id"),
            bedrag_cent=int(params["bedrag_cent"]),
            omschrijving=params.get("omschrijving", ""),
            beslissing_id=beslissing.id if beslissing else None,
        )
        sessie.add(opdracht)

    opdracht.status = str(UitbetalingStatus.KLAAR_VOOR_EXPORT)
    opdracht.goedgekeurd_op = nu()
    await sessie.flush()

    bedrag = opdracht.bedrag_cent / 100
    return (
        f"Uitbetaling van €{bedrag:.2f} aan {opdracht.begunstigde_naam} goedgekeurd en "
        "klaargezet voor handmatige overboeking"
    )


@registreer_uitvoerder("directie.wijs_uitbetaling_af")
async def wijs_uitbetaling_af(
    sessie: AsyncSession, params: dict[str, Any], _beslissing: Beslissing | None
) -> str:
    opdracht_id = params.get("uitbetaling_id")
    if opdracht_id is None:
        return str(params.get("reden", "Uitbetaling afgewezen"))
    opdracht = await sessie.get(Uitbetalingsopdracht, int(opdracht_id))
    if opdracht is None:
        raise LookupError(f"Uitbetalingsopdracht {opdracht_id} bestaat niet")
    opdracht.status = str(UitbetalingStatus.GEANNULEERD)
    bedrag = opdracht.bedrag_cent / 100
    return f"Uitbetaling van €{bedrag:.2f} aan {opdracht.begunstigde_naam} afgewezen"


async def openstaande_opdrachten(sessie: AsyncSession) -> list[Uitbetalingsopdracht]:
    """Alle door Sebas goedgekeurde uitbetalingen die nog uitgevoerd moeten worden."""
    resultaat = await sessie.execute(
        select(Uitbetalingsopdracht)
        .where(Uitbetalingsopdracht.status == str(UitbetalingStatus.KLAAR_VOOR_EXPORT))
        .order_by(Uitbetalingsopdracht.goedgekeurd_op)
    )
    return list(resultaat.scalars().all())


def _naar_csv(opdrachten: list[Uitbetalingsopdracht]) -> str:
    buffer = io.StringIO()
    schrijver = csv.writer(buffer, delimiter=";")
    schrijver.writerow(["id", "begunstigde", "bedrag_eur", "omschrijving", "goedgekeurd_op"])
    for o in opdrachten:
        schrijver.writerow(
            [
                o.id,
                o.begunstigde_naam,
                f"{o.bedrag_cent / 100:.2f}",
                o.omschrijving,
                o.goedgekeurd_op.isoformat() if o.goedgekeurd_op else "",
            ]
        )
    return buffer.getvalue()


async def exporteer_openstaande_opdrachten(sessie: AsyncSession) -> tuple[str, int]:
    """Maak een CSV van alle goedgekeurde uitbetalingen.

    Geeft ``(csv_inhoud, aantal)`` terug. Sebas voert de betalingen zelf uit bij
    zijn bank; dit bestand is niets meer dan zijn werklijst. Het bestand bevat
    daarom ook geen rekeningnummers — die staan in Sebas' eigen administratie,
    niet in dit systeem (AVG-dataminimalisatie).
    """
    opdrachten = await openstaande_opdrachten(sessie)
    inhoud = _naar_csv(opdrachten)

    if opdrachten:
        map_pad = Path(get_settings().uitbetaling_export_map)
        map_pad.mkdir(parents=True, exist_ok=True)
        bestand = map_pad / f"uitbetalingen-{nu():%Y%m%d-%H%M%S}.csv"
        bestand.write_text(inhoud, encoding="utf-8")

        moment = nu()
        for o in opdrachten:
            o.status = str(UitbetalingStatus.GEEXPORTEERD)
            o.geexporteerd_op = moment

        await log_activiteit(
            sessie,
            afdeling=Afdeling.FINANCIEEL,
            tekst=(
                f"{len(opdrachten)} goedgekeurde uitbetaling(en) geëxporteerd voor "
                "handmatige overboeking"
            ),
            tier=Tier.WACHT,
        )

    return inhoud, len(opdrachten)


async def markeer_handmatig_voldaan(
    sessie: AsyncSession, opdracht_id: int
) -> Uitbetalingsopdracht:
    """Leg vast dat Sebas de betaling daadwerkelijk heeft gedaan."""
    opdracht = await sessie.get(Uitbetalingsopdracht, opdracht_id)
    if opdracht is None:
        raise LookupError(f"Uitbetalingsopdracht {opdracht_id} bestaat niet")

    opdracht.status = str(UitbetalingStatus.HANDMATIG_VOLDAAN)
    opdracht.handmatig_voldaan_op = nu()

    # Was dit een vriendenbonus, dan is de referral hiermee afgerond. Zonder deze
    # stap blijft hij eeuwig op "ter-goedkeuring" staan en ziet de aanbrenger in
    # de app nooit dat zijn bonus binnen is.
    if opdracht.soort == "vriendenbonus" and opdracht.begunstigde_user_id is not None:
        openstaand = await sessie.execute(
            select(Referral).where(
                Referral.medewerker_id == opdracht.begunstigde_user_id,
                Referral.bonus_status == "ter-goedkeuring",
            )
        )
        for referral in openstaand.scalars().all():
            referral.bonus_status = "uitbetaald"

    bedrag = opdracht.bedrag_cent / 100
    await log_activiteit(
        sessie,
        afdeling=Afdeling.FINANCIEEL,
        tekst=(
            f"Uitbetaling van €{bedrag:.2f} aan {opdracht.begunstigde_naam} door Sebas "
            "handmatig voldaan"
        ),
        tier=Tier.WACHT,
    )
    return opdracht
