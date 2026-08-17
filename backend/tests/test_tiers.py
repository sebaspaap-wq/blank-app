"""Tests voor de escalatiemotor — het gedrag van tier 1, 2 en 3."""

from __future__ import annotations

from datetime import timedelta

import pytest
from sqlalchemy import select

from app.core import tiers
from app.core.domein import Afdeling, BeslissingStatus, Tier, Urgentie, nu
from app.core.tiers import Optie, Voorstel, behandel_voorstel, registreer_uitvoerder
from app.db.models import Activiteit, Beslissing

UITGEVOERD: list[str] = []


@registreer_uitvoerder("test.noteer")
async def _noteer(_sessie, params, _beslissing) -> str:
    UITGEVOERD.append(params["merk"])
    return f"uitgevoerd: {params['merk']}"


@pytest.fixture(autouse=True)
def leeg_register():
    UITGEVOERD.clear()
    yield
    UITGEVOERD.clear()


def _voorstel(tier: Tier, merk: str = "a") -> Voorstel:
    if tier is Tier.ZELFSTANDIG:
        return Voorstel(
            afdeling=Afdeling.MATCHING,
            tier=tier,
            logtekst="iets gedaan",
            actie={"uitvoerder": "test.noteer", "params": {"merk": merk}},
        )
    return Voorstel(
        afdeling=Afdeling.MATCHING,
        tier=tier,
        titel="Een keuze",
        situatie="Er moet iets besloten worden.",
        aanbeveling="AI-advies: doe optie 1.",
        urgentie=Urgentie.DEZE_WEEK,
        logtekst="voorstel ingediend",
        opties=[
            Optie(
                naam="Doorgaan",
                gevolg="Het gebeurt",
                actie={"uitvoerder": "test.noteer", "params": {"merk": f"{merk}-1"}},
            ),
            Optie(
                naam="Niet doen",
                gevolg="Er gebeurt niets",
                actie={"uitvoerder": "test.noteer", "params": {"merk": f"{merk}-2"}},
            ),
        ],
    )


async def test_tier1_voert_direct_uit_en_logt(sessie):
    uitkomst = await behandel_voorstel(sessie, _voorstel(Tier.ZELFSTANDIG, "direct"))

    assert uitkomst.uitgevoerd is True
    assert uitkomst.beslissing_id is None
    assert UITGEVOERD == ["direct"]

    regel = (await sessie.execute(select(Activiteit))).scalars().one()
    assert regel.tier == int(Tier.ZELFSTANDIG)
    assert regel.afdeling == "matching"


async def test_tier2_wacht_maar_krijgt_een_deadline(sessie):
    uitkomst = await behandel_voorstel(sessie, _voorstel(Tier.TENZIJ))

    assert uitkomst.uitgevoerd is False
    assert UITGEVOERD == []  # nog niets gebeurd

    beslissing = await sessie.get(Beslissing, uitkomst.beslissing_id)
    assert beslissing.tier == int(Tier.TENZIJ)
    assert beslissing.deadline_at is not None
    assert beslissing.status == str(BeslissingStatus.OPEN)


async def test_tier3_krijgt_nooit_een_deadline(sessie):
    uitkomst = await behandel_voorstel(sessie, _voorstel(Tier.WACHT))

    beslissing = await sessie.get(Beslissing, uitkomst.beslissing_id)
    assert beslissing.tier == int(Tier.WACHT)
    assert beslissing.deadline_at is None
    assert UITGEVOERD == []


async def test_sweep_voert_verlopen_tier2_uit(sessie):
    uitkomst = await behandel_voorstel(sessie, _voorstel(Tier.TENZIJ, "verlopen"))
    beslissing = await sessie.get(Beslissing, uitkomst.beslissing_id)
    beslissing.deadline_at = nu() - timedelta(minutes=1)

    uitgevoerd = await tiers.sweep_verlopen_tier2(sessie)

    assert len(uitgevoerd) == 1
    assert UITGEVOERD == ["verlopen-1"]  # de standaardoptie
    assert beslissing.status == str(BeslissingStatus.VERLOPEN_UITGEVOERD)
    assert beslissing.gekozen_optie == "Doorgaan"


