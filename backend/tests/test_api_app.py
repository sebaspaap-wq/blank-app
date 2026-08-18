"""API-tests voor het medewerker- en het horecascherm.

Het gaat hier om twee dingen. Eén: geven de endpoints exact de velden terug die
de renderfuncties in wosz-app.html al gebruiken? Twee: blijft de belofte van het
levelsysteem overeind nu medewerkers zelf op shifts kunnen reageren — reageren
mag je vooraan in de rij zetten, maar het mag de levelvolgorde niet omzeilen.
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.api import horeca as horeca_api
from app.api import medewerker as medewerker_api
from app.core.domein import MatchStatus, ReactieStatus
from app.db.models import Bericht, Match, Reactie, Referral, Shift, User
from app.db.session import get_sessie
from tests.conftest import maak_medewerker, maak_shift


@pytest_asyncio.fixture
async def client(sessie):
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(medewerker_api.router)
    app.include_router(horeca_api.router)

    async def _sessie_override():
        yield sessie

    app.dependency_overrides[get_sessie] = _sessie_override
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


# ---------------------------------------------------------------------------
# Medewerker
# ---------------------------------------------------------------------------


async def test_aanmelden_stuurt_meteen_een_onboardingbericht(client, sessie):
    """Onboarding is geen losse knop maar hoort bij aanmelden."""
    antwoord = await client.post(
        "/api/medewerker/aanmelden",
        json={
            "naam": "Nova Bakker",
            "email": "nova@voorbeeld.nl",
            "functies": ["bediening"],
            "beschikbare_dagen": ["za", "zo"],
            "ervaring_jaren": 2,
            "gewenst_uurloon": "€13,50",
        },
    )
    assert antwoord.status_code == 201
    lichaam = antwoord.json()
    assert lichaam["naam"] == "Nova Bakker"
    assert lichaam["seizoenUren"] == 0

    berichten = (await sessie.execute(select(Bericht))).scalars().all()
    assert [b.sjabloon for b in berichten] == ["onboarding"]
    assert "Nova Bakker" in berichten[0].inhoud


async def test_aanmelden_met_bestaand_emailadres_wordt_geweigerd(client):
    invoer = {"naam": "Nova Bakker", "email": "nova@voorbeeld.nl"}
    assert (await client.post("/api/medewerker/aanmelden", json=invoer)).status_code == 201
    tweede = await client.post("/api/medewerker/aanmelden", json=invoer)
    assert tweede.status_code == 409


async def test_beschikbare_shifts_hebben_de_velden_die_de_frontend_leest(
    client, sessie, bedrijf, zaterdag
):
    medewerker = await maak_medewerker(
        sessie, "Sanne", functies=["bediening"], dagen=["za"]
    )
    shift = await maak_shift(sessie, bedrijf, datum=zaterdag, functie="bediening")
    shift.uurloon = "€13,00 – €14,50"
    await sessie.flush()

    antwoord = await client.get(f"/api/medewerker/{medewerker.id}/shifts/beschikbaar")
    assert antwoord.status_code == 200
    (kaart,) = antwoord.json()
    # shiftCardHtml() leest precies deze sleutels.
    assert set(kaart) == {"id", "role", "datum", "tijd", "plek", "uurloon"}
    assert kaart["role"] == "bediening"
    assert kaart["plek"] == "Strandtent Zuid"
    assert kaart["uurloon"] == "€13,00 – €14,50"
    assert kaart["datum"].startswith("Za ")


async def test_shifts_die_niet_bij_je_passen_worden_niet_getoond(
    client, sessie, bedrijf, zaterdag
):
    """Een shift tonen waarop de agent je nooit zou kiezen is een lege belofte."""
    kok = await maak_medewerker(sessie, "Milan", functies=["keuken"], dagen=["za"])
    await maak_shift(sessie, bedrijf, datum=zaterdag, functie="bediening")

    antwoord = await client.get(f"/api/medewerker/{kok.id}/shifts/beschikbaar")
    assert antwoord.json() == []


async def test_reageren_levert_geen_match_maar_een_reactie_op(
    client, sessie, bedrijf, zaterdag
):
    """De agent blijft degene die de plek toekent."""
    sterk = await maak_medewerker(
        sessie, "Sanne", functies=["bediening"], dagen=["za"], seizoen_uren=120
    )
    zwak = await maak_medewerker(
        sessie, "Milan", functies=["bediening"], dagen=["za"], seizoen_uren=4
    )
    shift = await maak_shift(sessie, bedrijf, datum=zaterdag, functie="bediening")

    # De medewerker met de minste uren klikt als eerste.
    antwoord = await client.post(
        f"/api/medewerker/{zwak.id}/shifts/{shift.id}/reageer"
    )
    assert antwoord.status_code == 200

    reacties = (await sessie.execute(select(Reactie))).scalars().all()
    assert len(reacties) == 1
    assert reacties[0].medewerker_id == zwak.id

    # Hij krijgt de shift, want hij is de enige die gereageerd heeft — niet
    # omdat er een match langs de agent heen is geschreven.
    matches = (await sessie.execute(select(Match))).scalars().all()
    assert [m.medewerker_id for m in matches] == [zwak.id]
    assert matches[0].onderbouwing and "gereageerd" in matches[0].onderbouwing.lower()
    assert sterk.id not in {m.medewerker_id for m in matches}


async def test_binnen_de_reacties_wint_nog_steeds_het_hoogste_level(
    client, sessie, bedrijf, zaterdag
):
    """Reageren zet je vooraan in de rij, het zet de rij niet op zijn kop."""
    sterk = await maak_medewerker(
        sessie, "Sanne", functies=["bediening"], dagen=["za"], seizoen_uren=120
    )
    zwak = await maak_medewerker(
        sessie, "Milan", functies=["bediening"], dagen=["za"], seizoen_uren=4
    )
    shift = await maak_shift(sessie, bedrijf, datum=zaterdag, functie="bediening")

    sessie.add(Reactie(shift_id=shift.id, medewerker_id=zwak.id))
    await sessie.flush()

    await client.post(f"/api/medewerker/{sterk.id}/shifts/{shift.id}/reageer")

    matches = (await sessie.execute(select(Match))).scalars().all()
    assert [m.medewerker_id for m in matches] == [sterk.id]


async def test_reactie_wordt_gehonoreerd_bij_de_match(client, sessie, bedrijf, zaterdag):
    medewerker = await maak_medewerker(
        sessie, "Sanne", functies=["bediening"], dagen=["za"]
    )
    shift = await maak_shift(sessie, bedrijf, datum=zaterdag, functie="bediening")

    await client.post(f"/api/medewerker/{medewerker.id}/shifts/{shift.id}/reageer")

    reactie = (await sessie.execute(select(Reactie))).scalars().one()
    assert reactie.status == str(ReactieStatus.GEHONOREERD)


async def test_reageren_op_een_volle_shift_wordt_geweigerd(
    client, sessie, bedrijf, zaterdag
):
    eerste = await maak_medewerker(
        sessie, "Sanne", functies=["bediening"], dagen=["za"], seizoen_uren=100
    )
    tweede = await maak_medewerker(
        sessie, "Milan", functies=["bediening"], dagen=["za"], seizoen_uren=10
    )
    shift = await maak_shift(sessie, bedrijf, datum=zaterdag, functie="bediening")

    await client.post(f"/api/medewerker/{eerste.id}/shifts/{shift.id}/reageer")
    tweede_poging = await client.post(
        f"/api/medewerker/{tweede.id}/shifts/{shift.id}/reageer"
    )
    assert tweede_poging.status_code == 409


async def test_geschorste_medewerker_kan_niet_reageren(client, sessie, bedrijf, zaterdag):
    medewerker = await maak_medewerker(
        sessie, "Sanne", functies=["bediening"], dagen=["za"]
    )
    medewerker.geschorst = True
    await sessie.flush()
    shift = await maak_shift(sessie, bedrijf, datum=zaterdag, functie="bediening")

    antwoord = await client.post(
        f"/api/medewerker/{medewerker.id}/shifts/{shift.id}/reageer"
    )
    assert antwoord.status_code == 409
    assert (await sessie.execute(select(Reactie))).scalars().all() == []


async def test_annuleren_geeft_de_plek_terug_aan_de_volgende(
    client, sessie, bedrijf, zaterdag
):
    """Een afzegging blijft niet liggen tot de volgende matchronde."""
    eerste = await maak_medewerker(
        sessie, "Sanne", functies=["bediening"], dagen=["za"], seizoen_uren=100
    )
    tweede = await maak_medewerker(
        sessie, "Milan", functies=["bediening"], dagen=["za"], seizoen_uren=10
    )
    shift = await maak_shift(sessie, bedrijf, datum=zaterdag, functie="bediening")

    await client.post(f"/api/medewerker/{eerste.id}/shifts/{shift.id}/reageer")
    match = (await sessie.execute(select(Match))).scalars().one()

    antwoord = await client.post(
        f"/api/medewerker/{eerste.id}/matches/{match.id}/annuleer"
    )
    assert antwoord.status_code == 200
    assert antwoord.json()["aankomend"] == []

    matches = (await sessie.execute(select(Match))).scalars().all()
    statussen = {m.medewerker_id: m.status for m in matches}
    assert statussen[eerste.id] == str(MatchStatus.GEANNULEERD)
    assert statussen[tweede.id] == str(MatchStatus.BEVESTIGD)


async def test_je_kunt_de_shift_van_een_ander_niet_annuleren(
    client, sessie, bedrijf, zaterdag
):
    eigenaar = await maak_medewerker(
        sessie, "Sanne", functies=["bediening"], dagen=["za"]
    )
    ander = await maak_medewerker(sessie, "Milan", functies=["bediening"], dagen=["za"])
    shift = await maak_shift(sessie, bedrijf, datum=zaterdag, functie="bediening")

    await client.post(f"/api/medewerker/{eigenaar.id}/shifts/{shift.id}/reageer")
    match = (await sessie.execute(select(Match))).scalars().one()

    antwoord = await client.post(f"/api/medewerker/{ander.id}/matches/{match.id}/annuleer")
    assert antwoord.status_code == 404


async def test_uren_doorgeven_werkt_het_level_bij(client, sessie, bedrijf):
    medewerker = await maak_medewerker(
        sessie, "Sanne", functies=["bediening"], dagen=["za"], seizoen_uren=20
    )
    gisteren = date.today() - timedelta(days=1)
    shift = await maak_shift(sessie, bedrijf, datum=gisteren, functie="bediening")
    match = Match(
        shift_id=shift.id, medewerker_id=medewerker.id, status=str(MatchStatus.BEVESTIGD)
    )
    sessie.add(match)
    await sessie.flush()

    antwoord = await client.post(
        f"/api/medewerker/{medewerker.id}/matches/{match.id}/uren", json={"uren": 6}
    )
    assert antwoord.status_code == 200

    scherm = (await client.get(f"/api/medewerker/{medewerker.id}")).json()
    assert scherm["seizoenUren"] == 26
    # Een shift van gisteren hoort in de geschiedenis, niet in aankomend.
    assert scherm["aankomend"] == []
    assert scherm["geschiedenis"][0]["uren"] == 6


async def test_vriend_uitnodigen_maakt_een_referral_zonder_actief_account(
    client, sessie
):
    """Een uitnodiging mag nooit per ongeluk ingepland worden."""
    aanmelding = await client.post(
        "/api/medewerker/aanmelden", json={"naam": "Sanne de Vries"}
    )
    sanne_id = aanmelding.json()["id"]

    antwoord = await client.post(
        f"/api/medewerker/{sanne_id}/vrienden",
        json={"naam": "Tom Hendriks", "email": "tom@voorbeeld.nl"},
    )
    assert antwoord.status_code == 201
    assert antwoord.json() == [{"naam": "Tom Hendriks", "uren": 0.0, "status": "Bezig"}]

    tom = (
        (await sessie.execute(select(User).where(User.naam == "Tom Hendriks")))
        .scalars()
        .one()
    )
    assert tom.actief is False


async def test_aanmelden_na_een_uitnodiging_verhuist_de_referral(client, sessie):
    """Anders loopt de bonus mee met een account dat nooit uren maakt."""
    aanmelding = await client.post(
        "/api/medewerker/aanmelden", json={"naam": "Sanne de Vries"}
    )
    sanne_id = aanmelding.json()["id"]
    await client.post(
        f"/api/medewerker/{sanne_id}/vrienden",
        json={"naam": "Tom Hendriks", "email": "tom@voorbeeld.nl"},
    )

    echt = await client.post(
        "/api/medewerker/aanmelden",
        json={"naam": "Tom Hendriks", "email": "tom@voorbeeld.nl"},
    )
    assert echt.status_code == 201
    tom_id = echt.json()["id"]

    referral = (await sessie.execute(select(Referral))).scalars().one()
    assert referral.vriend_id == tom_id

    accounts = (
        (await sessie.execute(select(User).where(User.naam == "Tom Hendriks")))
        .scalars()
        .all()
    )
    assert len(accounts) == 1


# ---------------------------------------------------------------------------
# Horeca
# ---------------------------------------------------------------------------


async def test_aanvraag_plaatsen_matcht_meteen(client, sessie, bedrijf, zaterdag):
    """Geen gesimuleerde reactie na drie seconden, maar een echte matchronde."""
    await maak_medewerker(
        sessie, "Sanne", functies=["bediening"], dagen=["za"], seizoen_uren=60
    )

    antwoord = await client.post(
        f"/api/horeca/{bedrijf.id}/aanvragen",
        json={
            "functie": "bediening",
            "datum": zaterdag.isoformat(),
            "tijd": "17:00-01:00",
            "aantal": 1,
            "uurloon": "€13,50",
        },
    )
    assert antwoord.status_code == 201
    (aanvraag,) = antwoord.json()["aanvragen"]
    assert aanvraag["gematcht"] == 1
    assert aanvraag["gevraagd"] == 1
    assert aanvraag["uurloon"] == "€13,50"

    shift = (await sessie.execute(select(Shift))).scalars().one()
    assert shift.duur_uren == 8.0  # 17:00-01:00 loopt door na middernacht


async def test_aanvraag_met_datum_in_woorden(client, bedrijf):
    """Het datumveld is vrije tekst met 'bv. Za 23 aug' als voorbeeld."""
    doel = date.today() + timedelta(days=10)
    tekst = f"{doel.day} {['jan','feb','mrt','apr','mei','jun','jul','aug','sep','okt','nov','dec'][doel.month - 1]}"

    antwoord = await client.post(
        f"/api/horeca/{bedrijf.id}/aanvragen",
        json={"functie": "bar", "datum": tekst, "tijd": "18:00-00:00", "aantal": 1},
    )
    assert antwoord.status_code == 201
    (aanvraag,) = antwoord.json()["aanvragen"]
    assert aanvraag["datum"].endswith(tekst)


async def test_onleesbare_datum_wordt_geweigerd_en_niet_stil_op_vandaag_gezet(
    client, sessie, bedrijf
):
    antwoord = await client.post(
        f"/api/horeca/{bedrijf.id}/aanvragen",
        json={"functie": "bar", "datum": "volgende week ofzo", "tijd": "18:00-00:00"},
    )
    assert antwoord.status_code == 422
    assert (await sessie.execute(select(Shift))).scalars().all() == []


async def test_datum_in_het_verleden_wordt_geweigerd(client, bedrijf):
    gisteren = (date.today() - timedelta(days=1)).isoformat()
    antwoord = await client.post(
        f"/api/horeca/{bedrijf.id}/aanvragen",
        json={"functie": "bar", "datum": gisteren, "tijd": "18:00-00:00"},
    )
    assert antwoord.status_code == 422


async def test_kandidaten_hebben_de_velden_die_de_frontend_leest(
    client, sessie, bedrijf, zaterdag
):
    kandidaat = await maak_medewerker(
        sessie, "Sanne de Vries", functies=["bediening", "bar"], dagen=["za"]
    )
    kandidaat.ervaring_jaren = 2
    kandidaat.gewenst_uurloon = "€13,50"
    await sessie.flush()

    # Twee plekken, één kandidaat: er blijft er een over om te tonen.
    await maak_shift(sessie, bedrijf, datum=zaterdag, functie="bediening", aantal=2)

    antwoord = await client.get(f"/api/horeca/{bedrijf.id}")
    (aanvraag,) = antwoord.json()["aanvragen"]
    (k,) = aanvraag["kandidaten"]
    assert set(k) == {"medewerkerId", "naam", "info", "wens"}
    assert k["naam"] == "Sanne de Vries"
    assert k["info"] == "2 jaar ervaring · Bediening, Bar"
    assert k["wens"] == "€13,50"


async def test_bedrijf_kan_zelf_een_kandidaat_accepteren(
    client, sessie, bedrijf, zaterdag
):
    weinig_uren = await maak_medewerker(
        sessie, "Milan", functies=["bediening"], dagen=["za"], seizoen_uren=5
    )
    await maak_medewerker(
        sessie, "Sanne", functies=["bediening"], dagen=["za"], seizoen_uren=90
    )
    shift = await maak_shift(sessie, bedrijf, datum=zaterdag, functie="bediening", aantal=2)

    antwoord = await client.post(
        f"/api/horeca/{bedrijf.id}/aanvragen/{shift.id}/kandidaten/{weinig_uren.id}"
    )
    assert antwoord.status_code == 200

    matches = (await sessie.execute(select(Match))).scalars().all()
    assert [m.medewerker_id for m in matches] == [weinig_uren.id]
    assert "zelf gekozen" in (matches[0].onderbouwing or "").lower()


async def test_kandidaat_van_een_ander_bedrijf_accepteren_kan_niet(
    client, sessie, bedrijf, zaterdag
):
    from app.db.models import Bedrijf

    ander = Bedrijf(naam="Beachclub Noord", plaats="Zandvoort")
    sessie.add(ander)
    await sessie.flush()

    medewerker = await maak_medewerker(
        sessie, "Sanne", functies=["bediening"], dagen=["za"]
    )
    shift = await maak_shift(sessie, bedrijf, datum=zaterdag, functie="bediening")

    antwoord = await client.post(
        f"/api/horeca/{ander.id}/aanvragen/{shift.id}/kandidaten/{medewerker.id}"
    )
    assert antwoord.status_code == 404


async def test_horecastats_tellen_echte_cijfers(client, sessie, bedrijf, zaterdag):
    medewerker = await maak_medewerker(
        sessie, "Sanne", functies=["bediening"], dagen=["za"]
    )
    open_shift = await maak_shift(
        sessie, bedrijf, datum=zaterdag, functie="bediening", aantal=2
    )
    # Bewust een datum in deze kalendermaand: de teller heet "uren deze maand",
    # en twee dagen terug kan op de 1e van de maand de vorige maand zijn.
    in_deze_maand = date.today().replace(day=1)
    gewerkt = await maak_shift(sessie, bedrijf, datum=in_deze_maand, functie="bediening")
    sessie.add(
        Match(
            shift_id=gewerkt.id,
            medewerker_id=medewerker.id,
            status=str(MatchStatus.GEWERKT),
            uren_gewerkt=6.0,
        )
    )
    await sessie.flush()

    stats = (await client.get(f"/api/horeca/{bedrijf.id}")).json()["stats"]
    assert set(stats) == {
        "actieveAanvragen",
        "gematchtDezeWeek",
        "urenDezeMaand",
        "gemiddeldeMatchtijdMinuten",
    }
    assert stats["actieveAanvragen"] == 1  # alleen de nog niet gevulde shift
    assert stats["urenDezeMaand"] == 6
    assert open_shift.id  # de openstaande aanvraag bestaat


async def test_onbekend_bedrijf_geeft_404(client):
    assert (await client.get("/api/horeca/9999")).status_code == 404


async def test_onbekende_medewerker_geeft_404(client):
    assert (await client.get("/api/medewerker/9999")).status_code == 404


@pytest.mark.parametrize(
    "rol", ["horeca", "directie"], ids=["horeca-account", "directie-account"]
)
async def test_een_niet_medewerker_krijgt_geen_medewerkerscherm(client, sessie, rol):
    """De id-ruimte is gedeeld; zonder rolcontrole zou je elkaars scherm zien."""
    gebruiker = User(naam="Iemand anders", rol=rol)
    sessie.add(gebruiker)
    await sessie.flush()

    assert (await client.get(f"/api/medewerker/{gebruiker.id}")).status_code == 404
