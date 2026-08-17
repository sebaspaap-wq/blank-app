"""Tests voor de Support-agent en de template-engine.

De kern van paragraaf 3.3: Support mag standaardberichten sturen, maar geen
inhoudelijke toezeggingen doen over geld, tarieven of contractvoorwaarden, en
moet bij twijfel escaleren in plaats van gokken.
"""

from __future__ import annotations

import pytest
from sqlalchemy import select

from app.agents import sjablonen
from app.agents.support import SupportAgent
from app.core.domein import BerichtStatus, Kanaal, Tier, VraagUitkomst
from app.db.models import Activiteit, Bericht, Beslissing, Kennisbankitem, Supportvraag
from tests.conftest import maak_medewerker


# ---------------------------------------------------------------------------
# Template-engine
# ---------------------------------------------------------------------------


def test_sjabloon_met_bedrag_wordt_geweigerd():
    """Een sjabloon dat geld belooft, komt de registry niet in."""
    with pytest.raises(sjablonen.VerbodenToezeggingError) as fout:
        sjablonen.Sjabloon(
            naam="test_bedrag",
            kanaal=Kanaal.WHATSAPP,
            onderwerp="Goed nieuws",
            body="Je krijgt €20 bonus overgemaakt.",
        )
    assert "bedrag" in str(fout.value)


@pytest.mark.parametrize(
    "body",
    [
        "Het tarief gaat omhoog.",
        "Je krijgt een vergoeding voor de reistijd.",
        "We passen je contract aan.",
        "Wij beloven dat dit niet meer gebeurt.",
        "Je uurloon wordt verhoogd.",
        "Je krijgt 20 euro.",
    ],
)
def test_alle_soorten_toezeggingen_worden_geweigerd(body):
    with pytest.raises(sjablonen.VerbodenToezeggingError):
        sjablonen.Sjabloon(
            naam="test", kanaal=Kanaal.WHATSAPP, onderwerp="Onderwerp", body=body
        )


def test_geregistreerde_sjablonen_doen_geen_toezeggingen():
    """Elk sjabloon dat echt in gebruik is, is door de guard gekomen."""
    for naam, sjabloon in sjablonen.alle_sjablonen().items():
        sjablonen._controleer_geen_toezegging(naam, f"{sjabloon.onderwerp}\n{sjabloon.body}")


def test_ontbrekende_variabele_is_een_fout():
    """Liever niets versturen dan een half ingevuld bericht."""
    sjabloon = sjablonen.haal_sjabloon("no_show_waarschuwing")
    with pytest.raises(sjablonen.SjabloonFout) as fout:
        sjabloon.render(medewerker_naam="Sanne")
    assert "bedrijf_naam" in str(fout.value)


def test_onbekende_variabele_is_een_fout():
    """Er is geen sluiproute om extra tekst mee te sturen."""
    sjabloon = sjablonen.haal_sjabloon("onboarding")
    with pytest.raises(sjablonen.SjabloonFout):
        sjabloon.render(medewerker_naam="Sanne", extra_tekst="en hierbij beloof ik...")


def test_lege_variabele_is_een_fout():
    sjabloon = sjablonen.haal_sjabloon("onboarding")
    with pytest.raises(sjablonen.SjabloonFout):
        sjabloon.render(medewerker_naam="   ")


def test_onbekend_sjabloon_bestaat_niet():
    """Support kan alleen versturen wat geregistreerd is."""
    with pytest.raises(sjablonen.SjabloonFout) as fout:
        sjablonen.haal_sjabloon("zelfbedacht_bericht")
    assert "uitsluitend geregistreerde" in str(fout.value)


# ---------------------------------------------------------------------------
# Vragen beantwoorden
# ---------------------------------------------------------------------------


async def _kennisbank(sessie, *, vereist_mens: bool = False) -> Kennisbankitem:
    item = Kennisbankitem(
        vraag="Hoe meld ik me af voor een shift?",
        antwoord="Afmelden doe je in de app bij 'Mijn shifts'.",
        trefwoorden=["afmelden", "afzeggen", "annuleren"],
        categorie="shifts",
        vereist_mens=vereist_mens,
    )
    sessie.add(item)
    await sessie.flush()
    return item


