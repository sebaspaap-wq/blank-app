"""Endpoints voor het horecascherm van wosz-app.html.

Deze routes vervangen de hardcoded arrays in de frontend:

``aanvragen``           -> GET  /api/horeca/{bedrijf_id}
``submitRequest()``     -> POST /api/horeca/{bedrijf_id}/aanvragen
``accepteerKandidaat()``-> POST /api/horeca/{bedrijf_id}/aanvragen/{id}/kandidaten/{mid}
de vier tellers         -> zitten in ``stats`` van GET /api/horeca/{bedrijf_id}

De gesimuleerde ``setTimeout`` in de frontend, die na een paar seconden een
verzonnen kandidaat toevoegde, is hier een echte matchronde geworden: zodra een
aanvraag binnenkomt draait de Matching-agent er meteen overheen. Dat is het
verschil tussen een demo die reacties nabootst en een systeem dat ze oplevert.
"""

from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.matching import MatchingAgent
from app.api.schemas import (
    AanvraagIn,
    AanvraagUit,
    BedrijfsprofielIn,
    BedrijfsprofielUit,
    HorecafactuurUit,
    HorecamedewerkerUit,
    HorecaStatsUit,
    HorecaUit,
    KandidaatUit,
)
from app.api.weergave import (
    DatumFout,
    kandidaat_info,
    korte_datum,
    lees_datum,
    periode_tekst,
    uurloon_tekst,
)
from app.config import get_settings
from app.core.domein import MatchStatus, ShiftStatus, als_aware, level_voor_uren
from app.core.events import verwerk_pending
from app.db.models import Bedrijf, Factuur, Level, Match, Reactie, Shift, User
from app.db.session import get_sessie

router = APIRouter(prefix="/api/horeca", tags=["horeca"])

#: Hoe ver terug de aanvragenlijst kijkt. Verder terug is administratie, geen
#: dashboard.
HISTORIE_DAGEN = 30

#: Hoeveel kandidaten er per aanvraag getoond worden. De agent kiest zelf; deze
#: lijst laat het bedrijf meekijken en desgewenst zelf iemand aanwijzen.
MAX_KANDIDATEN = 5


async def _verwerk_events(sessie: AsyncSession) -> None:
    await verwerk_pending(sessie, get_settings().event_max_pogingen)


async def _haal_bedrijf(sessie: AsyncSession, bedrijf_id: int) -> Bedrijf:
    bedrijf = await sessie.get(Bedrijf, bedrijf_id)
    if bedrijf is None:
        raise HTTPException(status_code=404, detail="Bedrijf bestaat niet")
    return bedrijf


# ---------------------------------------------------------------------------
# Lezen
# ---------------------------------------------------------------------------


@router.get("/{bedrijf_id}", response_model=HorecaUit)
async def lees_scherm(
    bedrijf_id: int, sessie: AsyncSession = Depends(get_sessie)
) -> HorecaUit:
    """Alles wat het horecascherm nodig heeft, in één aanroep."""
    bedrijf = await _haal_bedrijf(sessie, bedrijf_id)
    return await _scherm(sessie, bedrijf)


@router.get("/{bedrijf_id}/aanvragen", response_model=list[AanvraagUit])
async def lees_aanvragen(
    bedrijf_id: int, sessie: AsyncSession = Depends(get_sessie)
) -> list[AanvraagUit]:
    bedrijf = await _haal_bedrijf(sessie, bedrijf_id)
    return await _aanvragen(sessie, bedrijf)


# ---------------------------------------------------------------------------
# Schrijven
# ---------------------------------------------------------------------------


@router.post("/{bedrijf_id}/aanvragen", response_model=HorecaUit, status_code=201)
async def plaats_aanvraag(
    bedrijf_id: int, invoer: AanvraagIn, sessie: AsyncSession = Depends(get_sessie)
) -> HorecaUit:
    """Plaats een personeelsvraag en laat de agent hem meteen vullen.

    Wachten op de volgende matchronde zou betekenen dat een aanvraag voor
    vanavond pas morgen wordt opgepakt. De agent draait daarom direct; wat hij
    niet kan vullen, meldt hij als wervingstekort aan Marketing — dat gaat via
    het event dat ``match_shift`` zelf publiceert.
    """
    bedrijf = await _haal_bedrijf(sessie, bedrijf_id)

    try:
        datum = lees_datum(invoer.datum)
    except DatumFout as fout:
        raise HTTPException(status_code=422, detail=str(fout)) from fout

    if datum < date.today():
        raise HTTPException(
            status_code=422, detail="Die datum ligt in het verleden. Kies een datum vanaf vandaag."
        )

    shift = Shift(
        bedrijf_id=bedrijf.id,
        datum=datum,
        tijd=invoer.tijd.strip(),
        functie=invoer.functie.strip(),
        aantal_gevraagd=invoer.aantal,
        status=str(ShiftStatus.OPEN),
        uurloon=invoer.uurloon.strip() if invoer.uurloon else None,
        duur_uren=_duur_uit_tijd(invoer.tijd),
    )
    sessie.add(shift)
    await sessie.flush()

    await MatchingAgent().match_shift(sessie, shift)
    await _verwerk_events(sessie)
    await sessie.commit()
    return await _scherm(sessie, bedrijf)


