"""Tests voor de Matching-agent: matchlogica, levels en no-shows."""

from __future__ import annotations

from sqlalchemy import select

from app.agents.matching import MatchingAgent
from app.core.domein import MatchStatus, ShiftStatus, Tier
from app.db.models import Activiteit, Beslissing, Match, User
from tests.conftest import maak_medewerker, maak_shift


async def test_matcht_op_functie(sessie, bedrijf, zaterdag):
    """Alleen wie de gevraagde functie kan doen, wordt gematcht."""
    kok = await maak_medewerker(sessie, "Lisa", functies=["keuken"], dagen=["za"])
    barman = await maak_medewerker(sessie, "Milan", functies=["bar"], dagen=["za"])
    shift = await maak_shift(sessie, bedrijf, datum=zaterdag, functie="bar")

    await MatchingAgent().match_shift(sessie, shift)

    matches = (await sessie.execute(select(Match))).scalars().all()
    assert len(matches) == 1
    assert matches[0].medewerker_id == barman.id
    assert kok.id not in [m.medewerker_id for m in matches]


async def test_matcht_op_beschikbaarheid(sessie, bedrijf, zaterdag):
    """Wie niet beschikbaar is op die dag, wordt overgeslagen."""
    await maak_medewerker(sessie, "Doordeweeks", functies=["bediening"], dagen=["ma", "di"])
    weekend = await maak_medewerker(
        sessie, "Weekend", functies=["bediening"], dagen=["za", "zo"]
    )
    shift = await maak_shift(sessie, bedrijf, datum=zaterdag)

    await MatchingAgent().match_shift(sessie, shift)

    matches = (await sessie.execute(select(Match))).scalars().all()
    assert len(matches) == 1
    assert matches[0].medewerker_id == weekend.id


async def test_levelprioriteit_bepaalt_de_keuze(sessie, bedrijf, zaterdag):
    """Bij gelijke geschiktheid krijgt de hoogste levelprioriteit voorrang."""
    await maak_medewerker(
        sessie, "Nieuw", functies=["bediening"], dagen=["za"], seizoen_uren=5
    )
    ervaren = await maak_medewerker(
        sessie, "Ervaren", functies=["bediening"], dagen=["za"], seizoen_uren=140
    )
    shift = await maak_shift(sessie, bedrijf, datum=zaterdag)

    await MatchingAgent().match_shift(sessie, shift)

    match = (await sessie.execute(select(Match))).scalars().one()
    assert match.medewerker_id == ervaren.id
    assert match.door_llm is False
    assert "levelprioriteit" in (match.onderbouwing or "").lower()


async def test_geschorste_medewerker_wordt_niet_gematcht(sessie, bedrijf, zaterdag):
    geschorst = await maak_medewerker(
        sessie, "Geschorst", functies=["bediening"], dagen=["za"], seizoen_uren=200
    )
    geschorst.geschorst = True
    beschikbaar = await maak_medewerker(
        sessie, "Beschikbaar", functies=["bediening"], dagen=["za"], seizoen_uren=10
    )
    shift = await maak_shift(sessie, bedrijf, datum=zaterdag)

    await MatchingAgent().match_shift(sessie, shift)

    match = (await sessie.execute(select(Match))).scalars().one()
    assert match.medewerker_id == beschikbaar.id


async def test_geen_dubbele_boeking_op_dezelfde_dag(sessie, bedrijf, zaterdag):
    """Eén medewerker kan niet twee shifts op dezelfde datum krijgen."""
    await maak_medewerker(sessie, "Enige", functies=["bediening"], dagen=["za"])
    shift_a = await maak_shift(sessie, bedrijf, datum=zaterdag)
    shift_b = await maak_shift(sessie, bedrijf, datum=zaterdag)

    agent = MatchingAgent()
    await agent.match_shift(sessie, shift_a)
    await agent.match_shift(sessie, shift_b)

    matches = (await sessie.execute(select(Match))).scalars().all()
    assert len(matches) == 1


async def test_shiftstatus_volgt_de_bezetting(sessie, bedrijf, zaterdag):
    await maak_medewerker(sessie, "Een", functies=["bediening"], dagen=["za"])
    shift = await maak_shift(sessie, bedrijf, datum=zaterdag, aantal=2)

    await MatchingAgent().match_shift(sessie, shift)

    assert shift.status == str(ShiftStatus.DEELS_GEMATCHT)


async def test_elke_match_levert_een_logregel_op(sessie, bedrijf, zaterdag):
    """Randvoorwaarde 6.4: elke agentactie komt in het activiteitenlog."""
    await maak_medewerker(sessie, "Sanne", functies=["bediening"], dagen=["za"])
    shift = await maak_shift(sessie, bedrijf, datum=zaterdag)

    await MatchingAgent().match_shift(sessie, shift)

    regels = (
        (await sessie.execute(select(Activiteit).where(Activiteit.afdeling == "matching")))
        .scalars()
        .all()
    )
    assert len(regels) == 1
    assert regels[0].tier == int(Tier.ZELFSTANDIG)
    assert "Sanne" in regels[0].tekst


