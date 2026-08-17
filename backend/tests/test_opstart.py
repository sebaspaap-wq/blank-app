"""Tests op het opstartpad: kan iemand dit systeem zonder voorkennis draaien?

Deze tests bewaken de route die in de README staat. Ze bestaan omdat er in die
route drie keer iets stil kapot bleek te zijn: een verkeerde database-URL, een
ontbrekende driver, en CORS-instellingen die het dashboard leeg lieten zonder
zichtbare foutmelding.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

from sqlalchemy import select

from app.db.models import Activiteit, Contentitem, Match

BACKEND = Path(__file__).resolve().parent.parent
ENV_VOORBEELD = BACKEND / ".env.example"
PYPROJECT = BACKEND / "pyproject.toml"

#: Poort waarop de README en het startscript het dashboard serveren.
DASHBOARD_POORT = 8090


def _env_waarden() -> dict[str, str]:
    waarden: dict[str, str] = {}
    for regel in ENV_VOORBEELD.read_text(encoding="utf-8").splitlines():
        regel = regel.strip()
        if not regel or regel.startswith("#") or "=" not in regel:
            continue
        sleutel, waarde = regel.split("=", 1)
        waarden[sleutel.strip()] = waarde.strip()
    return waarden


def test_env_voorbeeld_werkt_zonder_installatie():
    """``cp .env.example .env`` moet meteen werken, zonder database te installeren."""
    url = _env_waarden()["WOSZ_DATABASE_URL"]
    assert url.startswith("sqlite+aiosqlite:"), (
        f"De standaard database-URL is '{url}'. Wie .env.example kopieert krijgt "
        "dan meteen een verbindingsfout. Zet PostgreSQL in commentaar."
    )


def test_env_voorbeeld_heeft_geen_ingevulde_key():
    """Er hoort nooit een echte sleutel in dit bestand te staan."""
    assert _env_waarden()["ANTHROPIC_API_KEY"] == ""


def test_cors_laat_het_dashboard_erbij():
    """Het dashboard draait op een andere poort dan de API.

    Staat die poort er niet bij, dan laadt de pagina wel maar blijft hij leeg —
    de browser blokkeert de gegevens dan zonder zichtbare fout. Dat is precies
    de fout die deze test moet vangen.
    """
    origins = _env_waarden()["WOSZ_CORS_ORIGINS"]
    assert f":{DASHBOARD_POORT}" in origins, (
        f"WOSZ_CORS_ORIGINS is '{origins}' en bevat poort {DASHBOARD_POORT} niet. "
        "Het dashboard blijft dan leeg."
    )


def test_sqlite_driver_zit_in_de_gewone_installatie():
    """``uv pip install -e .`` moet genoeg zijn om te kunnen draaien.

    Zat aiosqlite alleen in de dev-extra, dan werkte de standaardinstallatie
    niet met de standaarddatabase.
    """
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    hoofddeps = " ".join(data["project"]["dependencies"])
    assert "aiosqlite" in hoofddeps, (
        "aiosqlite hoort bij de gewone dependencies: het is de driver voor de "
        "standaarddatabase uit .env.example."
    )


def test_startscripts_bestaan_en_zijn_uitvoerbaar():
    wortel = BACKEND.parent
    unix = wortel / "start.command"
    windows = wortel / "start-windows.bat"

    assert unix.exists(), "start.command ontbreekt"
    assert windows.exists(), "start-windows.bat ontbreekt"
    assert unix.stat().st_mode & 0o111, "start.command is niet uitvoerbaar (chmod +x)"


def test_startscript_gebruikt_dezelfde_poorten_als_de_cors_instelling():
    """Anders staat het dashboard weer stil zonder foutmelding."""
    script = (BACKEND.parent / "start.command").read_text(encoding="utf-8")
    assert f"DASHBOARD_POORT={DASHBOARD_POORT}" in script
    assert f":{DASHBOARD_POORT}" in _env_waarden()["WOSZ_CORS_ORIGINS"]


async def test_demo_vult_het_dashboard(sessie, bedrijf, zaterdag):
    """Na de demo-run staat er iets op het dashboard in plaats van nullen."""
    from app.db.demo import draai_demo
    from app.db.models import Hoek
    from tests.conftest import maak_medewerker, maak_shift

    await maak_medewerker(sessie, "Sanne", functies=["bediening"], dagen=["za"])
    await maak_shift(sessie, bedrijf, datum=zaterdag)
    sessie.add(
        Hoek(
            naam="Geen zzp-gedoe",
            omschrijving="Werken zonder KvK-gedoe.",
            voorbeelden=["Geen KvK, geen facturen, geen gedoe."],
            goedgekeurd=True,
        )
    )
    await sessie.flush()

    resultaat = await draai_demo(sessie)

    assert resultaat["gematcht"] == 1
    assert resultaat["posts"] >= 1
    assert (await sessie.execute(select(Match))).scalars().all()
    assert (await sessie.execute(select(Contentitem))).scalars().all()
    assert (await sessie.execute(select(Activiteit))).scalars().all()