@router.post(
    "/{bedrijf_id}/aanvragen/{shift_id}/kandidaten/{medewerker_id}",
    response_model=HorecaUit,
)
async def accepteer_kandidaat(
    bedrijf_id: int,
    shift_id: int,
    medewerker_id: int,
    sessie: AsyncSession = Depends(get_sessie),
) -> HorecaUit:
    """Het bedrijf wijst zelf een kandidaat aan.

    Dit loopt bewust via ``MatchingAgent``: ook een keuze van het bedrijf hoort
    in het activiteitenlog en moet dezelfde controles doorlopen (niet vol, niet
    dubbel geboekt). De agent legt de match vast; deze route beslist alleen wie
    het wordt.
    """
    bedrijf = await _haal_bedrijf(sessie, bedrijf_id)
    shift = await sessie.get(Shift, shift_id)
    if shift is None or shift.bedrijf_id != bedrijf.id:
        raise HTTPException(status_code=404, detail="Deze aanvraag is niet van jouw bedrijf")

    agent = MatchingAgent()
    kandidaten = await agent.kandidaten_voor(sessie, shift)
    gekozen = next((k for k in kandidaten if k.id == medewerker_id), None)
    if gekozen is None:
        raise HTTPException(
            status_code=409,
            detail="Deze kandidaat is niet meer beschikbaar voor deze shift",
        )

    await agent.plan_kandidaat_in(
        sessie,
        shift,
        gekozen,
        onderbouwing=f"Door {bedrijf.naam} zelf gekozen uit de voorgestelde kandidaten.",
    )
    await _verwerk_events(sessie)
    await sessie.commit()
    return await _scherm(sessie, bedrijf)


@router.post("/{bedrijf_id}/profiel", response_model=HorecaUit)
async def bewaar_profiel(
    bedrijf_id: int, invoer: BedrijfsprofielIn, sessie: AsyncSession = Depends(get_sessie)
) -> HorecaUit:
    """Werk het bedrijfsprofiel bij.

    De contactpersoon staat als gebruiker in het systeem en niet als tekstveld
    op het bedrijf — dat is dezelfde persoon die inlogt. Bestaat hij nog niet,
    dan wordt hij hier aangemaakt.
    """
    bedrijf = await _haal_bedrijf(sessie, bedrijf_id)

    bedrijf.naam = invoer.naam.strip()
    bedrijf.plaats = invoer.plaats or None

    if invoer.contactpersoon or invoer.email:
        contact = (
            await sessie.get(User, bedrijf.contact_user_id)
            if bedrijf.contact_user_id
            else None
        )
        if contact is None:
            contact = User(naam=invoer.contactpersoon or bedrijf.naam, rol="horeca")
            sessie.add(contact)
            await sessie.flush()
            bedrijf.contact_user_id = contact.id
        if invoer.contactpersoon:
            contact.naam = invoer.contactpersoon.strip()
        contact.email = invoer.email or None
        contact.bedrijf_id = bedrijf.id

    await sessie.commit()
    return await _scherm(sessie, bedrijf)


def _duur_uit_tijd(tijd: str) -> float:
    """Leid de shiftduur af uit "17:00-01:00".

    Lukt dat niet, dan houden we 6 uur aan — dezelfde standaard als het
    datamodel. De duur bepaalt alleen het urenvoorstel achteraf, dus een
    schatting is hier beter dan een foutmelding op een verder prima aanvraag.
    """
    schoon = tijd.replace("–", "-").replace("—", "-").replace(" ", "")
    delen = schoon.split("-")
    if len(delen) != 2:
        return 6.0
    try:
        start_u, start_m = (int(x) for x in delen[0].split(":"))
        eind_u, eind_m = (int(x) for x in delen[1].split(":"))
    except ValueError:
        return 6.0
    start = start_u * 60 + start_m
    eind = eind_u * 60 + eind_m
    if eind <= start:  # loopt door na middernacht
        eind += 24 * 60
    return round((eind - start) / 60, 1)


# ---------------------------------------------------------------------------
# Opbouw van de schermgegevens
# ---------------------------------------------------------------------------


