"""Tests voor de uitgaande kanalen.

De belangrijkste test in dit bestand is de laatste: agents mogen niets weten
van ``app.kanalen``. Ze schrijven naar de outbox en daar houdt hun rol op. Zou
die grens vervagen, dan zou een agent zelf kunnen versturen — en dan is "geen
toezeggingen naar buiten" weer een belofte in plaats van een eigenschap.
"""

from __future__ import annotations

import ast
from datetime import date, timedelta
from pathlib import Path

import pytest
from sqlalchemy import select

from app import kanalen
from app.config import Settings
from app.core.domein import BerichtStatus, ContentStatus, Kanaal, SocialKanaal
from app.db.models import Activiteit, Bericht, Contentitem, Hoek, User
from app.kanalen.basis import Kanaalfout, Post, Uitgaand, Verzendfout
from app.kanalen.console import ConsoleBerichtdriver, ConsoleSocialdriver
from app.kanalen.email import EmailBerichtdriver


class _Verzamelaar:
    """Driver die onthoudt wat hij zou versturen."""

    naam = "test"

    def __init__(self) -> None:
        self.verstuurd: list[Uitgaand] = []

    async def verstuur(self, uitgaand: Uitgaand) -> str:
        self.verstuurd.append(uitgaand)
        return "test-1"


class _Weigeraar:
    naam = "test"

    async def verstuur(self, _uitgaand: Uitgaand) -> str:
        raise Verzendfout("mailserver onbereikbaar")


async def _bericht(sessie, *, email: str | None = "sanne@voorbeeld.nl") -> Bericht:
    gebruiker = User(naam="Sanne de Vries", rol="medewerker", email=email)
    sessie.add(gebruiker)
    await sessie.flush()
    bericht = Bericht(
        kanaal=str(Kanaal.EMAIL),
        sjabloon="onboarding",
        ontvanger_user_id=gebruiker.id,
        ontvanger_naam=gebruiker.naam,
        onderwerp="Welkom bij WOSZ",
        inhoud="Hoi Sanne,\n\nWelkom bij WOSZ.",
        status=str(BerichtStatus.KLAAR),
    )
    sessie.add(bericht)
    await sessie.flush()
    return bericht


# ---------------------------------------------------------------------------
# Outbox
# ---------------------------------------------------------------------------


async def test_de_outbox_wordt_geleegd(sessie):
    bericht = await _bericht(sessie)
    driver = _Verzamelaar()

    verslag = await kanalen.verstuur_outbox(sessie, driver=driver)

    assert verslag == {"verstuurd": 1, "mislukt": 0}
    assert driver.verstuurd[0].ontvanger == "sanne@voorbeeld.nl"
    assert driver.verstuurd[0].onderwerp == "Welkom bij WOSZ"
    assert bericht.status == str(BerichtStatus.VERSTUURD)
    assert bericht.verstuurd_op is not None


async def test_een_verstuurd_bericht_gaat_niet_nog_een_keer(sessie):
    await _bericht(sessie)
    driver = _Verzamelaar()

    await kanalen.verstuur_outbox(sessie, driver=driver)
    tweede = await kanalen.verstuur_outbox(sessie, driver=driver)

    assert tweede == {"verstuurd": 0, "mislukt": 0}
    assert len(driver.verstuurd) == 1


async def test_een_mislukte_verzending_kost_geen_bericht(sessie):
    """Een mailserver die even plat ligt mag geen bericht laten verdwijnen."""
    bericht = await _bericht(sessie)

    verslag = await kanalen.verstuur_outbox(sessie, driver=_Weigeraar())

    assert verslag == {"verstuurd": 0, "mislukt": 1}
    assert bericht.status == str(BerichtStatus.KLAAR)

    # De volgende ronde lukt het wel.
    driver = _Verzamelaar()
    assert await kanalen.verstuur_outbox(sessie, driver=driver) == {
        "verstuurd": 1,
        "mislukt": 0,
    }


async def test_versturen_komt_in_het_activiteitenlog(sessie):
    await _bericht(sessie)
    await kanalen.verstuur_outbox(sessie, driver=_Verzamelaar())

    regels = (await sessie.execute(select(Activiteit))).scalars().all()
    assert any("verstuurd" in r.tekst for r in regels)


async def test_zonder_activiteit_geen_logregel(sessie):
    """Anders staat het log vol met 'nul berichten verstuurd'."""
    await kanalen.verstuur_outbox(sessie, driver=_Verzamelaar())
    assert (await sessie.execute(select(Activiteit))).scalars().all() == []


# ---------------------------------------------------------------------------
# Publiceren
# ---------------------------------------------------------------------------


async def _contentitem(sessie, *, dagen: int, status: ContentStatus) -> Contentitem:
    hoek = Hoek(naam="Geen zzp-gedoe", omschrijving="", toon="", voorbeelden=[])
    sessie.add(hoek)
    await sessie.flush()
    item = Contentitem(
        geplande_datum=date.today() + timedelta(days=dagen),
        kanaal=str(SocialKanaal.INSTAGRAM),
        hoek_id=hoek.id,
        haak="Geen KvK, geen gedoe.",
        concepttekst="Werken op het strand zonder papierwinkel.",
        status=str(status),
    )
    sessie.add(item)
    await sessie.flush()
    return item


class _Publicist:
    naam = "test"

    def __init__(self) -> None:
        self.posts: list[Post] = []

    async def publiceer(self, post: Post) -> str:
        self.posts.append(post)
        return "test-post-1"


