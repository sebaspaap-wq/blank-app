"""Tests die voorkomen dat het bedrijf per ongeluk iets doms doet.

Draaien met:  uv run python -m pytest tests -q   (of: python -m pytest tests -q)
"""

from __future__ import annotations

import pytest

from quitter.catalog import EXTRAS, PROGRAMMAS, KOSTEN, product
from quitter.compliance import controleer, is_publiceerbaar, moet_escaleren
from quitter.finance import break_even_orders, gemiddelde_orderwaarde, max_cac
from quitter.paths import veilig_pad
from quitter.taper import (
    MAX_STUKS_PER_DAG,
    PROGRAMMA_DAGEN,
    SCHEMAS,
    bepaal_programma,
)


# --- het afbouwschema mag nooit stiekem omhoog lopen ---------------------

@pytest.mark.parametrize("sleutel", list(SCHEMAS))
def test_schema_loopt_alleen_omlaag(sleutel):
    doses = [b.sterkte_mg * b.stuks_per_dag for b in SCHEMAS[sleutel].blokken]
    assert doses == sorted(doses, reverse=True), f"{sleutel} gaat ergens omhoog"


@pytest.mark.parametrize("sleutel", list(SCHEMAS))
def test_schema_blijft_binnen_de_maximumdosering(sleutel):
    for blok in SCHEMAS[sleutel].blokken:
        assert blok.stuks_per_dag <= MAX_STUKS_PER_DAG[blok.sterkte_mg]


@pytest.mark.parametrize("sleutel", list(SCHEMAS))
def test_schema_duurt_precies_negentig_dagen(sleutel):
    schema = SCHEMAS[sleutel]
    assert sum(b.stuks_totaal for b in schema.blokken) == schema.totaal_stuks()
    assert len(schema.alle_dagen()) == PROGRAMMA_DAGEN
    assert schema.dagplan(PROGRAMMA_DAGEN)["laatste_dag"] is True


def test_schema_eindigt_laag():
    # Het laatste blok moet altijd de laagste sterkte en het laagste aantal hebben.
    for sleutel, schema in SCHEMAS.items():
        laatste = schema.blokken[-1]
        assert laatste.sterkte_mg == 2, sleutel
        assert laatste.stuks_per_dag <= 3, sleutel


def test_zwaarder_programma_bevat_meer_nicotine():
    licht = SCHEMAS["licht"].totaal_nicotine_mg()
    standaard = SCHEMAS["standaard"].totaal_nicotine_mg()
    zwaar = SCHEMAS["zwaar"].totaal_nicotine_mg()
    assert licht < standaard < zwaar


def test_zelftest_stuurt_zware_roker_naar_het_zware_programma():
    sleutel, _ = bepaal_programma({"aantal": 4, "eerste": 4, "nacht": 2, "pogingen": 2})
    assert sleutel == "zwaar"
    sleutel, _ = bepaal_programma({"aantal": 0, "eerste": 0, "nacht": 0, "pogingen": 0})
    assert sleutel == "licht"


# --- geld ---------------------------------------------------------------

@pytest.mark.parametrize("p", PROGRAMMAS, ids=[p.sku for p in PROGRAMMAS])
def test_elk_programma_is_winstgevend_voor_advertenties(p):
    assert p.marge() > 0, f"{p.sku} kost meer dan het opbrengt"
    assert p.marge_procent() > 0.30, f"{p.sku} houdt te weinig over om te kunnen adverteren"


def test_duurder_programma_levert_meer_op():
    marges = [p.marge() for p in sorted(PROGRAMMAS, key=lambda x: x.prijs)]
    assert marges == sorted(marges)


def test_extras_verliezen_geen_geld():
    for e in EXTRAS:
        assert e.marge > 0, f"{e.sku} levert niets op"


def test_break_even_wordt_onmogelijk_bij_te_dure_klanten():
    _, marge = gemiddelde_orderwaarde()
    assert break_even_orders(marge + 1) == float("inf")
    assert break_even_orders(10.0) < 20


def test_max_cac_is_lager_dan_de_marge():
    _, marge = gemiddelde_orderwaarde()
    assert max_cac(25.0) == pytest.approx(marge - 25.0)


def test_kostprijs_bevat_alle_posten():
    p = product("Q90-S")
    gum = KOSTEN.gum_kosten(p.schema)
    assert p.kostprijs() > gum + KOSTEN.verpakking() + KOSTEN.verzending


# --- wat er niet naar buiten mag ----------------------------------------

@pytest.mark.parametrize("tekst", [
    "Gegarandeerd rookvrij in 90 dagen.",
    "Volkomen veilig en zonder bijwerkingen.",
    "Artsen raden QUITTER aan.",
    "Gratis proefpakket voor de eerste 100 aanmeldingen.",
    "Ook geschikt voor jongeren die willen stoppen.",
    "Stop met roken en val meteen af.",
])
def test_verboden_claims_worden_geblokkeerd(tekst):
    assert not is_publiceerbaar(tekst), f"deze tekst glipt erdoor: {tekst}"


@pytest.mark.parametrize("tekst", [
    "Je bouwt in 90 dagen af van 4 mg naar 2 mg naar nul. Lees voor gebruik de bijsluiter.",
    "Zes blokken van vijftien dagen. Elke ochtend één mail met wat je die dag doet.",
    "Het blikje past in je broekzak, precies waar je pakje zat.",
])
def test_gewone_merkteksten_komen_erdoor(tekst):
    assert is_publiceerbaar(tekst), controleer(tekst)


@pytest.mark.parametrize("vraag", [
    "Ik ben zwanger, mag ik dit gebruiken?",
    "Ik gebruik bloeddrukmedicatie, kan dat samen?",
    "Mijn hond heeft een stuk opgegeten.",
    "Ik heb er twintig gekauwd en ben misselijk en duizelig.",
])
def test_medische_vragen_gaan_naar_een_mens(vraag):
    assert moet_escaleren(vraag), f"deze vraag wordt niet geëscaleerd: {vraag}"


def test_gewone_vraag_hoeft_niet_te_escaleren():
    assert moet_escaleren("Wanneer wordt mijn pakket bezorgd?") == []


# --- agents mogen niet buiten hun hok komen -----------------------------

def test_agent_mag_niet_buiten_de_werkmappen_schrijven():
    with pytest.raises(PermissionError):
        veilig_pad("quitter/brand.py", schrijven=True)
    with pytest.raises(PermissionError):
        veilig_pad("../geheim.txt", schrijven=True)
    assert veilig_pad("content/ads/test.md", schrijven=True).name == "test.md"


def test_agent_mag_de_documentatie_wel_lezen():
    assert veilig_pad("docs/05-financieel.md", schrijven=False).name == "05-financieel.md"