async def _scherm(sessie: AsyncSession, bedrijf: Bedrijf) -> HorecaUit:
    aanvragen = await _aanvragen(sessie, bedrijf)
    return HorecaUit(
        bedrijf_id=bedrijf.id,
        bedrijf=bedrijf.naam,
        profiel=await _profiel(sessie, bedrijf),
        stats=await _stats(sessie, bedrijf, aanvragen),
        aanvragen=aanvragen,
        medewerkers=await _medewerkers(sessie, bedrijf),
        facturen=await _facturen(sessie, bedrijf),
    )


async def _profiel(sessie: AsyncSession, bedrijf: Bedrijf) -> BedrijfsprofielUit:
    contact = (
        await sessie.get(User, bedrijf.contact_user_id)
        if bedrijf.contact_user_id
        else None
    )
    return BedrijfsprofielUit(
        naam=bedrijf.naam,
        plaats=bedrijf.plaats,
        contactpersoon=contact.naam if contact else None,
        email=contact.email if contact else None,
        tarief_per_uur=bedrijf.tarief_per_uur,
    )


async def _medewerkers(
    sessie: AsyncSession, bedrijf: Bedrijf
) -> list[HorecamedewerkerUit]:
    """Iedereen die via WOSZ voor dit bedrijf heeft gewerkt.

    Alleen daadwerkelijk gewerkte shifts tellen. Een geplande shift zegt nog
    niets, en een no-show hoort hier niet als werkervaring te verschijnen.
    """
    resultaat = await sessie.execute(
        select(Match, Shift)
        .join(Shift, Shift.id == Match.shift_id)
        .where(
            Shift.bedrijf_id == bedrijf.id,
            Match.status == str(MatchStatus.GEWERKT),
        )
    )

    per_persoon: dict[int, dict] = {}
    for match, shift in resultaat.all():
        regel = per_persoon.setdefault(
            match.medewerker_id,
            {"uren": 0.0, "laatste": shift.datum, "functies": {}},
        )
        regel["uren"] += match.uren_gewerkt or 0.0
        regel["laatste"] = max(regel["laatste"], shift.datum)
        regel["functies"][shift.functie] = regel["functies"].get(shift.functie, 0) + 1

    uit: list[HorecamedewerkerUit] = []
    for medewerker_id, regel in per_persoon.items():
        persoon = await sessie.get(User, medewerker_id)
        if persoon is None:
            continue
        # De functie waarin iemand hier het vaakst heeft gewerkt — dat is wat
        # het bedrijf van hem kent, niet wat er verder in zijn profiel staat.
        vaakst = max(regel["functies"].items(), key=lambda p: p[1])[0]
        uit.append(
            HorecamedewerkerUit(
                naam=persoon.naam,
                functie=vaakst.capitalize(),
                uren_totaal=round(regel["uren"], 1),
                laatste_shift=korte_datum(regel["laatste"]),
                contact=persoon.email or persoon.telefoon or "—",
            )
        )
    uit.sort(key=lambda m: -m.uren_totaal)
    return uit


async def _facturen(sessie: AsyncSession, bedrijf: Bedrijf) -> list[HorecafactuurUit]:
    resultaat = await sessie.execute(
        select(Factuur)
        .where(Factuur.bedrijf_id == bedrijf.id)
        .order_by(Factuur.periode.desc(), Factuur.id.desc())
    )
    return [
        HorecafactuurUit(
            id=f.id,
            periode=periode_tekst(f.periode),
            uren=round(f.uren, 1),
            tarief_per_uur_eur=bedrijf.tarief_per_uur,
            bedrag_eur=f.bedrag_cent / 100,
            status=f.status,
        )
        for f in resultaat.scalars().all()
    ]


async def _aanvragen(sessie: AsyncSession, bedrijf: Bedrijf) -> list[AanvraagUit]:
    grens = date.today() - timedelta(days=HISTORIE_DAGEN)
    resultaat = await sessie.execute(
        select(Shift)
        .where(
            Shift.bedrijf_id == bedrijf.id,
            Shift.datum >= grens,
            Shift.status != str(ShiftStatus.GEANNULEERD),
        )
        .order_by(Shift.datum.desc(), Shift.id.desc())
    )

    uit: list[AanvraagUit] = []
    for shift in resultaat.scalars().all():
        uit.append(
            AanvraagUit(
                id=shift.id,
                functie=shift.functie,
                datum=korte_datum(shift.datum),
                tijd=shift.tijd,
                gevraagd=shift.aantal_gevraagd,
                gematcht=await _aantal_gematcht(sessie, shift),
                uurloon=uurloon_tekst(shift.uurloon),
                kandidaten=await _kandidaten(sessie, shift),
            )
        )
    return uit


async def _aantal_gematcht(sessie: AsyncSession, shift: Shift) -> int:
    resultaat = await sessie.execute(
        select(Match).where(
            Match.shift_id == shift.id,
            Match.status.notin_([str(MatchStatus.GEANNULEERD), str(MatchStatus.NO_SHOW)]),
        )
    )
    return len(list(resultaat.scalars().all()))


