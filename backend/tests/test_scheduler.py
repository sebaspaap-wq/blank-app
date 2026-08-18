"""Tests voor de automatische aansturing.

Twee vragen staan hier centraal. Ten eerste: doet de scheduler het werk dat
anders op een knopdruk zou wachten? Ten tweede, en belangrijker: blijft de
tier-indeling overeind nu er niemand meekijkt? Een taak die vanzelf draait mag
nooit meer kunnen dan de agent zelf mag.
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest
from sqlalchemy import select

from app.agents.matching import ESCALEER_NA_DAGEN, HERINNER_NA_DAGEN, MatchingAgent
from app.core.domein import BeslissingStatus, MatchStatus, Tier
from app.core.events import UrenOntbreken, verwerk_pending
from app.db.models import AgentEvent, Bericht, Beslissing, Match, Shift
from app import scheduler
from tests.conftest import maak_medewerker, maak_shift


async def _afgelopen_shift(sessie, bedrijf, *, dagen_geleden: int, medewerker):
    shift = await maak_shift(
        sessie,
        bedrijf,
        datum=date.today() - timedelta(days=dagen_geleden),
        functie="bediening",
    )
    match = Match(
        shift_id=shift.id,
        medewerker_id=medewerker.id,
        status=str(MatchStatus.BEVESTIGD),
    )
    sessie.add(match)
    await sessie.flush()
    return shift, match


# ---------------------------------------------------------------------------
# Uren opvolgen
# ---------------------------------------------------------------------------


async def test_herinnering_na_een_afgelopen_shift(sessie, bedrijf):
    """Zonder deze stap blijft een shift eeuwig op 'bevestigd' staan."""
    medewerker = await maak_medewerker(
        sessie, "Sanne", functies=["bediening"], dagen=["za"]
    )
    await _afgelopen_shift(
        sessie, bedrijf, dagen_geleden=HERINNER_NA_DAGEN, medewerker=medewerker
    )

    verslag = await MatchingAgent().volg_afgelopen_shifts_op(sessie)
    assert verslag["herinnerd"] == ["Sanne"]
    assert verslag["geescaleerd"] == []

    await verwerk_pending(sessie)
    berichten = (await sessie.execute(select(Bericht))).scalars().all()
    assert [b.sjabloon for b in berichten] == ["uren_herinnering"]
    assert "Strandtent Zuid" in berichten[0].inhoud


async def test_dezelfde_herinnering_gaat_niet_twee_keer_de_deur_uit(sessie, bedrijf):
    medewerker = await maak_medewerker(
        sessie, "Sanne", functies=["bediening"], dagen=["za"]
    )
    await _afgelopen_shift(
        sessie, bedrijf, dagen_geleden=HERINNER_NA_DAGEN, medewerker=medewerker
    )

    agent = MatchingAgent()
    await agent.volg_afgelopen_shifts_op(sessie)
    await verwerk_pending(sessie)
    tweede = await agent.volg_afgelopen_shifts_op(sessie)

    assert tweede["herinnerd"] == []
    berichten = (await sessie.execute(select(Bericht))).scalars().all()
    assert len(berichten) == 1


async def test_een_shift_van_vandaag_levert_nog_geen_herinnering_op(sessie, bedrijf):
    """Een avondshift die na middernacht eindigt is 's ochtends nog niet 'te laat'."""
    medewerker = await maak_medewerker(
        sessie, "Sanne", functies=["bediening"], dagen=["za"]
    )
    shift = await maak_shift(sessie, bedrijf, datum=date.today(), functie="bediening")
    sessie.add(
        Match(
            shift_id=shift.id,
            medewerker_id=medewerker.id,
            status=str(MatchStatus.BEVESTIGD),
        )
    )
    await sessie.flush()

    verslag = await MatchingAgent().volg_afgelopen_shifts_op(sessie)
    assert verslag == {"herinnerd": [], "geescaleerd": []}
    assert (await sessie.execute(select(AgentEvent))).scalars().all() == []


async def test_ontbrekende_uren_gaan_als_tier_2_naar_sebas(sessie, bedrijf):
    """De agent boekt niet zelf en beschuldigt niemand; hij legt het voor."""
    medewerker = await maak_medewerker(
        sessie, "Sanne", functies=["bediening"], dagen=["za"]
    )
    _shift, match = await _afgelopen_shift(
        sessie, bedrijf, dagen_geleden=ESCALEER_NA_DAGEN, medewerker=medewerker
    )

    verslag = await MatchingAgent().volg_afgelopen_shifts_op(sessie)
    assert verslag["geescaleerd"] == ["Sanne"]

    beslissing = (await sessie.execute(select(Beslissing))).scalars().one()
    assert beslissing.tier == int(Tier.TENZIJ)
    assert beslissing.status == str(BeslissingStatus.OPEN)
    assert beslissing.deadline_at is not None
    assert [o["naam"] for o in beslissing.opties] == ["6 uur boeken", "Niet verschenen"]

    # Er is nog niets gebeurd: dat is precies het punt van tier 2.
    await sessie.refresh(match)
    assert match.status == str(MatchStatus.BEVESTIGD)
    assert match.uren_gewerkt is None


