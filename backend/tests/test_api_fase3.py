"""API-tests voor de Marketing-endpoints."""

from __future__ import annotations

from datetime import timedelta

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.api import directie as directie_api
from app.api import marketing as marketing_api
from app.core.domein import nu
from app.db.models import Campagne, Hoek
from app.db.session import get_sessie


@pytest_asyncio.fixture
async def client(sessie):
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(marketing_api.router)
    app.include_router(directie_api.router)

    async def _sessie_override():
        yield sessie

    app.dependency_overrides[get_sessie] = _sessie_override
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def hoek(sessie) -> Hoek:
    h = Hoek(
        naam="Geen zzp-gedoe",
        omschrijving="Werken zonder KvK-gedoe.",
        toon="Nuchter.",
        voorbeelden=["Geen KvK, geen facturen, geen gedoe."],
        goedgekeurd=True,
    )
    sessie.add(h)
    await sessie.flush()
    return h


@pytest_asyncio.fixture
async def campagnes(sessie, hoek) -> tuple[Campagne, Campagne]:
    a = Campagne(naam="Geen zzp-gedoe", hoek_id=hoek.id, dagbudget_cent=2500)
    b = Campagne(naam="Vrienden-bonus", hoek_id=hoek.id, dagbudget_cent=1500)
    sessie.add_all([a, b])
    await sessie.flush()
    return a, b


async def test_kalender_toont_geplande_items(client, hoek):
    await client.post("/api/marketing/kalender/weekplanning?aantal=2")

    items = (await client.get("/api/marketing/kalender")).json()

    assert len(items) == 2
    item = items[0]
    assert set(item) == {
        "id",
        "geplandeDatum",
        "kanaal",
        "hoek",
        "haak",
        "concepttekst",
        "aanleiding",
        "status",
        "doorLlm",
    }
    assert item["hoek"] == "Geen zzp-gedoe"
    assert item["status"] == "gepland"


async def test_plannen_op_niet_goedgekeurde_hoek_geeft_409(client, sessie):
    hoek = Hoek(naam="Experiment", goedgekeurd=False)
    sessie.add(hoek)
    await sessie.flush()

    antwoord = await client.post(
        "/api/marketing/kalender",
        json={
            "hoek_id": hoek.id,
            "geplande_datum": (nu().date() + timedelta(days=1)).isoformat(),
        },
    )
    assert antwoord.status_code == 409


async def test_item_markeren_als_gepubliceerd(client, hoek):
    await client.post("/api/marketing/kalender/weekplanning?aantal=1")
    item_id = (await client.get("/api/marketing/kalender")).json()[0]["id"]

    antwoord = await client.post(f"/api/marketing/kalender/{item_id}/gepubliceerd")

    assert antwoord.status_code == 200
    assert antwoord.json()["status"] == "gepubliceerd"


async def test_campagnes_tonen_de_bandbreedte(client, campagnes):
    lijst = (await client.get("/api/marketing/campagnes")).json()

    assert len(lijst) == 2
    campagne = lijst[0]
    assert campagne["dagbudgetEur"] == 25.0
    assert campagne["bandbreedtePct"] == 20.0
    assert campagne["maxVerschuivingEur"] == 5.0  # 20% van €25


async def test_verschuiving_binnen_bandbreedte_lukt(client, campagnes):
    antwoord = await client.post(
        "/api/marketing/campagnes/budget/verschuiven",
        json={
            "van_campagne_id": campagnes[1].id,
            "naar_campagne_id": campagnes[0].id,
            "bedrag_eur": 3.0,
            "reden": "presteert beter",
        },
    )
    assert antwoord.status_code == 200

    lijst = (await client.get("/api/marketing/campagnes")).json()
    totaal = sum(c["dagbudgetEur"] for c in lijst)
    assert totaal == 40.0  # ongewijzigd