async def test_standaardvraag_wordt_zelfstandig_beantwoord(sessie):
    """Tier 1: past er een goedgekeurd antwoord, dan gaat het eruit."""
    item = await _kennisbank(sessie)
    medewerker = await maak_medewerker(sessie, "Sanne", functies=["bar"], dagen=["za"])

    resultaat = await SupportAgent().beantwoord_vraag(
        sessie, "Hoe kan ik me afmelden voor mijn shift?", medewerker.id
    )

    assert resultaat["uitkomst"] == str(VraagUitkomst.BEANTWOORD)
    assert resultaat["kennisbankitem_id"] == item.id
    assert resultaat["beslissing_id"] is None

    bericht = (await sessie.execute(select(Bericht))).scalars().one()
    assert bericht.sjabloon == "kennisbank_antwoord"
    assert bericht.status == str(BerichtStatus.KLAAR)
    # De verstuurde tekst is letterlijk het goedgekeurde antwoord.
    assert item.antwoord in bericht.inhoud
    assert "Sanne" in bericht.inhoud


async def test_klacht_escaleert_altijd_naar_tier3(sessie):
    """Een klacht wordt nooit beantwoord, ook niet als er iets op lijkt te passen."""
    await _kennisbank(sessie)
    medewerker = await maak_medewerker(sessie, "Milan", functies=["bar"], dagen=["za"])

    resultaat = await SupportAgent().beantwoord_vraag(
        sessie,
        "Ik heb een klacht: ik werd uitgescholden door de manager en wil me afmelden",
        medewerker.id,
    )

    assert resultaat["uitkomst"] == str(VraagUitkomst.GEESCALEERD)
    beslissing = await sessie.get(Beslissing, resultaat["beslissing_id"])
    assert beslissing.tier == int(Tier.WACHT)
    assert beslissing.urgentie == "dringend"


@pytest.mark.parametrize(
    "vraag",
    [
        "Ik wil een klacht indienen over het bedrijf",
        "Er was ruzie tijdens de shift",
        "Ik voelde me onveilig op de werkvloer",
        "Dit voelt als discriminatie",
        "Ik ga naar een advocaat",
        "Ik heb letsel opgelopen tijdens mijn shift",
    ],
)
async def test_klachtsignalen_worden_herkend(sessie, vraag):
    await _kennisbank(sessie)
    medewerker = await maak_medewerker(sessie, "Noor", functies=["bar"], dagen=["za"])

    resultaat = await SupportAgent().beantwoord_vraag(sessie, vraag, medewerker.id)

    assert resultaat["uitkomst"] == str(VraagUitkomst.GEESCALEERD)


async def test_onbekende_vraag_escaleert_in_plaats_van_gokken(sessie):
    """Paragraaf 3.3: buiten de kennisbank niet laten gokken."""
    await _kennisbank(sessie)
    medewerker = await maak_medewerker(sessie, "Daan", functies=["bar"], dagen=["za"])

    resultaat = await SupportAgent().beantwoord_vraag(
        sessie, "Mag ik mijn hond meenemen naar de strandtent?", medewerker.id
    )

    assert resultaat["uitkomst"] == str(VraagUitkomst.GEESCALEERD)
    assert resultaat["kennisbankitem_id"] is None