async def test_uren_registreren_werkt_level_bij(sessie, bedrijf, zaterdag):
    medewerker = await maak_medewerker(
        sessie, "Tom", functies=["bediening"], dagen=["za"], seizoen_uren=22
    )
    shift = await maak_shift(sessie, bedrijf, datum=zaterdag)
    agent = MatchingAgent()
    await agent.match_shift(sessie, shift)
    match = (await sessie.execute(select(Match))).scalars().one()

    resultaat = await agent.registreer_gewerkte_uren(sessie, match.id, 6.0)

    assert resultaat["seizoen_uren"] == 28.0
    assert resultaat["level"] == 2  # drempel van 25 uur gepasseerd
    assert resultaat["level_naam"] == "Shift Regular"
    assert match.status == str(MatchStatus.GEWERKT)
    assert match.uren_gewerkt == 6.0


async def test_no_show_logt_bij_matching_en_support(sessie, bedrijf, zaterdag):
    """Hoofdstuk 8: no-show geeft een matching-regel én een support-waarschuwing."""
    from app.core.events import verwerk_pending

    await maak_medewerker(sessie, "Milan", functies=["bediening"], dagen=["za"])
    shift = await maak_shift(sessie, bedrijf, datum=zaterdag)
    agent = MatchingAgent()
    await agent.match_shift(sessie, shift)
    match = (await sessie.execute(select(Match))).scalars().one()

    await agent.signaleer_no_show(sessie, match.id)
    await verwerk_pending(sessie)

    afdelingen = [
        a.afdeling
        for a in (await sessie.execute(select(Activiteit))).scalars().all()
    ]
    assert "matching" in afdelingen
    assert "support" in afdelingen

    support_regel = (
        (await sessie.execute(select(Activiteit).where(Activiteit.afdeling == "support")))
        .scalars()
        .one()
    )
    assert "Waarschuwing" in support_regel.tekst
    assert "Milan" in support_regel.tekst


async def test_herhaalde_no_shows_geven_tier2_voorstel(sessie, bedrijf, zaterdag):
    """Drie no-shows: schorsingsvoorstel dat vanzelf doorgaat (tier 2)."""
    from datetime import timedelta

    medewerker = await maak_medewerker(
        sessie, "Onbetrouwbaar", functies=["bediening"], dagen=["za"]
    )
    agent = MatchingAgent()

    for week in range(3):
        shift = await maak_shift(
            sessie, bedrijf, datum=zaterdag + timedelta(weeks=week)
        )
        await agent.match_shift(sessie, shift)
        match = (
            (
                await sessie.execute(
                    select(Match).where(Match.shift_id == shift.id)
                )
            )
            .scalars()
            .one()
        )
        resultaat = await agent.signaleer_no_show(sessie, match.id)

    assert resultaat["aantal_no_shows"] == 3
    beslissing = await sessie.get(Beslissing, resultaat["beslissing_id"])
    assert beslissing is not None
    assert beslissing.tier == int(Tier.TENZIJ)
    assert beslissing.deadline_at is not None
    # Tier 2 legt het voor, maar schorst nog niet.
    assert medewerker.geschorst is False


async def test_urengeschil_is_tier3_en_wacht(sessie, bedrijf, zaterdag):
    """Tier 3: er wordt niets geboekt tot Sebas kiest."""
    await maak_medewerker(sessie, "Noor", functies=["bediening"], dagen=["za"])
    shift = await maak_shift(sessie, bedrijf, datum=zaterdag)
    agent = MatchingAgent()
    await agent.match_shift(sessie, shift)
    match = (await sessie.execute(select(Match))).scalars().one()

    beslissing_id = await agent.meld_urengeschil(
        sessie, match.id, uren_medewerker=8.0, uren_bedrijf=6.0
    )

    beslissing = await sessie.get(Beslissing, beslissing_id)
    assert beslissing.tier == int(Tier.WACHT)
    assert beslissing.deadline_at is None
    assert beslissing.urgentie == "dringend"
    assert match.uren_gewerkt is None  # nog niets vastgelegd


async def test_wervingstekort_gaat_als_event_naar_marketing(sessie, bedrijf, zaterdag):
    """Geen kandidaten -> gestructureerd event naar Marketing, geen vrije tekst."""
    from app.core.events import verwerk_pending
    from app.db.models import AgentEvent

    shift = await maak_shift(sessie, bedrijf, datum=zaterdag, aantal=2)

    await MatchingAgent().match_shift(sessie, shift)

    event = (await sessie.execute(select(AgentEvent))).scalars().one()
    assert event.type == "werving.tekort"
    assert event.bron_afdeling == "matching"
    assert event.doel_afdeling == "marketing"
    assert event.payload["open_plekken"] == 2

    await verwerk_pending(sessie)
    marketing = (
        (await sessie.execute(select(Activiteit).where(Activiteit.afdeling == "marketing")))
        .scalars()
        .all()
    )
    assert len(marketing) == 1


async def test_agent_mag_niet_namens_andere_afdeling_handelen(sessie):
    """Gescheiden verantwoordelijkheden, afgedwongen in code."""
    import pytest

    from app.core.domein import Afdeling
    from app.core.tiers import Voorstel

    agent = MatchingAgent()
    voorstel = Voorstel(
        afdeling=Afdeling.FINANCIEEL,
        tier=Tier.ZELFSTANDIG,
        logtekst="poging",
        actie={"uitvoerder": "matching.geen_actie", "params": {}},
    )
    with pytest.raises(PermissionError):
        await agent.voer_uit(sessie, voorstel)