async def test_sweep_laat_tier2_binnen_de_termijn_met_rust(sessie):
    await behandel_voorstel(sessie, _voorstel(Tier.TENZIJ))

    uitgevoerd = await tiers.sweep_verlopen_tier2(sessie)

    assert uitgevoerd == []
    assert UITGEVOERD == []


async def test_sweep_raakt_tier3_nooit_aan(sessie):
    """Kern van de harde eis: tier 3 gaat nooit vanzelf door.

    Zelfs met een verstreken deadline op het record blijft de beslissing staan,
    omdat de sweep hard op tier 2 filtert.
    """
    uitkomst = await behandel_voorstel(sessie, _voorstel(Tier.WACHT, "nooit"))
    beslissing = await sessie.get(Beslissing, uitkomst.beslissing_id)
    beslissing.deadline_at = nu() - timedelta(days=7)  # zou nooit mogen bestaan

    uitgevoerd = await tiers.sweep_verlopen_tier2(sessie)

    assert uitgevoerd == []
    assert UITGEVOERD == []
    assert beslissing.status == str(BeslissingStatus.OPEN)


async def test_keuze_van_sebas_voert_de_gekozen_optie_uit(sessie):
    uitkomst = await behandel_voorstel(sessie, _voorstel(Tier.WACHT, "keuze"))

    beslissing = await tiers.verwerk_keuze(sessie, uitkomst.beslissing_id, 1)

    assert UITGEVOERD == ["keuze-2"]
    assert beslissing.gekozen_optie == "Niet doen"
    assert beslissing.status == str(BeslissingStatus.UITGEVOERD)


async def test_keuze_logt_een_regel_zonder_afdelingslabel(sessie):
    """``resolveDecision()`` toont deze regel zonder afdeling; dat blijft zo."""
    uitkomst = await behandel_voorstel(sessie, _voorstel(Tier.WACHT))

    await tiers.verwerk_keuze(sessie, uitkomst.beslissing_id, 0)

    regels = (await sessie.execute(select(Activiteit))).scalars().all()
    directieregels = [r for r in regels if r.afdeling == "directie"]
    assert len(directieregels) == 1
    assert directieregels[0].tekst.startswith("Jouw keuze verwerkt:")


async def test_dubbele_keuze_wordt_geweigerd(sessie):
    uitkomst = await behandel_voorstel(sessie, _voorstel(Tier.WACHT))
    await tiers.verwerk_keuze(sessie, uitkomst.beslissing_id, 0)

    with pytest.raises(ValueError):
        await tiers.verwerk_keuze(sessie, uitkomst.beslissing_id, 1)


async def test_onbekende_uitvoerder_wordt_bij_aanmaak_afgevangen(sessie):
    voorstel = Voorstel(
        afdeling=Afdeling.MATCHING,
        tier=Tier.WACHT,
        titel="Kapot",
        situatie="Verwijst naar niets.",
        logtekst="test",
        opties=[
            Optie(naam="A", gevolg="x", actie={"uitvoerder": "bestaat.niet", "params": {}}),
            Optie(naam="B", gevolg="y", actie={}),
        ],
    )
    with pytest.raises(tiers.OnbekendeUitvoerderError):
        await behandel_voorstel(sessie, voorstel)


async def test_beslissing_vereist_minstens_twee_opties():
    with pytest.raises(ValueError):
        Voorstel(
            afdeling=Afdeling.MATCHING,
            tier=Tier.WACHT,
            titel="Eén optie",
            situatie="Dat is geen keuze.",
            logtekst="test",
            opties=[Optie(naam="A", gevolg="x")],
        )
