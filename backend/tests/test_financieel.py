"""Tests voor de Financieel-agent.

Kern van paragraaf 3.4: uren en factuurconcepten zijn tier 1, maar élke
uitbetaling is tier 3 — zonder uitzondering.
"""

from __future__ import annotations

from sqlalchemy import select

from app.agents.financieel import FinancieelAgent
from app.agents.matching import MatchingAgent
from app.core.domein import BeslissingStatus, Tier, UitbetalingStatus
from app.core.events import LevelBereikt, UrenGewerkt, verwerk_pending
from app.db.models import (
    Activiteit,
    Beslissing,
    Factuur,
    Match,
    Referral,
    Uitbetalingsopdracht,
)
from tests.conftest import maak_medewerker, maak_shift


# ---------------------------------------------------------------------------
# Uren en facturen (tier 1)
# ---------------------------------------------------------------------------


async def test_uren_belanden_op_een_factuurconcept(sessie, bedrijf):
    resultaat = await FinancieelAgent().verwerk_uren(
        sessie,
        UrenGewerkt(
            match_id=1,
            medewerker_id=1,
            bedrijf_id=bedrijf.id,
            uren=6.0,
            datum="2026-08-22",
        ),
    )

    assert resultaat["periode"] == "2026-08"
    factuur = (await sessie.execute(select(Factuur))).scalars().one()
    assert factuur.uren == 6.0
    assert factuur.bedrag_cent == 1200  # 6 uur x €2,00 WOSZ-marge


async def test_uren_tellen_op_binnen_dezelfde_periode(sessie, bedrijf):
    agent = FinancieelAgent()
    for uren in (6.0, 8.0, 4.0):
        await agent.verwerk_uren(
            sessie,
            UrenGewerkt(
                match_id=1,
                medewerker_id=1,
                bedrijf_id=bedrijf.id,
                uren=uren,
                datum="2026-08-22",
            ),
        )

    factuur = (await sessie.execute(select(Factuur))).scalars().one()
    assert factuur.uren == 18.0
    assert factuur.bedrag_cent == 3600


async def test_andere_periode_krijgt_een_eigen_factuur(sessie, bedrijf):
    agent = FinancieelAgent()
    await agent.verwerk_uren(
        sessie,
        UrenGewerkt(
            match_id=1, medewerker_id=1, bedrijf_id=bedrijf.id, uren=6.0, datum="2026-08-22"
        ),
    )
    await agent.verwerk_uren(
        sessie,
        UrenGewerkt(
            match_id=2, medewerker_id=1, bedrijf_id=bedrijf.id, uren=6.0, datum="2026-09-05"
        ),
    )

    facturen = (await sessie.execute(select(Factuur))).scalars().all()
    assert {f.periode for f in facturen} == {"2026-08", "2026-09"}


async def test_periode_afsluiten_is_tier1(sessie, bedrijf):
    """Een factuur sturen is geen uitbetaling: er komt geld binnen."""
    agent = FinancieelAgent()
    await agent.verwerk_uren(
        sessie,
        UrenGewerkt(
            match_id=1, medewerker_id=1, bedrijf_id=bedrijf.id, uren=10.0, datum="2026-08-22"
        ),
    )

    verslag = await agent.sluit_periode_af(sessie, "2026-08")

    assert len(verslag) == 1
    factuur = (await sessie.execute(select(Factuur))).scalars().one()
    assert factuur.status == "klaar-ter-goedkeuring"

    # Geen enkele beslissing: dit hoefde niet langs Sebas.
    beslissingen = (await sessie.execute(select(Beslissing))).scalars().all()
    assert beslissingen == []


# ---------------------------------------------------------------------------
# Bonussen (tier 3)
# ---------------------------------------------------------------------------


async def test_levelbonus_is_tier3_en_betaalt_niet_uit(sessie):
    beslissing_id = await FinancieelAgent().zet_levelbonus_klaar(
        sessie,
        LevelBereikt(
            medewerker_id=1,
            medewerker_naam="Sanne de Vries",
            nieuw_level=3,
            level_naam="Vaste Kracht",
            bonus_bedrag_cent=2000,
            seizoen_uren=62.0,
        ),
    )

    beslissing = await sessie.get(Beslissing, beslissing_id)
    assert beslissing.tier == int(Tier.WACHT)
    assert beslissing.deadline_at is None
    assert beslissing.urgentie == "dringend"
    assert beslissing.afdeling_bron == "financieel"

    opdracht = (await sessie.execute(select(Uitbetalingsopdracht))).scalars().one()
    assert opdracht.status == str(UitbetalingStatus.CONCEPT)
    assert opdracht.goedgekeurd_op is None


async def test_goedkeuren_zet_klaar_voor_handmatige_overboeking(sessie):
    from app.core.tiers import verwerk_keuze

    beslissing_id = await FinancieelAgent().zet_levelbonus_klaar(
        sessie,
        LevelBereikt(
            medewerker_id=1,
            medewerker_naam="Sanne",
            nieuw_level=3,
            level_naam="Vaste Kracht",
            bonus_bedrag_cent=2000,
            seizoen_uren=62.0,
        ),
    )

    await verwerk_keuze(sessie, beslissing_id, 0)  # "Goedkeuren"

    opdracht = (await sessie.execute(select(Uitbetalingsopdracht))).scalars().one()
    assert opdracht.status == str(UitbetalingStatus.KLAAR_VOOR_EXPORT)
    assert opdracht.goedgekeurd_op is not None
    # Nog steeds niet betaald: dat doet Sebas zelf bij de bank.
    assert opdracht.handmatig_voldaan_op is None