async def _kandidaten(sessie: AsyncSession, shift: Shift) -> list[KandidaatUit]:
    """Wie er nog beschikbaar is voor de openstaande plekken.

    Alleen tonen wat de agent ook echt zou kunnen inplannen — dus dezelfde harde
    criteria. Iemand die zelf op de shift heeft gereageerd staat bovenaan.
    """
    if await _aantal_gematcht(sessie, shift) >= shift.aantal_gevraagd:
        return []
    if shift.datum < date.today():
        return []

    beschikbaar = await MatchingAgent().kandidaten_voor(sessie, shift)

    gereageerd = await sessie.execute(
        select(Reactie.medewerker_id).where(Reactie.shift_id == shift.id)
    )
    reacties = set(gereageerd.scalars().all())

    gewogen: list[tuple[bool, float, User]] = []
    for kandidaat in beschikbaar:
        level = await sessie.get(Level, kandidaat.id)
        uren = level.seizoen_uren if level else 0.0
        gewogen.append((kandidaat.id in reacties, uren, kandidaat))
    gewogen.sort(key=lambda rij: (not rij[0], -rij[1], rij[2].id))

    uit: list[KandidaatUit] = []
    for _, uren, kandidaat in gewogen[:MAX_KANDIDATEN]:
        uit.append(
            KandidaatUit(
                medewerker_id=kandidaat.id,
                naam=kandidaat.naam,
                info=kandidaat_info(
                    ervaring_jaren=kandidaat.ervaring_jaren or 0.0,
                    functies=list(kandidaat.functies or []),
                    level_naam=level_voor_uren(uren)["naam"],
                ),
                wens=uurloon_tekst(kandidaat.gewenst_uurloon),
            )
        )
    return uit


async def _stats(
    sessie: AsyncSession, bedrijf: Bedrijf, aanvragen: list[AanvraagUit]
) -> HorecaStatsUit:
    """De vier tellers bovenaan het scherm, uit echte cijfers.

    ``gemiddeldeMatchtijdMinuten`` is de tijd tussen het plaatsen van een
    aanvraag en de eerste match erop — het getal dat een bedrijf wil weten: hoe
    snel heb ik iemand? Zonder matches valt er niets te middelen; dan is het
    ``None`` en niet 0, want "nog niets gemeten" is iets anders dan "meteen".
    """
    actief = sum(1 for a in aanvragen if a.gematcht < a.gevraagd)
    vandaag = date.today()

    week_start = vandaag - timedelta(days=vandaag.weekday())
    deze_week = await sessie.execute(
        select(Match)
        .join(Shift, Shift.id == Match.shift_id)
        .where(
            Shift.bedrijf_id == bedrijf.id,
            Shift.datum >= week_start,
            Match.status.notin_([str(MatchStatus.GEANNULEERD)]),
        )
    )
    gematcht_deze_week = len(list(deze_week.scalars().all()))

    alle = await sessie.execute(
        select(Match, Shift)
        .join(Shift, Shift.id == Match.shift_id)
        .where(
            Shift.bedrijf_id == bedrijf.id,
            Match.status.notin_([str(MatchStatus.GEANNULEERD)]),
        )
    )
    rijen = list(alle.all())
    uren_deze_maand = sum(
        m.uren_gewerkt or 0.0
        for m, s in rijen
        if (s.datum.year, s.datum.month) == (vandaag.year, vandaag.month)
    )

    # Eerste match per shift, zodat een shift met drie plekken niet drie keer
    # meetelt in het gemiddelde.
    eerste: dict[int, tuple[Match, Shift]] = {}
    for match, shift in rijen:
        huidig = eerste.get(shift.id)
        if huidig is None or als_aware(match.aangemaakt_op) < als_aware(huidig[0].aangemaakt_op):
            eerste[shift.id] = (match, shift)

    wachttijden = [
        (als_aware(match.aangemaakt_op) - als_aware(shift.aangemaakt_op)).total_seconds() / 60
        for match, shift in eerste.values()
        if match.aangemaakt_op and shift.aangemaakt_op
    ]
    # Een negatieve wachttijd zegt niets en zou het gemiddelde vertekenen: die
    # ontstaat alleen bij demodata die met terugwerkende kracht is aangemaakt.
    wachttijden = [w for w in wachttijden if w >= 0]

    return HorecaStatsUit(
        actieve_aanvragen=actief,
        gematcht_deze_week=gematcht_deze_week,
        uren_deze_maand=round(uren_deze_maand),
        gemiddelde_matchtijd_minuten=(
            round(sum(wachttijden) / len(wachttijden)) if wachttijden else None
        ),
    )


__all__ = ["router"]
