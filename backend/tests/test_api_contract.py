"""Contracttests: geeft de API exact terug wat wosz-app.html verwacht?

Elke test hieronder controleert een veldnaam of vorm die een renderfunctie in
de bestaande frontend letterlijk gebruikt. Breekt een van deze tests, dan breekt
het dashboard — ook al blijft de backend zelf gezond.
"""

from __future__ import annotations

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.agents.matching import MatchingAgent
from app.api import directie as directie_api
from app.api import matching as matching_api
from app.core.domein import Afdeling, Tier, Urgentie
from app.core.tiers import Optie, Voorstel, behandel_voorstel
from app.db.models import Match
from app.db.session import get_sessie
from tests.conftest import maak_doelstelling, maak_medewerker, maak_shift

#: Sleutels van DEPT_LABEL in wosz-app.html.
FRONTEND_AFDELINGEN = {"marketing", "matching", "support", "financieel"}


@pytest_asyncio.fixture
async def client(sessie):
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(directie_api.router)
    app.include_router(matching_api.router)

    async def _sessie_override():
        yield sessie

    app.dependency_overrides[get_sessie] = _sessie_override

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c


# ---------------------------------------------------------------------------
# activityLog  ->  GET /api/directie/activiteiten
# ---------------------------------------------------------------------------


async def test_activiteiten_hebben_de_velden_van_activitylog(
    client, sessie, bedrijf, zaterdag
):
    """``renderLog()`` leest a.tijd, a.tekst en a.afdeling."""
    await maak_medewerker(sessie, "Sanne", functies=["bediening"], dagen=["za"])
    shift = await maak_shift(sessie, bedrijf, datum=zaterdag)
    await MatchingAgent().match_shift(sessie, shift)

    antwoord = await client.get("/api/directie/activiteiten")
    assert antwoord.status_code == 200
    regels = antwoord.json()
    assert regels, "verwacht minstens één activiteit"

    regel = regels[0]
    assert set(regel) >= {"tijd", "tekst", "afdeling"}
    assert isinstance(regel["tekst"], str) and regel["tekst"]
    # 'HH:MM', zoals toLocaleTimeString('nl-NL', {hour:'2-digit', minute:'2-digit'})
    assert len(regel["tijd"]) == 5 and regel["tijd"][2] == ":"


async def test_afdeling_is_altijd_een_sleutel_van_dept_label_of_null(
    client, sessie, bedrijf, zaterdag
):
    """DEPT_LABEL kent alleen vier afdelingen.

    Een onbekende waarde zou in de frontend als 'undefined' verschijnen. Voor
    directieregels sturen we daarom null, precies zoals resolveDecision() nu
    een regel zonder afdeling toevoegt.
    """
    await maak_medewerker(sessie, "Noor", functies=["bediening"], dagen=["za"])
    shift = await maak_shift(sessie, bedrijf, datum=zaterdag)
    await MatchingAgent().match_shift(sessie, shift)

    uitkomst = await behandel_voorstel(
        sessie,
        Voorstel(
            afdeling=Afdeling.MATCHING,
            tier=Tier.WACHT,
            titel="Iets kiezen",
            situatie="Situatie.",
            logtekst="voorstel",
            opties=[
                Optie(naam="A", gevolg="x", actie={}),
                Optie(naam="B", gevolg="y", actie={}),
            ],
        ),
    )
    await client.post(
        f"/api/directie/beslissingen/{uitkomst.beslissing_id}/kies",
        json={"optie_index": 0},
    )

    regels = (await client.get("/api/directie/activiteiten")).json()
    for regel in regels:
        assert regel["afdeling"] is None or regel["afdeling"] in FRONTEND_AFDELINGEN

    assert any(
        r["afdeling"] is None and r["tekst"].startswith("Jouw keuze verwerkt:")
        for r in regels
    )


async def test_activiteiten_staan_nieuwste_eerst(client, sessie, bedrijf, zaterdag):
    """``activityLog.unshift()`` zet de nieuwste vooraan; de API doet hetzelfde."""
    from app.core.activity import log_activiteit

    await log_activiteit(sessie, afdeling=Afdeling.MATCHING, tekst="eerste")
    await log_activiteit(sessie, afdeling=Afdeling.MATCHING, tekst="tweede")

    regels = (await client.get("/api/directie/activiteiten")).json()
    assert regels[0]["tekst"] == "tweede"


async def test_activiteiten_respecteert_de_limiet_van_40(client, sessie):
    from app.core.activity import log_activiteit

    for i in range(45):
        await log_activiteit(sessie, afdeling=Afdeling.SUPPORT, tekst=f"regel {i}")

    regels = (await client.get("/api/directie/activiteiten")).json()
    assert len(regels) == 40