async def test_afwijzen_annuleert_de_opdracht(sessie):
    from app.core.tiers import verwerk_keuze

    beslissing_id = await FinancieelAgent().zet_levelbonus_klaar(
        sessie,
        LevelBereikt(
            medewerker_id=1,
            medewerker_naam="Sanne",
            nieuw_level=3,
            level_naam="Vaste Kracht",
            bonus_bedrag_cent=2000,
            seizoen_uren=62.0,
        ),
    )

    await verwerk_keuze(sessie, beslissing_id, 1)  # "Nu niet uitbetalen"

    opdracht = (await sessie.execute(select(Uitbetalingsopdracht))).scalars().one()
    assert opdracht.status == str(UitbetalingStatus.GEANNULEERD)


async def test_vriendenbonus_bij_het_passeren_van_de_drempel(sessie, bedrijf):
    aanbrenger = await maak_medewerker(sessie, "Sanne", functies=["bar"], dagen=["za"])
    vriend = await maak_medewerker(sessie, "Tom", functies=["bar"], dagen=["za"])
    sessie.add(
        Referral(
            medewerker_id=aanbrenger.id,
            vriend_id=vriend.id,
            uren_vriend=46.0,
            bonus_status="bezig",
            bonus_bedrag_cent=2000,
        )
    )
    await sessie.flush()

    await FinancieelAgent().verwerk_uren(
        sessie,
        UrenGewerkt(
            match_id=1,
            medewerker_id=vriend.id,
            bedrijf_id=bedrijf.id,
            uren=6.0,
            datum="2026-08-22",
        ),
    )

    referral = (await sessie.execute(select(Referral))).scalars().one()
    assert referral.uren_vriend == 52.0
    assert referral.bonus_status == "ter-goedkeuring"

    opdracht = (await sessie.execute(select(Uitbetalingsopdracht))).scalars().one()
    assert opdracht.soort == "vriendenbonus"
    assert opdracht.begunstigde_naam == "Sanne"
    assert opdracht.status == str(UitbetalingStatus.CONCEPT)

    beslissing = (await sessie.execute(select(Beslissing))).scalars().one()
    assert beslissing.tier == int(Tier.WACHT)


async def test_vriendenbonus_nog_niet_onder_de_drempel(sessie, bedrijf):
    aanbrenger = await maak_medewerker(sessie, "Sanne", functies=["bar"], dagen=["za"])
    vriend = await maak_medewerker(sessie, "Tom", functies=["bar"], dagen=["za"])
    sessie.add(
        Referral(
            medewerker_id=aanbrenger.id,
            vriend_id=vriend.id,
            uren_vriend=20.0,
            bonus_status="bezig",
        )
    )
    await sessie.flush()

    await FinancieelAgent().verwerk_uren(
        sessie,
        UrenGewerkt(
            match_id=1,
            medewerker_id=vriend.id,
            bedrijf_id=bedrijf.id,
            uren=6.0,
            datum="2026-08-22",
        ),
    )

    assert (await sessie.execute(select(Uitbetalingsopdracht))).scalars().all() == []
    assert (await sessie.execute(select(Beslissing))).scalars().all() == []


async def test_geen_bonus_bij_bedrag_nul(sessie):
    """Level 1 kent geen bonus; dan hoeft Sebas ook niets te beslissen."""
    beslissing_id = await FinancieelAgent().zet_levelbonus_klaar(
        sessie,
        LevelBereikt(
            medewerker_id=1,
            medewerker_naam="Nieuw",
            nieuw_level=1,
            level_naam="Beach Starter",
            bonus_bedrag_cent=0,
            seizoen_uren=3.0,
        ),
    )

    assert beslissing_id is None
    assert (await sessie.execute(select(Beslissing))).scalars().all() == []


# ---------------------------------------------------------------------------
# Keten Matching -> Financieel via de event-bus
# ---------------------------------------------------------------------------


async def test_uren_van_matching_komen_via_de_bus_bij_financieel(
    sessie, bedrijf, zaterdag
):
    """De volledige keten: uren boeken -> event -> factuurconcept."""
    await maak_medewerker(
        sessie, "Sanne", functies=["bediening"], dagen=["za"], seizoen_uren=20
    )
    shift = await maak_shift(sessie, bedrijf, datum=zaterdag)
    agent = MatchingAgent()
    await agent.match_shift(sessie, shift)
    match = (await sessie.execute(select(Match))).scalars().one()

    await agent.registreer_gewerkte_uren(sessie, match.id, 6.0)
    await verwerk_pending(sessie)

    factuur = (await sessie.execute(select(Factuur))).scalars().one()
    assert factuur.uren == 6.0

    financieel = (
        (await sessie.execute(select(Activiteit).where(Activiteit.afdeling == "financieel")))
        .scalars()
        .all()
    )
    assert any("factuurconcept" in a.tekst for a in financieel)


async def test_levelsprong_leidt_tot_bonusbeslissing_via_de_bus(sessie, bedrijf, zaterdag):
    """Matching meldt de levelsprong; Financieel zet de bonus klaar (tier 3)."""
    await maak_medewerker(
        sessie, "Tom", functies=["bediening"], dagen=["za"], seizoen_uren=22
    )
    shift = await maak_shift(sessie, bedrijf, datum=zaterdag)
    agent = MatchingAgent()
    await agent.match_shift(sessie, shift)
    match = (await sessie.execute(select(Match))).scalars().one()

    await agent.registreer_gewerkte_uren(sessie, match.id, 6.0)  # 22 -> 28 uur, level 2
    await verwerk_pending(sessie)

    beslissing = (await sessie.execute(select(Beslissing))).scalars().one()
    assert beslissing.afdeling_bron == "financieel"
    assert beslissing.tier == int(Tier.WACHT)
    assert beslissing.status == str(BeslissingStatus.OPEN)
    assert "Shift Regular" in beslissing.situatie
