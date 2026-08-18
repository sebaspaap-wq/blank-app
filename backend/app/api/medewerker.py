"""Endpoints voor het medewerkerscherm van wosz-app.html.

Deze routes vervangen de hardcoded arrays in de frontend:

``beschikbaar``      -> GET  /api/medewerker/{id}/shifts/beschikbaar
``mijnAankomend``    -> GET  /api/medewerker/{id}/shifts/mijn  (aankomend)
``mijnGeschiedenis`` -> GET  /api/medewerker/{id}/shifts/mijn  (geschiedenis)
``vrienden``         -> GET  /api/medewerker/{id}/vrienden
``seizoenUren``      -> zit in GET /api/medewerker/{id}
``reageerShift()``   -> POST /api/medewerker/{id}/shifts/{shift_id}/reageer
``annuleerShift()``  -> POST /api/medewerker/{id}/matches/{match_id}/annuleer
``submitInvite()``   -> POST /api/medewerker/{id}/vrienden

Eén principe loopt door alle schrijfacties heen: de app schrijft nooit
rechtstreeks een match. Reageren legt een *reactie* vast, en daarna draait de
Matching-agent. Zo blijft de levelprioriteit gelden — anders zou wie het snelst
klikt altijd winnen, en dat is precies de belofte die het levelsysteem doet.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.matching import MatchingAgent
from app.agents.support import SupportAgent
from app.api.schemas import (
    AanmeldingIn,
    MedewerkerUit,
    MijnShiftsUit,
    MijnShiftUit,
    ProfielIn,
    ProfielUit,
    ShiftUit,
    UrenIn,
    VriendIn,
    VriendUit,
)
from app.api.weergave import korte_datum, uurloon_tekst
from app.config import get_settings
from app.core.domein import MatchStatus, ReactieStatus, ShiftStatus
from app.core.events import verwerk_pending
from app.db.models import Bedrijf, Level, Match, Reactie, Referral, Shift, User
from app.db.session import get_sessie

router = APIRouter(prefix="/api/medewerker", tags=["medewerker"])

#: Weekdagafkortingen zoals ze in ``User.beschikbare_dagen`` staan.
DAGEN = ("ma", "di", "wo", "do", "vr", "za", "zo")

#: Hoe de statussen van een referral in de app heten.
VRIEND_STATUS = {
    "bezig": "Bezig",
    "ter-goedkeuring": "Wacht op uitbetaling",
    "uitbetaald": "Uitbetaald",
}


async def _verwerk_events(sessie: AsyncSession) -> None:
    """Handel de events af die deze actie zojuist heeft opgeleverd.

    In productie doet de achtergrondworker dit binnen enkele seconden; hier
    draaien we hem meteen mee zodat het antwoord aan de app al klopt.
    """
    await verwerk_pending(sessie, get_settings().event_max_pogingen)


async def _haal_medewerker(sessie: AsyncSession, medewerker_id: int) -> User:
    gebruiker = await sessie.get(User, medewerker_id)
    if gebruiker is None or gebruiker.rol != "medewerker":
        raise HTTPException(status_code=404, detail="Medewerker bestaat niet")
    return gebruiker


# ---------------------------------------------------------------------------
# Aanmelden
# ---------------------------------------------------------------------------


@router.post("/aanmelden", response_model=MedewerkerUit, status_code=201)
async def meld_aan(
    invoer: AanmeldingIn, sessie: AsyncSession = Depends(get_sessie)
) -> MedewerkerUit:
    """Nieuwe medewerker in het systeem, inclusief automatische onboarding.

    Het welkomstbericht is geen losse stap die iemand nog moet aanzetten: het
    hoort bij aanmelden. Support verstuurt het als tier 1-actie, dus het komt
    ook in het activiteitenlog terecht.
    """
    bestaand = await _zoek_op_email(sessie, invoer.email)
    if bestaand is not None:
        raise HTTPException(
            status_code=409, detail=f"{invoer.email} is al aangemeld als medewerker"
        )

    gebruiker = User(
        naam=invoer.naam.strip(),
        rol="medewerker",
        email=invoer.email,
        telefoon=invoer.telefoon,
        functies=[f.lower() for f in invoer.functies],
        beschikbare_dagen=[d.lower() for d in invoer.beschikbare_dagen],
        ervaring_jaren=invoer.ervaring_jaren,
        gewenst_uurloon=invoer.gewenst_uurloon,
        actief=True,
    )
    sessie.add(gebruiker)
    await sessie.flush()
    sessie.add(Level(medewerker_id=gebruiker.id, huidig_level=1, seizoen_uren=0.0))
    await sessie.flush()

    # Was deze persoon eerder uitgenodigd door een vriend? Dan wordt de
    # uitnodiging nu een echte referral in plaats van een tweede account.
    await _koppel_uitnodiging(sessie, gebruiker)

    await SupportAgent().verstuur_onboarding(sessie, gebruiker.id)
    await _verwerk_events(sessie)
    await sessie.commit()
    return await _scherm(sessie, gebruiker)


async def _zoek_op_email(sessie: AsyncSession, email: str | None) -> User | None:
    if not email:
        return None
    resultaat = await sessie.execute(
        select(User).where(User.email == email, User.rol == "medewerker", User.actief.is_(True))
    )
    return resultaat.scalars().first()


async def _koppel_uitnodiging(sessie: AsyncSession, nieuw: User) -> None:
    """Zet een openstaande uitnodiging om in een aanmelding van dezelfde persoon.

    Een uitnodiging maakt een inactief account aan zodat de vriendenbonus ergens
    aan kan hangen. Meldt die persoon zich later echt aan, dan moet de referral
    naar het nieuwe account wijzen; anders loopt de bonus mee met een account dat
    nooit uren maakt.
    """
    if not nieuw.email:
        return
    resultaat = await sessie.execute(
        select(User).where(
            User.email == nieuw.email,
            User.rol == "medewerker",
            User.actief.is_(False),
            User.id != nieuw.id,
        )
    )
    for uitgenodigd in resultaat.scalars().all():
        referrals = await sessie.execute(
            select(Referral).where(Referral.vriend_id == uitgenodigd.id)
        )
        for referral in referrals.scalars().all():
            referral.vriend_id = nieuw.id
        await sessie.delete(uitgenodigd)


# ---------------------------------------------------------------------------
# Lezen
# ---------------------------------------------------------------------------


@router.get("/{medewerker_id}", response_model=MedewerkerUit)
async def lees_scherm(
    medewerker_id: int, sessie: AsyncSession = Depends(get_sessie)
) -> MedewerkerUit:
    """Alles wat het medewerkerscherm nodig heeft, in één aanroep."""
    gebruiker = await _haal_medewerker(sessie, medewerker_id)
    return await _scherm(sessie, gebruiker)


@router.get("/{medewerker_id}/shifts/beschikbaar", response_model=list[ShiftUit])
async def lees_beschikbaar(
    medewerker_id: int, sessie: AsyncSession = Depends(get_sessie)
) -> list[ShiftUit]:
    gebruiker = await _haal_medewerker(sessie, medewerker_id)
    return await _beschikbare_shifts(sessie, gebruiker)


@router.get("/{medewerker_id}/shifts/mijn", response_model=MijnShiftsUit)
async def lees_mijn_shifts(
    medewerker_id: int, sessie: AsyncSession = Depends(get_sessie)
) -> MijnShiftsUit:
    gebruiker = await _haal_medewerker(sessie, medewerker_id)
    aankomend, geschiedenis = await _mijn_shifts(sessie, gebruiker)
    return MijnShiftsUit(aankomend=aankomend, geschiedenis=geschiedenis)


@router.get("/{medewerker_id}/vrienden", response_model=list[VriendUit])
async def lees_vrienden(
    medewerker_id: int, sessie: AsyncSession = Depends(get_sessie)
) -> list[VriendUit]:
    gebruiker = await _haal_medewerker(sessie, medewerker_id)
    return await _vrienden(sessie, gebruiker)


# ---------------------------------------------------------------------------
# Schrijven
# ---------------------------------------------------------------------------


@router.post("/{medewerker_id}/shifts/{shift_id}/reageer", response_model=MedewerkerUit)
async def reageer_op_shift(
    medewerker_id: int, shift_id: int, sessie: AsyncSession = Depends(get_sessie)
) -> MedewerkerUit:
    """Reageer op een shift; de Matching-agent beslist meteen daarna.

    De reactie is geen toezegging. Hij zet de medewerker vooraan in de rij voor
    deze ene shift; binnen die groep wint nog steeds wie de meeste seizoensuren
    heeft. Daarom draait de agent hier direct, zodat de medewerker in hetzelfde
    antwoord ziet of hij de shift heeft.
    """
    gebruiker = await _haal_medewerker(sessie, medewerker_id)
    if gebruiker.geschorst:
        raise HTTPException(
            status_code=409,
            detail="Je kunt op dit moment niet op shifts reageren. Neem contact op met WOSZ.",
        )

    shift = await sessie.get(Shift, shift_id)
    if shift is None:
        raise HTTPException(status_code=404, detail="Shift bestaat niet")
    if shift.status in {str(ShiftStatus.GEMATCHT), str(ShiftStatus.GEANNULEERD)}:
        raise HTTPException(status_code=409, detail="Deze shift is niet meer open")

    bestaand = await sessie.execute(
        select(Reactie).where(
            Reactie.shift_id == shift_id,
            Reactie.medewerker_id == medewerker_id,
            Reactie.status == str(ReactieStatus.OPEN),
        )
    )
    if bestaand.scalars().first() is None:
        sessie.add(Reactie(shift_id=shift_id, medewerker_id=medewerker_id))
        await sessie.flush()

    await MatchingAgent().match_shift(sessie, shift)
    await _verwerk_events(sessie)
    await sessie.commit()
    return await _scherm(sessie, gebruiker)


@router.post("/{medewerker_id}/matches/{match_id}/annuleer", response_model=MedewerkerUit)
async def annuleer_shift(
    medewerker_id: int, match_id: int, sessie: AsyncSession = Depends(get_sessie)
) -> MedewerkerUit:
    """Zeg een ingeplande shift af.

    De plek komt daarmee weer vrij, dus de agent probeert hem meteen opnieuw te
    vullen. Doet hij dat niet, dan zou een afzegging stil blijven liggen tot de
    volgende matchronde — en bij een shift van morgen is dat te laat.
    """
    gebruiker = await _haal_medewerker(sessie, medewerker_id)
    match = await sessie.get(Match, match_id)
    if match is None or match.medewerker_id != medewerker_id:
        raise HTTPException(status_code=404, detail="Shift staat niet op jouw naam")
    if match.status not in {str(MatchStatus.VOORGESTELD), str(MatchStatus.BEVESTIGD)}:
        raise HTTPException(status_code=409, detail="Deze shift kun je niet meer annuleren")

    match.status = str(MatchStatus.GEANNULEERD)
    await sessie.flush()

    shift = await sessie.get(Shift, match.shift_id)
    if shift is not None:
        # De eigen reactie vervalt, anders krijgt wie net afzegde de plek terug.
        eigen = await sessie.execute(
            select(Reactie).where(
                Reactie.shift_id == shift.id, Reactie.medewerker_id == medewerker_id
            )
        )
        for reactie in eigen.scalars().all():
            reactie.status = str(ReactieStatus.VERVALLEN)
        await sessie.flush()
        await MatchingAgent().match_shift(sessie, shift)

    await _verwerk_events(sessie)
    await sessie.commit()
    return await _scherm(sessie, gebruiker)


@router.post("/{medewerker_id}/matches/{match_id}/uren")
async def geef_uren_door(
    medewerker_id: int,
    match_id: int,
    invoer: UrenIn,
    sessie: AsyncSession = Depends(get_sessie),
) -> dict[str, Any]:
    """Geef door hoeveel uur je hebt gewerkt.

    Dit is hetzelfde pad als ``/api/matching/matches/{id}/uren``, maar dan met de
    controle dat de match ook echt van deze medewerker is.
    """
    await _haal_medewerker(sessie, medewerker_id)
    match = await sessie.get(Match, match_id)
    if match is None or match.medewerker_id != medewerker_id:
        raise HTTPException(status_code=404, detail="Shift staat niet op jouw naam")

    try:
        resultaat = await MatchingAgent().registreer_gewerkte_uren(
            sessie, match_id, invoer.uren
        )
    except LookupError as fout:
        raise HTTPException(status_code=404, detail=str(fout)) from fout
    await _verwerk_events(sessie)
    await sessie.commit()
    return resultaat


@router.post("/{medewerker_id}/profiel", response_model=MedewerkerUit)
async def bewaar_profiel(
    medewerker_id: int, invoer: ProfielIn, sessie: AsyncSession = Depends(get_sessie)
) -> MedewerkerUit:
    """Werk het eigen profiel bij.

    Functies en beschikbare dagen zijn geen cosmetica: de Matching-agent
    gebruikt ze als harde criteria. Wie hier een functie uitvinkt, verdwijnt
    daarmee uit de kandidatenlijst voor dat soort shifts.
    """
    gebruiker = await _haal_medewerker(sessie, medewerker_id)

    onbekende_dagen = {d.lower() for d in invoer.beschikbare_dagen} - set(DAGEN)
    if onbekende_dagen:
        raise HTTPException(
            status_code=422,
            detail=f"Onbekende dag(en): {', '.join(sorted(onbekende_dagen))}",
        )

    gebruiker.naam = invoer.naam.strip()
    gebruiker.email = invoer.email or None
    gebruiker.telefoon = invoer.telefoon or None
    gebruiker.woonplaats = invoer.woonplaats or None
    gebruiker.gewenst_uurloon = invoer.gewenst_uurloon or None
    gebruiker.functies = [f.lower() for f in invoer.functies]
    gebruiker.beschikbare_dagen = [d.lower() for d in invoer.beschikbare_dagen]
    await sessie.commit()
    return await _scherm(sessie, gebruiker)


@router.post("/{medewerker_id}/vrienden", response_model=list[VriendUit], status_code=201)
async def nodig_vriend_uit(
    medewerker_id: int, invoer: VriendIn, sessie: AsyncSession = Depends(get_sessie)
) -> list[VriendUit]:
    """Meld een vriend aan voor de vriendenbonus.

    De vriend krijgt een inactief account: genoeg om de bonus aan op te hangen,
    maar niet genoeg om ingepland te worden. De Matching-agent kijkt alleen naar
    actieve medewerkers, dus een uitnodiging kan nooit per ongeluk een shift
    krijgen. Meldt de vriend zich later zelf aan met hetzelfde e-mailadres, dan
    verhuist de referral naar dat echte account.
    """
    gebruiker = await _haal_medewerker(sessie, medewerker_id)

    vriend = User(
        naam=invoer.naam.strip(),
        rol="medewerker",
        email=invoer.email,
        actief=False,
        functies=[],
        beschikbare_dagen=[],
    )
    sessie.add(vriend)
    await sessie.flush()

    sessie.add(
        Referral(
            medewerker_id=gebruiker.id,
            vriend_id=vriend.id,
            uren_vriend=0.0,
            bonus_status="bezig",
            bonus_bedrag_cent=2000,
        )
    )
    await sessie.commit()
    return await _vrienden(sessie, gebruiker)


# ---------------------------------------------------------------------------
# Opbouw van de schermgegevens
# ---------------------------------------------------------------------------


async def _scherm(sessie: AsyncSession, gebruiker: User) -> MedewerkerUit:
    aankomend, geschiedenis = await _mijn_shifts(sessie, gebruiker)
    level = await sessie.get(Level, gebruiker.id)
    return MedewerkerUit(
        id=gebruiker.id,
        naam=gebruiker.naam,
        seizoen_uren=level.seizoen_uren if level else 0.0,
        profiel=_profiel(gebruiker),
        beschikbaar=await _beschikbare_shifts(sessie, gebruiker),
        aankomend=aankomend,
        geschiedenis=geschiedenis,
        vrienden=await _vrienden(sessie, gebruiker),
    )


def _profiel(gebruiker: User) -> ProfielUit:
    return ProfielUit(
        naam=gebruiker.naam,
        email=gebruiker.email,
        telefoon=gebruiker.telefoon,
        woonplaats=gebruiker.woonplaats,
        gewenst_uurloon=gebruiker.gewenst_uurloon,
        functies=list(gebruiker.functies or []),
        beschikbare_dagen=list(gebruiker.beschikbare_dagen or []),
    )


async def _beschikbare_shifts(sessie: AsyncSession, gebruiker: User) -> list[ShiftUit]:
    """Shifts waar deze medewerker daadwerkelijk op kan reageren.

    Dezelfde harde criteria als de Matching-agent hanteert: juiste functie,
    beschikbare dag, niet al gereageerd of ingepland. Een shift tonen waarop de
    agent je toch nooit zou kiezen, is een lege belofte.
    """
    if gebruiker.geschorst or not gebruiker.actief:
        return []

    resultaat = await sessie.execute(
        select(Shift)
        .where(
            Shift.status.in_([str(ShiftStatus.OPEN), str(ShiftStatus.DEELS_GEMATCHT)]),
            Shift.datum >= date.today(),
        )
        .order_by(Shift.datum, Shift.id)
    )
    shifts = list(resultaat.scalars().all())

    # Ook geannuleerde shifts blijven uit de lijst: de agent biedt ze je niet
    # opnieuw aan, dus tonen zou een knop opleveren die niets doet.
    eigen_matches = await sessie.execute(
        select(Match.shift_id).where(Match.medewerker_id == gebruiker.id)
    )
    bezet = set(eigen_matches.scalars().all())

    gereageerd_op = await sessie.execute(
        select(Reactie.shift_id).where(
            Reactie.medewerker_id == gebruiker.id,
            Reactie.status == str(ReactieStatus.OPEN),
        )
    )
    reacties = set(gereageerd_op.scalars().all())

    functies = [f.lower() for f in (gebruiker.functies or [])]
    dagen = gebruiker.beschikbare_dagen or []

    uit: list[ShiftUit] = []
    for shift in shifts:
        if shift.id in bezet or shift.id in reacties:
            continue
        if functies and shift.functie.lower() not in functies:
            continue
        if dagen and DAGEN[shift.datum.weekday()] not in dagen:
            continue
        bedrijf = await sessie.get(Bedrijf, shift.bedrijf_id)
        uit.append(
            ShiftUit(
                id=shift.id,
                role=shift.functie,
                datum=korte_datum(shift.datum),
                tijd=shift.tijd,
                plek=bedrijf.naam if bedrijf else "Onbekende locatie",
                uurloon=uurloon_tekst(shift.uurloon),
            )
        )
    return uit


async def _mijn_shifts(
    sessie: AsyncSession, gebruiker: User
) -> tuple[list[MijnShiftUit], list[MijnShiftUit]]:
    """Splits de eigen shifts in aankomend en geschiedenis.

    De grens is de datum, niet de status: een shift van gisteren waarvan de uren
    nog niet zijn doorgegeven hoort in de geschiedenis, want hij is voorbij.
    """
    resultaat = await sessie.execute(
        select(Match, Shift)
        .join(Shift, Shift.id == Match.shift_id)
        .where(
            Match.medewerker_id == gebruiker.id,
            Match.status.notin_([str(MatchStatus.GEANNULEERD)]),
        )
        .order_by(Shift.datum)
    )
    rijen = list(resultaat.all())

    vandaag = date.today()
    aankomend: list[MijnShiftUit] = []
    geschiedenis: list[MijnShiftUit] = []

    for match, shift in rijen:
        bedrijf = await sessie.get(Bedrijf, shift.bedrijf_id)
        plek = bedrijf.naam if bedrijf else "Onbekende locatie"
        if shift.datum >= vandaag and match.status in {
            str(MatchStatus.VOORGESTELD),
            str(MatchStatus.BEVESTIGD),
        }:
            aankomend.append(
                MijnShiftUit(
                    match_id=match.id,
                    role=shift.functie,
                    datum=korte_datum(shift.datum),
                    tijd=shift.tijd,
                    plek=plek,
                    status=_status_label(match.status),
                    uurloon=shift.uurloon,
                )
            )
        else:
            geschiedenis.append(
                MijnShiftUit(
                    match_id=match.id,
                    role=shift.functie,
                    datum=korte_datum(shift.datum),
                    tijd=shift.tijd,
                    plek=plek,
                    status=_status_label(match.status),
                    uurloon=shift.uurloon,
                    uren=match.uren_gewerkt,
                )
            )

    aankomend.sort(key=lambda s: s.match_id)
    geschiedenis.reverse()
    return aankomend, geschiedenis


def _status_label(status: str) -> str:
    return {
        str(MatchStatus.VOORGESTELD): "Voorgesteld",
        str(MatchStatus.BEVESTIGD): "Bevestigd",
        str(MatchStatus.GEWERKT): "Afgerond",
        str(MatchStatus.NO_SHOW): "Niet verschenen",
        str(MatchStatus.GEANNULEERD): "Geannuleerd",
    }.get(status, status)


async def _vrienden(sessie: AsyncSession, gebruiker: User) -> list[VriendUit]:
    resultaat = await sessie.execute(
        select(Referral).where(Referral.medewerker_id == gebruiker.id).order_by(Referral.id)
    )
    uit: list[VriendUit] = []
    for referral in resultaat.scalars().all():
        vriend = await sessie.get(User, referral.vriend_id)
        label = VRIEND_STATUS.get(referral.bonus_status, referral.bonus_status.capitalize())
        if referral.bonus_status == "uitbetaald":
            label = f"Uitbetaald · €{referral.bonus_bedrag_cent / 100:.0f}"
        uit.append(
            VriendUit(
                naam=vriend.naam if vriend else "Onbekend",
                uren=referral.uren_vriend,
                status=label,
            )
        )
    return uit


__all__ = ["router"]