async def test_afdelingsfeed_filtert_op_afdeling(client, sessie):
    from app.core.activity import log_activiteit

    await log_activiteit(sessie, afdeling=Afdeling.SUPPORT, tekst="support-regel")
    await log_activiteit(sessie, afdeling=Afdeling.MATCHING, tekst="matching-regel")

    regels = (await client.get("/api/directie/activiteiten/support")).json()
    assert len(regels) == 1
    assert regels[0]["afdeling"] == "support"


# ---------------------------------------------------------------------------
# decisions  ->  GET /api/directie/beslissingen
# ---------------------------------------------------------------------------


async def _maak_beslissing(sessie) -> int:
    uitkomst = await behandel_voorstel(
        sessie,
        Voorstel(
            afdeling=Afdeling.MATCHING,
            tier=Tier.WACHT,
            urgentie=Urgentie.DRINGEND,
            titel="Vriendenbonus uitbetalen aan Sanne de Vries",
            situatie="Tom Hendriks heeft de 50-uursgrens gehaald.",
            aanbeveling="AI-advies: Goedkeuren — uren komen overeen.",
            logtekst="bonus klaargezet",
            opties=[
                Optie(naam="Goedkeuren", gevolg="€20 wordt overgemaakt", actie={}),
                Optie(naam="Uren controleren", gevolg="Uitbetaling 1 dag uitgesteld", actie={}),
            ],
        ),
    )
    return uitkomst.beslissing_id


async def test_beslissing_heeft_de_velden_van_decisioncardhtml(client, sessie):
    """``decisionCardHtml()`` leest id, urgentie, titel, situatie, opties, aanbeveling."""
    await _maak_beslissing(sessie)

    body = (await client.get("/api/directie/beslissingen")).json()
    assert set(body) == {"open", "afgehandeld"}

    beslissing = body["open"][0]
    assert set(beslissing) >= {
        "id",
        "urgentie",
        "titel",
        "situatie",
        "opties",
        "aanbeveling",
    }
    assert isinstance(beslissing["id"], int)
    assert beslissing["urgentie"] in {"dringend", "deze-week"}
    assert isinstance(beslissing["aanbeveling"], str)  # nooit null: gaat rechtstreeks in HTML

    optie = beslissing["opties"][0]
    assert set(optie) == {"naam", "gevolg"}


async def test_dringende_beslissing_staat_vooraan(client, sessie):
    """``renderUrgentBanner()`` zoekt de eerste dringende beslissing."""
    await behandel_voorstel(
        sessie,
        Voorstel(
            afdeling=Afdeling.MATCHING,
            tier=Tier.WACHT,
            urgentie=Urgentie.DEZE_WEEK,
            titel="Rustig",
            situatie="Kan wachten.",
            logtekst="x",
            opties=[Optie(naam="A", gevolg="x"), Optie(naam="B", gevolg="y")],
        ),
    )
    await _maak_beslissing(sessie)

    body = (await client.get("/api/directie/beslissingen")).json()
    assert body["open"][0]["urgentie"] == "dringend"


async def test_afgehandelde_beslissing_heeft_camelcase_gekozenoptie(client, sessie):
    """``decisionCardHtml()`` toont ``d.gekozenOptie`` — let op de hoofdletter O."""
    beslissing_id = await _maak_beslissing(sessie)

    antwoord = await client.post(
        f"/api/directie/beslissingen/{beslissing_id}/kies", json={"optie_index": 0}
    )
    assert antwoord.status_code == 200
    assert antwoord.json()["gekozenOptie"] == "Goedkeuren"

    body = (await client.get("/api/directie/beslissingen")).json()
    assert body["open"] == []
    assert body["afgehandeld"][0]["gekozenOptie"] == "Goedkeuren"


async def test_onbekende_beslissing_geeft_404(client):
    antwoord = await client.post(
        "/api/directie/beslissingen/999/kies", json={"optie_index": 0}
    )
    assert antwoord.status_code == 404


async def test_ongeldige_optie_geeft_422(client, sessie):
    beslissing_id = await _maak_beslissing(sessie)
    antwoord = await client.post(
        f"/api/directie/beslissingen/{beslissing_id}/kies", json={"optie_index": 9}
    )
    assert antwoord.status_code == 422


# ---------------------------------------------------------------------------
# dailyReport  ->  GET /api/directie/dagrapport
# ---------------------------------------------------------------------------