async def test_de_voorzichtige_optie_is_de_standaardafloop(sessie, bedrijf):
    """Als Sebas niets doet, worden de geplande uren geboekt.

    Iemand als 'niet verschenen' registreren heeft gevolgen voor zijn level en
    toekomstige shifts. Dat is geen uitkomst die mag ontstaan doordat er niemand
    op de knop drukte.
    """
    medewerker = await maak_medewerker(
        sessie, "Sanne", functies=["bediening"], dagen=["za"]
    )
    await _afgelopen_shift(
        sessie, bedrijf, dagen_geleden=ESCALEER_NA_DAGEN, medewerker=medewerker
    )
    await MatchingAgent().volg_afgelopen_shifts_op(sessie)

    beslissing = (await sessie.execute(select(Beslissing))).scalars().one()
    standaard = beslissing.opties[0]
    assert standaard["actie"]["uitvoerder"] == "matching.corrigeer_uren"


async def test_een_voorgelegde_shift_wordt_niet_opnieuw_voorgelegd(sessie, bedrijf):
    medewerker = await maak_medewerker(
        sessie, "Sanne", functies=["bediening"], dagen=["za"]
    )
    await _afgelopen_shift(
        sessie, bedrijf, dagen_geleden=ESCALEER_NA_DAGEN, medewerker=medewerker
    )

    agent = MatchingAgent()
    await agent.volg_afgelopen_shifts_op(sessie)
    tweede = await agent.volg_afgelopen_shifts_op(sessie)

    assert tweede["geescaleerd"] == []
    beslissingen = (await sessie.execute(select(Beslissing))).scalars().all()
    assert len(beslissingen) == 1


async def test_doorgegeven_uren_halen_de_shift_uit_de_opvolging(sessie, bedrijf):
    medewerker = await maak_medewerker(
        sessie, "Sanne", functies=["bediening"], dagen=["za"]
    )
    _shift, match = await _afgelopen_shift(
        sessie, bedrijf, dagen_geleden=ESCALEER_NA_DAGEN, medewerker=medewerker
    )

    await MatchingAgent().registreer_gewerkte_uren(sessie, match.id, 6.0)
    verslag = await MatchingAgent().volg_afgelopen_shifts_op(sessie)

    assert verslag == {"herinnerd": [], "geescaleerd": []}


# ---------------------------------------------------------------------------
# De taken zelf
# ---------------------------------------------------------------------------


async def test_matchingtaak_vult_een_shift_die_pas_later_matchbaar_werd(
    sessie, bedrijf, zaterdag, engine
):
    """Precies waar de periodieke ronde voor bestaat.

    De shift stond open zonder kandidaten. Meldt er zich daarna iemand aan, dan
    moet die shift alsnog gevuld worden zonder dat iemand op een knop drukt.
    """
    await maak_shift(sessie, bedrijf, datum=zaterdag, functie="bediening")
    await maak_medewerker(sessie, "Sanne", functies=["bediening"], dagen=["za"])
    await sessie.commit()

    uitkomst = await scheduler.draai_taak(
        scheduler.Taak("matching", interval=1, werk=scheduler.match_open_shifts)
    )
    assert uitkomst == "1 plek(ken) gevuld"

    matches = (await sessie.execute(select(Match))).scalars().all()
    assert len(matches) == 1
    assert matches[0].status == str(MatchStatus.BEVESTIGD)


async def test_een_taak_zonder_werk_meldt_niets(sessie, engine):
    """Anders staat het log vol regels waarin niets gebeurde."""
    await sessie.commit()
    uitkomst = await scheduler.draai_taak(
        scheduler.Taak("matching", interval=1, werk=scheduler.match_open_shifts)
    )
    assert uitkomst is None


async def test_facturentaak_doet_alleen_op_de_eerste_iets(sessie, engine, monkeypatch):
    await sessie.commit()

    class _Middenin(date):
        @classmethod
        def today(cls):
            return date(2026, 8, 18)

    monkeypatch.setattr("app.scheduler.date", _Middenin)
    assert await scheduler.sluit_vorige_maand_af(sessie) is None


@pytest.mark.parametrize(
    ("seconden", "verwacht"),
    [
        (600, "elke 10 minuten"),
        (3600, "elk uur"),
        (6 * 3600, "elke 6 uur"),
        (24 * 3600, "elke dag"),
        (48 * 3600, "elke 2 dagen"),
        (60, "elke minuut"),
    ],
)
def test_intervallen_zijn_leesbaar(seconden, verwacht):
    assert scheduler._leesbaar(seconden) == verwacht


def test_elke_taak_heeft_een_eigen_naam():
    namen = [taak.naam for taak in scheduler.TAKEN]
    assert len(namen) == len(set(namen))


def test_geen_enkele_taak_raakt_uitbetalingen(sessie):
    """De scheduler mag niet stiekem een pad naar geld openen.

    Elke taak roept één agentmethode aan. Zou daar een uitbetaling tussen zitten,
    dan zou er 's nachts geld de deur uit kunnen zonder dat Sebas iets heeft
    gezien. Deze test leest de broncode van de taken en eist dat er niets uit
    ``app.payouts`` in voorkomt.
    """
    import inspect

    for taak in scheduler.TAKEN:
        bron = inspect.getsource(taak.werk)
        assert "payout" not in bron.lower()
        assert "uitbetal" not in bron.lower()