async def test_geldvraag_escaleert_ook_met_antwoord_in_de_kennisbank(sessie):
    """Onderwerpen die als vereist_mens staan, gaan altijd naar Sebas."""
    item = Kennisbankitem(
        vraag="Wanneer krijg ik uitbetaald?",
        antwoord="Uitbetalingen worden per periode klaargezet.",
        trefwoorden=["uitbetaald", "uitbetaling", "betaling"],
        categorie="geld",
        vereist_mens=True,
    )
    sessie.add(item)
    await sessie.flush()
    medewerker = await maak_medewerker(sessie, "Tom", functies=["bar"], dagen=["za"])

    resultaat = await SupportAgent().beantwoord_vraag(
        sessie, "Wanneer word ik uitbetaald voor mijn shift?", medewerker.id
    )

    assert resultaat["uitkomst"] == str(VraagUitkomst.GEESCALEERD)
    assert resultaat["kennisbankitem_id"] == item.id  # gevonden, maar niet verstuurd

    # De medewerker krijgt alleen het neutrale sjabloon, niet het antwoord.
    berichten = (await sessie.execute(select(Bericht))).scalars().all()
    assert len(berichten) == 1
    assert berichten[0].sjabloon == "vraag_doorgezet"
    assert item.antwoord not in berichten[0].inhoud

    beslissing = await sessie.get(Beslissing, resultaat["beslissing_id"])
    assert "Wanneer krijg ik uitbetaald?" in beslissing.situatie


async def test_escalatie_stuurt_alleen_een_neutraal_bericht(sessie):
    await _kennisbank(sessie)
    medewerker = await maak_medewerker(sessie, "Lisa", functies=["keuken"], dagen=["ma"])

    await SupportAgent().beantwoord_vraag(
        sessie, "Mag ik mijn hond meenemen?", medewerker.id
    )

    bericht = (await sessie.execute(select(Bericht))).scalars().one()
    assert bericht.sjabloon == "vraag_doorgezet"
    assert "doorgezet naar Sebas" in bericht.inhoud


async def test_elke_vraag_wordt_vastgelegd(sessie):
    """Audit-trail: elke binnengekomen vraag is later terug te vinden."""
    await _kennisbank(sessie)
    medewerker = await maak_medewerker(sessie, "Sanne", functies=["bar"], dagen=["za"])

    await SupportAgent().beantwoord_vraag(sessie, "Hoe kan ik me afmelden?", medewerker.id)
    await SupportAgent().beantwoord_vraag(sessie, "Iets heel anders?", medewerker.id)

    vragen = (await sessie.execute(select(Supportvraag))).scalars().all()
    assert len(vragen) == 2
    assert {v.uitkomst for v in vragen} == {
        str(VraagUitkomst.BEANTWOORD),
        str(VraagUitkomst.GEESCALEERD),
    }


# ---------------------------------------------------------------------------
# Onboarding en no-show
# ---------------------------------------------------------------------------


async def test_onboarding_is_tier1(sessie):
    medewerker = await maak_medewerker(sessie, "Nieuw", functies=["bar"], dagen=["za"])

    await SupportAgent().verstuur_onboarding(sessie, medewerker.id)

    bericht = (await sessie.execute(select(Bericht))).scalars().one()
    assert bericht.sjabloon == "onboarding"
    assert "Welkom bij WOSZ" in bericht.onderwerp

    regel = (
        (await sessie.execute(select(Activiteit).where(Activiteit.afdeling == "support")))
        .scalars()
        .one()
    )
    assert regel.tier == int(Tier.ZELFSTANDIG)


async def test_no_show_gebruikt_zwaarder_sjabloon_bij_herhaling(sessie, bedrijf, zaterdag):
    from sqlalchemy import select as sel

    from app.agents.matching import MatchingAgent
    from app.core.events import verwerk_pending
    from app.db.models import Match
    from tests.conftest import maak_shift

    await maak_medewerker(sessie, "Onbetrouwbaar", functies=["bediening"], dagen=["za"])
    agent = MatchingAgent()

    from datetime import timedelta

    for week in range(2):
        shift = await maak_shift(sessie, bedrijf, datum=zaterdag + timedelta(weeks=week))
        await agent.match_shift(sessie, shift)
        match = (
            (await sessie.execute(sel(Match).where(Match.shift_id == shift.id)))
            .scalars()
            .one()
        )
        await agent.signaleer_no_show(sessie, match.id)
        await verwerk_pending(sessie)

    berichten = (await sessie.execute(select(Bericht))).scalars().all()
    assert [b.sjabloon for b in berichten] == [
        "no_show_waarschuwing",
        "herhaalde_no_show",
    ]
    assert "2e keer" in berichten[1].inhoud
