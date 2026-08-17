"""Tests voor de Marketing-agent.

Kern van paragraaf 3.1: contentplanning binnen de huisstijl en kleine
budgetschuiven zijn tier 1; nieuw budget, een nieuwe hoek en resultaten die meer
dan 25% afwijken zijn tier 3.
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest
import pytest_asyncio
from sqlalchemy import select

from app.agents.marketing import (
    AFWIJKING_DREMPEL_PCT,
    BandbreedteOverschredenError,
    MarketingAgent,
)
from app.core.domein import (
    BudgetmutatieStatus,
    CampagneStatus,
    ContentStatus,
    Tier,
    nu,
)
from app.core.events import WervingstekortGemeld, verwerk_pending
from app.db.models import (
    Activiteit,
    Beslissing,
    Budgetmutatie,
    Campagne,
    CampagneResultaat,
    Contentitem,
    Hoek,
)


@pytest_asyncio.fixture
async def hoek(sessie) -> Hoek:
    h = Hoek(
        naam="Geen zzp-gedoe",
        omschrijving="Werken zonder KvK-gedoe.",
        toon="Nuchter en direct.",
        voorbeelden=["Geen KvK, geen facturen, geen gedoe."],
        goedgekeurd=True,
    )
    sessie.add(h)
    await sessie.flush()
    return h


@pytest_asyncio.fixture
async def campagnes(sessie, hoek) -> tuple[Campagne, Campagne]:
    goed = Campagne(
        naam="Geen zzp-gedoe",
        hoek_id=hoek.id,
        dagbudget_cent=2500,
        bandbreedte_pct=20.0,
        verwachte_kosten_per_aanmelding_cent=450,
    )
    matig = Campagne(
        naam="Vrienden-bonus",
        hoek_id=hoek.id,
        dagbudget_cent=1500,
        bandbreedte_pct=20.0,
        verwachte_kosten_per_aanmelding_cent=600,
    )
    sessie.add_all([goed, matig])
    await sessie.flush()
    return goed, matig


# ---------------------------------------------------------------------------
# Content-kalender (tier 1)
# ---------------------------------------------------------------------------


async def test_content_plannen_is_tier1(sessie, hoek):
    morgen = nu().date() + timedelta(days=1)

    await MarketingAgent().plan_content(
        sessie, hoek_id=hoek.id, geplande_datum=morgen, aanleiding="weekplanning"
    )

    item = (await sessie.execute(select(Contentitem))).scalars().one()
    assert item.status == str(ContentStatus.GEPLAND)
    assert item.hoek_id == hoek.id
    assert item.haak

    regel = (
        (await sessie.execute(select(Activiteit).where(Activiteit.afdeling == "marketing")))
        .scalars()
        .one()
    )
    assert regel.tier == int(Tier.ZELFSTANDIG)


async def test_content_op_niet_goedgekeurde_hoek_wordt_geweigerd(sessie):
    """Buiten de huisstijl plannen is geen tier 1-actie."""
    hoek = Hoek(naam="Experiment", omschrijving="Nog niet akkoord", goedgekeurd=False)
    sessie.add(hoek)
    await sessie.flush()

    with pytest.raises(PermissionError) as fout:
        await MarketingAgent().plan_content(
            sessie, hoek_id=hoek.id, geplande_datum=nu().date() + timedelta(days=1)
        )
    assert "niet goedgekeurd" in str(fout.value)
    assert (await sessie.execute(select(Contentitem))).scalars().all() == []


async def test_concepttekst_bevat_nooit_een_bedrag(sessie, hoek):
    """Een post die een bedrag noemt, is een toezegging — die gaat er niet in."""
    await MarketingAgent().plan_week(sessie, aantal=3)

    items = (await sessie.execute(select(Contentitem))).scalars().all()
    assert items
    for item in items:
        tekst = f"{item.haak} {item.concepttekst}"
        assert "€" not in tekst
        assert "euro" not in tekst.lower()
        assert "per uur" not in tekst.lower()


async def test_weekplanning_vult_meerdere_dagen(sessie, hoek):
    verslag = await MarketingAgent().plan_week(sessie, aantal=3)

    assert len(verslag) == 3
    items = (await sessie.execute(select(Contentitem))).scalars().all()
    assert len({i.geplande_datum for i in items}) == 3


# ---------------------------------------------------------------------------
# Budget (tier 1 binnen de bandbreedte)
# ---------------------------------------------------------------------------


async def test_budget_verschuiven_binnen_bandbreedte(sessie, campagnes):
    goed, matig = campagnes
    totaal_voor = goed.dagbudget_cent + matig.dagbudget_cent

    # 20% van €15,00 = €3,00 — precies het maximum.
    await MarketingAgent().verschuif_budget(
        sessie,
        van_campagne_id=matig.id,
        naar_campagne_id=goed.id,
        bedrag_cent=300,
        reden="presteert beter",
    )

    assert matig.dagbudget_cent == 1200
    assert goed.dagbudget_cent == 2800
    # De kern: het totaal is per constructie behouden.
    assert goed.dagbudget_cent + matig.dagbudget_cent == totaal_voor


async def test_verschuiving_boven_de_bandbreedte_kan_niet_via_tier1(sessie, campagnes):
    """De agent kan een grote schuif niet zelfstandig forceren."""
    goed, matig = campagnes

    with pytest.raises(BandbreedteOverschredenError) as fout:
        await MarketingAgent().verschuif_budget(
            sessie,
            van_campagne_id=matig.id,
            naar_campagne_id=goed.id,
            bedrag_cent=1000,  # €10 van een budget van €15 = 67%
            reden="te veel",
        )

    assert "bandbreedte" in str(fout.value)
    assert matig.dagbudget_cent == 1500  # onveranderd
    assert (await sessie.execute(select(Budgetmutatie))).scalars().all() == []


async def test_verschuiving_levert_een_werklijstregel_op(sessie, campagnes):
    """Het systeem wijzigt niets in Ads Manager; Sebas doet dat zelf."""
    goed, matig = campagnes

    await MarketingAgent().verschuif_budget(
        sessie,
        van_campagne_id=matig.id,
        naar_campagne_id=goed.id,
        bedrag_cent=200,
        reden="test",
    )

    mutatie = (await sessie.execute(select(Budgetmutatie))).scalars().one()
    assert mutatie.soort == "verschuiving"
    assert mutatie.status == str(BudgetmutatieStatus.KLAAR_VOOR_UITVOERING)
    assert mutatie.doorgevoerd_op is None


async def test_verschuiving_naar_zichzelf_wordt_geweigerd(sessie, campagnes):
    goed, _ = campagnes
    with pytest.raises(ValueError):
        await MarketingAgent().verschuif_budget(
            sessie,
            van_campagne_id=goed.id,
            naar_campagne_id=goed.id,
            bedrag_cent=100,
            reden="onzin",
        )


# ---------------------------------------------------------------------------
# Tier 3
# ---------------------------------------------------------------------------


async def test_budgetverhoging_is_tier3(sessie, campagnes):
    """Nieuw geld gaat altijd langs Sebas."""
    goed, _ = campagnes
    budget_voor = goed.dagbudget_cent

    beslissing_id = await MarketingAgent().vraag_budgetverhoging(
        sessie, campagne_id=goed.id, extra_cent=1000, reden="werving loopt achter"
    )

    beslissing = await sessie.get(Beslissing, beslissing_id)
    assert beslissing.tier == int(Tier.WACHT)
    assert beslissing.deadline_at is None
    assert beslissing.afdeling_bron == "marketing"
    # Nog niets gewijzigd.
    assert goed.dagbudget_cent == budget_voor
    assert (await sessie.execute(select(Budgetmutatie))).scalars().all() == []


async def test_goedgekeurde_verhoging_komt_op_de_werklijst(sessie, campagnes):
    from app.core.tiers import verwerk_keuze

    goed, _ = campagnes
    beslissing_id = await MarketingAgent().vraag_budgetverhoging(
        sessie, campagne_id=goed.id, extra_cent=1000, reden="werving loopt achter"
    )

    await verwerk_keuze(sessie, beslissing_id, 0)  # Goedkeuren

    assert goed.dagbudget_cent == 3500
    mutatie = (await sessie.execute(select(Budgetmutatie))).scalars().one()
    assert mutatie.soort == "verhoging"
    assert mutatie.status == str(BudgetmutatieStatus.KLAAR_VOOR_UITVOERING)


async def test_nieuwe_hoek_is_tier3_en_voegt_niets_toe(sessie, hoek):
    beslissing_id = await MarketingAgent().stel_nieuwe_hoek_voor(
        sessie,
        naam="Bijbaan naast je studie",
        omschrijving="Richten op studenten die roosters combineren.",
        reden="De huidige hoeken spreken studenten weinig aan.",
    )

    beslissing = await sessie.get(Beslissing, beslissing_id)
    assert beslissing.tier == int(Tier.WACHT)
    # De hoek bestaat nog niet: alleen de bestaande fixture-hoek staat er.
    hoeken = (await sessie.execute(select(Hoek))).scalars().all()
    assert len(hoeken) == 1


async def test_goedgekeurde_hoek_komt_in_de_huisstijl(sessie, hoek):
    from app.core.tiers import verwerk_keuze

    beslissing_id = await MarketingAgent().stel_nieuwe_hoek_voor(
        sessie, naam="Bijbaan naast je studie", omschrijving="Voor studenten.", reden="test"
    )

    await verwerk_keuze(sessie, beslissing_id, 0)

    hoeken = (await sessie.execute(select(Hoek))).scalars().all()
    assert len(hoeken) == 2
    nieuw = next(h for h in hoeken if h.naam == "Bijbaan naast je studie")
    assert nieuw.goedgekeurd is True


async def test_afwijking_boven_25_procent_escaleert(sessie, campagnes):
    """Paragraaf 3.1: meer dan 25% afwijking gaat naar Sebas."""
    goed, _ = campagnes
    gisteren = nu().date() - timedelta(days=1)

    # Verwacht €4,50 per aanmelding; werkelijk €10,00 = +122%.
    sessie.add(
        CampagneResultaat(
            campagne_id=goed.id, datum=gisteren, uitgaven_cent=2000, aanmeldingen=2
        )
    )
    await sessie.flush()

    bevindingen = await MarketingAgent().beoordeel_resultaten(sessie, datum=gisteren)

    bevinding = next(b for b in bevindingen if b["campagne"] == goed.naam)
    assert bevinding["afwijking_pct"] > AFWIJKING_DREMPEL_PCT
    assert bevinding["beslissing_id"] is not None

    beslissing = await sessie.get(Beslissing, bevinding["beslissing_id"])
    assert beslissing.tier == int(Tier.WACHT)
    # Er is niets gepauzeerd: dat wacht op Sebas.
    assert goed.status == str(CampagneStatus.ACTIEF)


async def test_dagcijfers_worden_opgeteld_bij_meerdere_rijen(sessie, campagnes):
    """Cijfers kunnen in delen binnenkomen; de dagconclusie telt ze op.

    Eerder pakte de agent de eerste rij die de database teruggaf, waardoor een
    tweede invoer voor dezelfde dag stil genegeerd werd.
    """
    goed, _ = campagnes
    gisteren = nu().date() - timedelta(days=1)

    # Twee halve dagen: samen €20 voor 2 aanmeldingen = €10 per aanmelding,
    # tegenover een verwachting van €4,50 (+122%).
    sessie.add_all(
        [
            CampagneResultaat(
                campagne_id=goed.id, datum=gisteren, uitgaven_cent=1000, aanmeldingen=1
            ),
            CampagneResultaat(
                campagne_id=goed.id, datum=gisteren, uitgaven_cent=1000, aanmeldingen=1
            ),
        ]
    )
    await sessie.flush()

    bevindingen = await MarketingAgent().beoordeel_resultaten(sessie, datum=gisteren)

    bevinding = next(b for b in bevindingen if b["campagne"] == goed.naam)
    assert bevinding["werkelijk_cent"] == 1000
    assert bevinding["beslissing_id"] is not None


async def test_afwijking_precies_op_de_drempel_escaleert_niet(sessie, campagnes):
    """Paragraaf 3.1 zegt "> 25%", dus precies 25% blijft tier 1."""
    _, matig = campagnes
    gisteren = nu().date() - timedelta(days=1)

    # Verwacht €6,00; werkelijk €7,50 = precies +25%.
    sessie.add(
        CampagneResultaat(
            campagne_id=matig.id, datum=gisteren, uitgaven_cent=1500, aanmeldingen=2
        )
    )
    await sessie.flush()

    bevindingen = await MarketingAgent().beoordeel_resultaten(sessie, datum=gisteren)

    bevinding = next(b for b in bevindingen if b["campagne"] == matig.naam)
    assert bevinding["afwijking_pct"] == 25.0
    assert bevinding["beslissing_id"] is None


async def test_afwijking_binnen_de_marge_escaleert_niet(sessie, campagnes):
    goed, _ = campagnes
    gisteren = nu().date() - timedelta(days=1)

    # Verwacht €4,50; werkelijk €5,00 = +11%.
    sessie.add(
        CampagneResultaat(
            campagne_id=goed.id, datum=gisteren, uitgaven_cent=1000, aanmeldingen=2
        )
    )
    await sessie.flush()

    bevindingen = await MarketingAgent().beoordeel_resultaten(sessie, datum=gisteren)

    bevinding = next(b for b in bevindingen if b["campagne"] == goed.naam)
    assert bevinding["beslissing_id"] is None
    assert (await sessie.execute(select(Beslissing))).scalars().all() == []


async def test_pauzeren_gebeurt_pas_na_keuze_van_sebas(sessie, campagnes):
    from app.core.tiers import verwerk_keuze

    goed, _ = campagnes
    gisteren = nu().date() - timedelta(days=1)
    sessie.add(
        CampagneResultaat(
            campagne_id=goed.id, datum=gisteren, uitgaven_cent=2000, aanmeldingen=2
        )
    )
    await sessie.flush()

    bevindingen = await MarketingAgent().beoordeel_resultaten(sessie, datum=gisteren)
    beslissing_id = bevindingen[0]["beslissing_id"]

    await verwerk_keuze(sessie, beslissing_id, 0)  # Campagne pauzeren

    assert goed.status == str(CampagneStatus.GEPAUZEERD)


# ---------------------------------------------------------------------------
# De lus Matching -> Marketing
# ---------------------------------------------------------------------------


async def test_wervingstekort_leidt_tot_content(sessie, hoek):
    """De pijl Matching → Marketing is nu functioneel, niet alleen een logregel."""
    over_een_week = (nu().date() + timedelta(days=7)).isoformat()

    await MarketingAgent().reageer_op_wervingstekort(
        sessie,
        WervingstekortGemeld(functie="bediening", open_plekken=1, datum=over_een_week),
    )

    item = (await sessie.execute(select(Contentitem))).scalars().one()
    assert "bediening" in item.aanleiding
    assert item.status == str(ContentStatus.GEPLAND)
    # De post staat vóór de shift gepland, anders komt de werving te laat.
    assert item.geplande_datum < date.fromisoformat(over_een_week)


async def test_groot_tekort_stuurt_ook_budget_bij(sessie, hoek, campagnes):
    """Vanaf twee open plekken verschuift de agent ook budget (tier 1)."""
    goed, matig = campagnes
    vanaf = nu().date() - timedelta(days=3)
    # 'Geen zzp-gedoe' levert goedkopere aanmeldingen dan 'Vrienden-bonus'.
    sessie.add_all(
        [
            CampagneResultaat(
                campagne_id=goed.id, datum=vanaf, uitgaven_cent=2500, aanmeldingen=6
            ),
            CampagneResultaat(
                campagne_id=matig.id, datum=vanaf, uitgaven_cent=1500, aanmeldingen=2
            ),
        ]
    )
    await sessie.flush()
    totaal_voor = goed.dagbudget_cent + matig.dagbudget_cent

    await MarketingAgent().reageer_op_wervingstekort(
        sessie,
        WervingstekortGemeld(
            functie="bediening",
            open_plekken=2,
            datum=(nu().date() + timedelta(days=7)).isoformat(),
        ),
    )

    # Budget is naar de best presterende campagne geschoven, totaal gelijk.
    assert goed.dagbudget_cent > 2500
    assert goed.dagbudget_cent + matig.dagbudget_cent == totaal_voor
    assert (await sessie.execute(select(Budgetmutatie))).scalars().first() is not None


async def test_wervingstekort_via_de_bus(sessie, hoek, bedrijf, zaterdag):
    """Volledige keten: onvervulbare shift -> event -> content op de kalender."""
    from app.agents.matching import MatchingAgent
    from tests.conftest import maak_shift

    # Geen kandidaten: de shift blijft open.
    shift = await maak_shift(sessie, bedrijf, datum=zaterdag, aantal=1)
    await MatchingAgent().match_shift(sessie, shift)

    await verwerk_pending(sessie)

    item = (await sessie.execute(select(Contentitem))).scalars().one()
    assert "bediening" in item.aanleiding

    marketing = (
        (await sessie.execute(select(Activiteit).where(Activiteit.afdeling == "marketing")))
        .scalars()
        .all()
    )
    assert any("ingepland" in a.tekst for a in marketing)


async def test_zonder_hoek_wordt_er_niets_gepland(sessie):
    """Geen goedgekeurde huisstijl: dan plant de agent niets, maar meldt het wel."""
    await MarketingAgent().reageer_op_wervingstekort(
        sessie,
        WervingstekortGemeld(
            functie="keuken", open_plekken=1, datum=nu().date().isoformat()
        ),
    )

    assert (await sessie.execute(select(Contentitem))).scalars().all() == []
    regel = (
        (await sessie.execute(select(Activiteit).where(Activiteit.afdeling == "marketing")))
        .scalars()
        .one()
    )
    assert "geen goedgekeurde hoek" in regel.tekst


# ---------------------------------------------------------------------------
# Geen Meta Ads-koppeling
# ---------------------------------------------------------------------------


def test_er_is_geen_meta_ads_client_in_de_codebase():
    """Het systeem kan geen advertentie publiceren of budget live wijzigen."""
    from pathlib import Path

    import app.agents

    wortel = Path(app.agents.__file__).parent.parent
    verdacht = (
        "facebook_business",
        "graph.facebook.com",
        "meta_ads",
        "ads_api",
        "META_ACCESS_TOKEN",
    )
    treffers: list[str] = []
    for pad in wortel.rglob("*.py"):
        inhoud = pad.read_text(encoding="utf-8")
        for term in verdacht:
            if term in inhoud:
                treffers.append(f"{pad.name}: {term}")
    assert not treffers, f"Onverwachte Meta Ads-integratie gevonden: {treffers}"


def test_agentconfiguratie_bevat_geen_meta_credentials():
    from app.config import AgentSettings

    velden = set(AgentSettings.model_fields)
    verdacht = {"meta", "ads", "facebook", "instagram", "token"}
    gevonden = {v for v in velden if any(t in v.lower() for t in verdacht)}
    assert not gevonden, f"AgentSettings bevat advertentiecredentials: {gevonden}"