async def test_dagrapport_heeft_de_vorm_van_dailyreport(client, sessie):
    await maak_doelstelling(sessie)

    rapport = (await client.get("/api/directie/dagrapport")).json()
    assert set(rapport) == {"datum", "secties", "voortgang", "aandacht"}

    # 'Maandag 17 augustus 2026'
    assert rapport["datum"][0].isupper()
    assert any(maand in rapport["datum"] for maand in ("januari", "augustus", "december"))

    sectie = rapport["secties"][0]
    assert set(sectie) == {"titel", "icon", "items"}
    assert isinstance(sectie["items"], list)
    assert all(isinstance(i, str) for i in sectie["items"])
    # renderDashSummary() doet items.slice(0,1); een lege lijst rendert niets.
    assert sectie["items"]


async def test_voortgang_gebruikt_camelcase_iseuro(client, sessie):
    """``fmtVal(v.waarde, v.isEuro)`` leest dat veld letterlijk."""
    await maak_doelstelling(sessie)

    rapport = (await client.get("/api/directie/dagrapport")).json()
    metriek = rapport["voortgang"][0]
    assert set(metriek) == {"label", "waarde", "doel", "isEuro"}
    assert isinstance(metriek["isEuro"], bool)
    assert metriek["doel"] > 0  # renderRapport() deelt hierdoor


async def test_aandachtspunten_zijn_platte_strings(client, sessie):
    """``dailyReport.aandacht.map(a => <li>${a}</li>)`` verwacht strings."""
    await _maak_beslissing(sessie)

    rapport = (await client.get("/api/directie/dagrapport")).json()
    assert rapport["aandacht"]
    assert all(isinstance(a, str) for a in rapport["aandacht"])


# ---------------------------------------------------------------------------
# de vier tellers  ->  GET /api/directie/dashboard
# ---------------------------------------------------------------------------


async def test_dashboard_levert_de_vier_tellers(client, sessie, bedrijf, zaterdag):
    await maak_medewerker(sessie, "Sanne", functies=["bediening"], dagen=["za"])
    shift = await maak_shift(sessie, bedrijf, datum=zaterdag)
    await MatchingAgent().match_shift(sessie, shift)
    await _maak_beslissing(sessie)

    cijfers = (await client.get("/api/directie/dashboard")).json()
    assert set(cijfers) == {
        "actiesVandaag",
        "nieuweMatches",
        "aanmeldingenVandaag",
        "openBeslissingen",
    }
    assert all(isinstance(v, int) for v in cijfers.values())
    assert cijfers["nieuweMatches"] == 1
    assert cijfers["openBeslissingen"] == 1
    assert cijfers["actiesVandaag"] >= 1


# ---------------------------------------------------------------------------
# Matching-endpoints
# ---------------------------------------------------------------------------


async def test_matching_run_vult_shifts_en_logt(client, sessie, bedrijf, zaterdag):
    await maak_medewerker(sessie, "Daan", functies=["bediening"], dagen=["za"])
    await maak_shift(sessie, bedrijf, datum=zaterdag)

    antwoord = await client.post("/api/matching/run")
    assert antwoord.status_code == 200
    assert antwoord.json()["shifts"][0]["gematcht"] == ["Daan"]

    regels = (await client.get("/api/directie/activiteiten")).json()
    assert any(r["afdeling"] == "matching" for r in regels)


async def test_no_show_endpoint_geeft_twee_afdelingen_in_het_log(
    client, sessie, bedrijf, zaterdag
):
    await maak_medewerker(sessie, "Milan", functies=["bediening"], dagen=["za"])
    await maak_shift(sessie, bedrijf, datum=zaterdag)
    await client.post("/api/matching/run")
    match = (await sessie.execute(select(Match))).scalars().one()

    antwoord = await client.post(f"/api/matching/matches/{match.id}/no-show")
    assert antwoord.status_code == 200

    regels = (await client.get("/api/directie/activiteiten")).json()
    afdelingen = {r["afdeling"] for r in regels}
    assert {"matching", "support"} <= afdelingen


async def test_urengeschil_endpoint_maakt_tier3_beslissing(
    client, sessie, bedrijf, zaterdag
):
    await maak_medewerker(sessie, "Noor", functies=["bediening"], dagen=["za"])
    await maak_shift(sessie, bedrijf, datum=zaterdag)
    await client.post("/api/matching/run")
    match = (await sessie.execute(select(Match))).scalars().one()

    antwoord = await client.post(
        f"/api/matching/matches/{match.id}/urengeschil",
        json={"uren_medewerker": 8, "uren_bedrijf": 6},
    )
    assert antwoord.status_code == 200

    body = (await client.get("/api/directie/beslissingen")).json()
    assert body["open"][0]["tier"] == 3
    assert body["open"][0]["urgentie"] == "dringend"