async def test_verschuiving_boven_bandbreedte_geeft_409(client, campagnes):
    antwoord = await client.post(
        "/api/marketing/campagnes/budget/verschuiven",
        json={
            "van_campagne_id": campagnes[1].id,
            "naar_campagne_id": campagnes[0].id,
            "bedrag_eur": 10.0,
            "reden": "te veel",
        },
    )
    assert antwoord.status_code == 409
    assert "bandbreedte" in antwoord.json()["detail"]


async def test_budgetverhoging_maakt_tier3_beslissing(client, campagnes):
    antwoord = await client.post(
        "/api/marketing/campagnes/budget/verhogen",
        json={
            "campagne_id": campagnes[0].id,
            "extra_eur": 10.0,
            "reden": "werving loopt achter",
        },
    )
    assert antwoord.status_code == 200

    body = (await client.get("/api/directie/beslissingen")).json()
    assert body["open"][0]["afdelingBron"] == "marketing"
    assert body["open"][0]["tier"] == 3


async def test_budgetmutaties_zijn_een_werklijst(client, campagnes):
    await client.post(
        "/api/marketing/campagnes/budget/verschuiven",
        json={
            "van_campagne_id": campagnes[1].id,
            "naar_campagne_id": campagnes[0].id,
            "bedrag_eur": 2.0,
            "reden": "test",
        },
    )

    mutaties = (await client.get("/api/marketing/budgetmutaties")).json()
    assert len(mutaties) == 1
    assert mutaties[0]["status"] == "klaar-voor-uitvoering"
    assert mutaties[0]["vanCampagne"] == "Vrienden-bonus"
    assert mutaties[0]["naarCampagne"] == "Geen zzp-gedoe"

    await client.post(f"/api/marketing/budgetmutaties/{mutaties[0]['id']}/doorgevoerd")
    assert (await client.get("/api/marketing/budgetmutaties")).json() == []


async def test_resultaten_registreren_en_beoordelen(client, sessie, campagnes):
    goed = campagnes[0]
    goed.verwachte_kosten_per_aanmelding_cent = 450
    await sessie.flush()
    gisteren = (nu().date() - timedelta(days=1)).isoformat()

    await client.post(
        "/api/marketing/resultaten",
        json={
            "campagne_id": goed.id,
            "datum": gisteren,
            "uitgaven_eur": 20.0,
            "aanmeldingen": 2,
        },
    )

    antwoord = await client.post(f"/api/marketing/resultaten/beoordelen?datum={gisteren}")

    bevinding = antwoord.json()["bevindingen"][0]
    assert bevinding["afwijking_pct"] > 25
    assert bevinding["beslissing_id"] is not None


async def test_marketingroutes_liggen_vast(client):
    """De API kent precies deze marketingroutes, en geen ervan publiceert.

    Een nieuwe route laat deze test falen. Dat is de bedoeling: dit is het
    gebied waar iets namens WOSZ naar buiten zou kunnen gaan, dus er hoort
    iemand naar te kijken voordat er een bijkomt.

    Let op ``/gepubliceerd``: dat is geen publicatie-actie maar een afvinkje
    achteraf, net als ``/voldaan`` bij de uitbetalingen. Het systeem plaatst
    geen posts — het legt vast dat Sebas dat gedaan heeft.
    """
    from app.main import app as volledige_app

    paden = set(volledige_app.openapi()["paths"])
    marketingroutes = {p for p in paden if p.startswith("/api/marketing")}

    assert marketingroutes == {
        "/api/marketing/kalender",
        "/api/marketing/kalender/weekplanning",
        "/api/marketing/kalender/{item_id}/gepubliceerd",
        "/api/marketing/kalender/{item_id}/afwijzen",
        "/api/marketing/campagnes",
        "/api/marketing/campagnes/budget/verschuiven",
        "/api/marketing/campagnes/budget/verhogen",
        "/api/marketing/budgetmutaties",
        "/api/marketing/budgetmutaties/{mutatie_id}/doorgevoerd",
        "/api/marketing/hoeken/voorstellen",
        "/api/marketing/resultaten",
        "/api/marketing/resultaten/beoordelen",
    }