async def test_content_van_vandaag_wordt_gepubliceerd(sessie):
    item = await _contentitem(sessie, dagen=0, status=ContentStatus.GEPLAND)
    driver = _Publicist()

    gepubliceerd = await kanalen.publiceer_geplande_posts(sessie, driver=driver)

    assert gepubliceerd == ["Geen KvK, geen gedoe."]
    assert item.status == str(ContentStatus.GEPUBLICEERD)
    assert item.gepubliceerd_op is not None
    assert driver.posts[0].tekst == "Werken op het strand zonder papierwinkel."


async def test_content_van_volgende_week_blijft_staan(sessie):
    item = await _contentitem(sessie, dagen=5, status=ContentStatus.GEPLAND)
    driver = _Publicist()

    assert await kanalen.publiceer_geplande_posts(sessie, driver=driver) == []
    assert item.status == str(ContentStatus.GEPLAND)
    assert driver.posts == []


async def test_een_voorstel_wordt_nooit_gepubliceerd(sessie):
    """Alleen wat op de kalender staat gaat eruit, niet wat nog ter beoordeling ligt."""
    item = await _contentitem(sessie, dagen=-1, status=ContentStatus.VOORSTEL)

    assert await kanalen.publiceer_geplande_posts(sessie, driver=_Publicist()) == []
    assert item.status == str(ContentStatus.VOORSTEL)


async def test_publiceren_komt_in_het_activiteitenlog(sessie):
    await _contentitem(sessie, dagen=0, status=ContentStatus.GEPLAND)
    await kanalen.publiceer_geplande_posts(sessie, driver=_Publicist())

    regels = (await sessie.execute(select(Activiteit))).scalars().all()
    assert any("gepubliceerd" in r.tekst for r in regels)


# ---------------------------------------------------------------------------
# Driverkeuze
# ---------------------------------------------------------------------------


def test_standaard_verstuurt_niets():
    """Een verse installatie mag nooit per ongeluk echte mensen mailen."""
    instellingen = Settings(WOSZ_DATABASE_URL="sqlite+aiosqlite:///:memory:")
    assert instellingen.bericht_driver == "console"
    assert instellingen.social_driver == "console"
    assert isinstance(kanalen.kies_berichtdriver(instellingen), ConsoleBerichtdriver)
    assert isinstance(kanalen.kies_socialdriver(instellingen), ConsoleSocialdriver)


def test_onbekend_kanaal_geeft_een_leesbare_fout():
    instellingen = Settings(WOSZ_BERICHT_DRIVER="duiven")
    with pytest.raises(Kanaalfout, match="console"):
        kanalen.kies_berichtdriver(instellingen)


def test_email_zonder_instellingen_start_niet():
    """Liever een fout bij het opstarten dan berichten die nergens aankomen."""
    instellingen = Settings(WOSZ_BERICHT_DRIVER="email")
    with pytest.raises(Kanaalfout, match="WOSZ_SMTP_HOST"):
        kanalen.kies_berichtdriver(instellingen)


def test_email_met_instellingen_start_wel():
    instellingen = Settings(
        WOSZ_BERICHT_DRIVER="email",
        WOSZ_SMTP_HOST="smtp.voorbeeld.nl",
        WOSZ_AFZENDER_EMAIL="hallo@wosz.nl",
    )
    assert isinstance(kanalen.kies_berichtdriver(instellingen), EmailBerichtdriver)


async def test_zonder_adres_wordt_er_niet_verstuurd(sessie):
    """Een bericht zonder ontvanger blijft klaarstaan in plaats van te verdwijnen."""
    await _bericht(sessie, email=None)
    driver = EmailBerichtdriver(
        Settings(WOSZ_SMTP_HOST="smtp.voorbeeld.nl", WOSZ_AFZENDER_EMAIL="hallo@wosz.nl")
    )

    verslag = await kanalen.verstuur_outbox(sessie, driver=driver)
    assert verslag == {"verstuurd": 0, "mislukt": 1}


# ---------------------------------------------------------------------------
# De grens tussen agents en kanalen
# ---------------------------------------------------------------------------


def _importen(bestand: Path) -> set[str]:
    boom = ast.parse(bestand.read_text(encoding="utf-8"), filename=str(bestand))
    namen: set[str] = set()
    for knoop in ast.walk(boom):
        if isinstance(knoop, ast.Import):
            namen.update(alias.name for alias in knoop.names)
        elif isinstance(knoop, ast.ImportFrom) and knoop.module:
            namen.add(knoop.module)
            namen.update(f"{knoop.module}.{alias.name}" for alias in knoop.names)
    return namen


def test_geen_enkele_agent_kan_zelf_versturen():
    """Agents schrijven naar de outbox; versturen doet de applicatielaag.

    Deze test leest de imports van elk bestand in ``app/agents`` en faalt zodra
    er een pad naar ``app.kanalen`` in zit. Dezelfde constructie als bij
    uitbetalingen: de scheiding is een eigenschap van de code, geen afspraak.
    """
    map_pad = Path(__file__).resolve().parent.parent / "app" / "agents"
    overtreders = {
        bestand.name
        for bestand in map_pad.glob("*.py")
        if any(naam.startswith("app.kanalen") for naam in _importen(bestand))
    }
    assert overtreders == set()


def test_agentinstellingen_kennen_geen_verzendgegevens():
    """Een agent die zelf zou willen mailen, heeft geen adres en geen wachtwoord."""
    from app.config import AgentSettings

    velden = set(AgentSettings.model_fields)
    for verboden in ("smtp_host", "smtp_wachtwoord", "afzender_email", "bericht_driver"):
        assert verboden not in velden
