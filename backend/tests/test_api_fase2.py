"""API-tests voor de Support- en Financieel-endpoints."""

from __future__ import annotations

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.api import directie as directie_api
from app.api import financieel as financieel_api
from app.api import matching as matching_api
from app.api import support as support_api
from app.core.domein import BerichtStatus
from app.db.models import Bericht, Kennisbankitem, Match
from app.db.session import get_sessie
from tests.conftest import maak_medewerker, maak_shift


@pytest_asyncio.fixture
async def client(sessie):
    from fastapi import FastAPI

    app = FastAPI()
    for router in (
        directie_api.router,
        matching_api.router,
        support_api.router,
        financieel_api.router,
    ):
        app.include_router(router)

    async def _sessie_override():
        yield sessie

    app.dependency_overrides[get_sessie] = _sessie_override
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


async def _kennisbank(sessie):
    item = Kennisbankitem(
        vraag="Hoe meld ik me af voor een shift?",
        antwoord="Afmelden doe je in de app bij 'Mijn shifts'.",
        trefwoorden=["afmelden", "afzeggen"],
        categorie="shifts",
    )
    sessie.add(item)
    await sessie.flush()
    return item


# ---------------------------------------------------------------------------
# Support
# ---------------------------------------------------------------------------


async def test_vraag_endpoint_beantwoordt(client, sessie):
    await _kennisbank(sessie)
    medewerker = await maak_medewerker(sessie, "Sanne", functies=["bar"], dagen=["za"])

    antwoord = await client.post(
        "/api/support/vragen",
        json={"vraag": "Hoe kan ik me afmelden?", "medewerker_id": medewerker.id},
    )

    assert antwoord.status_code == 200
    assert antwoord.json()["uitkomst"] == "beantwoord"


async def test_vraag_endpoint_escaleert_en_maakt_beslissing(client, sessie):
    await _kennisbank(sessie)
    medewerker = await maak_medewerker(sessie, "Milan", functies=["bar"], dagen=["za"])

    antwoord = await client.post(
        "/api/support/vragen",
        json={"vraag": "Ik heb een klacht over het bedrijf", "medewerker_id": medewerker.id},
    )
    assert antwoord.json()["uitkomst"] == "geescaleerd"

    body = (await client.get("/api/directie/beslissingen")).json()
    assert body["open"][0]["afdelingBron"] == "support"
    assert body["open"][0]["tier"] == 3


async def test_onbekende_medewerker_geeft_404(client):
    antwoord = await client.post(
        "/api/support/vragen", json={"vraag": "Hallo?", "medewerker_id": 999}
    )
    assert antwoord.status_code == 404


async def test_outbox_toont_de_volledige_tekst(client, sessie):
    medewerker = await maak_medewerker(sessie, "Noor", functies=["bar"], dagen=["za"])
    await client.post("/api/support/onboarding", json={"medewerker_id": medewerker.id})

    berichten = (await client.get("/api/support/berichten")).json()

    assert len(berichten) == 1
    bericht = berichten[0]
    assert bericht["sjabloon"] == "onboarding"
    assert bericht["ontvanger"] == "Noor"
    assert bericht["status"] == "klaar"
    assert "Welkom bij WOSZ" in bericht["inhoud"]


async def test_bericht_markeren_als_verstuurd(client, sessie):
    medewerker = await maak_medewerker(sessie, "Daan", functies=["bar"], dagen=["za"])
    await client.post("/api/support/onboarding", json={"medewerker_id": medewerker.id})
    bericht = (await sessie.execute(select(Bericht))).scalars().one()

    antwoord = await client.post(f"/api/support/berichten/{bericht.id}/verstuurd")

    assert antwoord.status_code == 200
    assert antwoord.json()["status"] == str(BerichtStatus.VERSTUURD)
    # Standaard toont de outbox alleen wat nog klaarstaat.
    assert (await client.get("/api/support/berichten")).json() == []


async def test_sjablonenoverzicht_toont_alles_wat_support_kan_sturen(client):
    sjablonen = (await client.get("/api/support/sjablonen")).json()

    namen = {s["naam"] for s in sjablonen}
    assert {"onboarding", "no_show_waarschuwing", "vraag_doorgezet"} <= namen
    for sjabloon in sjablonen:
        assert set(sjabloon) == {"naam", "kanaal", "onderwerp", "body", "variabelen"}
        assert "€" not in sjabloon["body"]


# ---------------------------------------------------------------------------
# Financieel
# ---------------------------------------------------------------------------


async def test_facturen_verschijnen_na_geboekte_uren(client, sessie, bedrijf, zaterdag):
    await maak_medewerker(sessie, "Sanne", functies=["bediening"], dagen=["za"])
    await maak_shift(sessie, bedrijf, datum=zaterdag)
    await client.post("/api/matching/run")
    match = (await sessie.execute(select(Match))).scalars().one()

    await client.post(f"/api/matching/matches/{match.id}/uren", json={"uren": 6})

    facturen = (await client.get("/api/financieel/facturen")).json()
    assert len(facturen) == 1
    assert facturen[0]["bedrijf"] == "Strandtent Zuid"
    assert facturen[0]["uren"] == 6.0
    assert facturen[0]["bedragEur"] == 12.0
    assert facturen[0]["status"] == "concept"


async def test_periode_afsluiten(client, sessie, bedrijf, zaterdag):
    await maak_medewerker(sessie, "Sanne", functies=["bediening"], dagen=["za"])
    shift = await maak_shift(sessie, bedrijf, datum=zaterdag)
    await client.post("/api/matching/run")
    match = (await sessie.execute(select(Match))).scalars().one()
    await client.post(f"/api/matching/matches/{match.id}/uren", json={"uren": 6})

    periode = shift.datum.strftime("%Y-%m")
    antwoord = await client.post(f"/api/financieel/periodes/{periode}/afsluiten")

    assert antwoord.status_code == 200
    assert antwoord.json()["facturen"][0]["uren"] == 6.0

    facturen = (await client.get("/api/financieel/facturen")).json()
    assert facturen[0]["status"] == "klaar-ter-goedkeuring"


async def test_uitbetaalroutes_zijn_uitsluitend_administratief(client):
    """De API kent precies drie uitbetalingsroutes, en geen ervan betaalt uit.

    Een nieuwe route die met uitbetalingen te maken heeft, laat deze test falen.
    Dat is de bedoeling: er hoort iemand naar te kijken voordat er een vierde
    bijkomt, want dit is het gebied waar geld de deur uit zou kunnen gaan.
    """
    from app.main import app as volledige_app

    paden = set(volledige_app.openapi()["paths"])
    uitbetaalroutes = {p for p in paden if "uitbetaling" in p.lower()}

    assert uitbetaalroutes == {
        "/api/directie/uitbetalingen",  # lijst bekijken
        "/api/directie/uitbetalingen/export",  # werklijst downloaden
        "/api/directie/uitbetalingen/{opdracht_id}/voldaan",  # achteraf afvinken
    }

    # En geen enkele route draagt een naam die op zelf betalen duidt.
    verdacht = [
        p
        for p in paden
        if any(term in p.lower() for term in ("payout", "transfer", "overboek", "payment"))
    ]
    assert verdacht == [], f"Onverwachte betaalroute(s): {verdacht}"
