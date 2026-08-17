"""Tests voor de architecturale scheiding rond uitbetalingen.

De harde eis: de Financieel-agent krijgt geen toegang tot enige betaal-API of
banking-credentials, en dat moet een eigenschap van de bouw zijn — niet een
regel die een LLM moet onthouden. Deze tests bewaken die grens.
"""

from __future__ import annotations

import ast
import pkgutil
from pathlib import Path

import pytest
from sqlalchemy import select

import app.agents
from app.config import AgentSettings, Settings
from app.core.domein import UitbetalingStatus
from app.db.models import Activiteit, Uitbetalingsopdracht

AGENTS_MAP = Path(app.agents.__file__).parent
VERBODEN_PREFIX = "app.payouts"


def _modulepaden() -> list[Path]:
    return sorted(AGENTS_MAP.rglob("*.py"))


def _imports_van(pad: Path) -> set[str]:
    boom = ast.parse(pad.read_text(encoding="utf-8"), filename=str(pad))
    namen: set[str] = set()
    for knoop in ast.walk(boom):
        if isinstance(knoop, ast.Import):
            namen.update(alias.name for alias in knoop.names)
        elif isinstance(knoop, ast.ImportFrom) and knoop.module and knoop.level == 0:
            namen.add(knoop.module)
            namen.update(f"{knoop.module}.{alias.name}" for alias in knoop.names)
    return namen


def test_geen_enkele_agent_importeert_de_uitbetalingsmodule():
    """Directe import-guard: agents mogen app.payouts niet aanraken."""
    overtredingen: list[str] = []
    for pad in _modulepaden():
        for naam in _imports_van(pad):
            if naam == VERBODEN_PREFIX or naam.startswith(VERBODEN_PREFIX + "."):
                overtredingen.append(f"{pad.relative_to(AGENTS_MAP.parent.parent)} -> {naam}")
    assert not overtredingen, (
        "Een module onder app/agents/ importeert de uitbetalingsmodule. "
        "Zie app/payouts/README.md voor waarom dat niet mag:\n"
        + "\n".join(overtredingen)
    )


def test_ook_niet_via_een_omweg():
    """Indirecte import-guard: geen enkel pad, hoe diep ook, mag erbij komen.

    Loopt de volledige import-graaf van elke agentmodule na. Zo blijft de grens
    ook staan als iemand later een hulpmodule tussenvoegt.
    """
    import importlib
    import sys

    for module_info in pkgutil.walk_packages(
        [str(AGENTS_MAP)], prefix="app.agents."
    ):
        importlib.import_module(module_info.name)

    bezocht: set[str] = set()

    def _volg(modulenaam: str, pad: list[str]) -> list[str] | None:
        if modulenaam in bezocht:
            return None
        bezocht.add(modulenaam)
        module = sys.modules.get(modulenaam)
        if module is None or not getattr(module, "__file__", None):
            return None
        bestand = Path(module.__file__)
        if "site-packages" in bestand.parts or "lib" in bestand.parts[:3]:
            return None
        for naam in _imports_van(bestand):
            if naam == VERBODEN_PREFIX or naam.startswith(VERBODEN_PREFIX + "."):
                return [*pad, modulenaam, naam]
            if naam.startswith("app."):
                # Los 'from app.core.tiers import X' op naar de module zelf.
                kandidaat = naam if naam in sys.modules else naam.rsplit(".", 1)[0]
                gevonden = _volg(kandidaat, [*pad, modulenaam])
                if gevonden:
                    return gevonden
        return None

    for module_info in pkgutil.walk_packages([str(AGENTS_MAP)], prefix="app.agents."):
        keten = _volg(module_info.name, [])
        assert keten is None, "Indirect pad naar app.payouts: " + " -> ".join(keten)


def test_financieel_agent_bereikt_de_uitbetalingsmodule_niet():
    """De agent die met geld werkt, kan er nog steeds niet bij.

    De Financieel-agent berekent bedragen en maakt conceptrecords, maar verwijst
    naar de goedkeuringsuitvoerder alleen bij naam — als string in de beslissing.
    Hij importeert app.payouts niet, en kan dat ook niet gaan doen zonder deze
    test te breken.
    """
    from app.agents import financieel

    pad = Path(financieel.__file__)
    for naam in _imports_van(pad):
        assert not naam.startswith(VERBODEN_PREFIX), (
            f"De Financieel-agent importeert {naam}. Verwijs naar de uitvoerder "
            "bij naam in plaats van de module te importeren."
        )

    # De uitvoerder wordt wel degelijk aangeroepen — via de registry, niet via een import.
    from app.core.tiers import uitvoerder_bestaat

    assert uitvoerder_bestaat(financieel.UITVOERDER_GOEDKEUREN)
    assert uitvoerder_bestaat(financieel.UITVOERDER_AFWIJZEN)


def test_agentconfiguratie_bevat_geen_betaalvelden():
    """Agents krijgen AgentSettings; daar zit structureel niets over geld in."""
    velden = set(AgentSettings.model_fields)
    verdacht = {"betaal", "bank", "iban", "mollie", "stripe", "uitbetaling", "payout"}
    gevonden = {v for v in velden if any(term in v.lower() for term in verdacht)}
    assert not gevonden, f"AgentSettings bevat betaalgerelateerde velden: {gevonden}"

    # Ter contrast: de applicatieconfiguratie kent de exportmap wél. Agents
    # krijgen dat object nooit te zien.
    assert "uitbetaling_export_map" in Settings.model_fields


def test_er_bestaat_geen_betaalclient_in_de_codebase():
    """Er is nergens een betaalprovider-integratie om aan te roepen."""
    wortel = AGENTS_MAP.parent
    verdachte_termen = ("mollie", "stripe", "adyen", "sepa_transfer", "initiate_payment")
    treffers: list[str] = []
    for pad in wortel.rglob("*.py"):
        inhoud = pad.read_text(encoding="utf-8").lower()
        for term in verdachte_termen:
            if term in inhoud:
                treffers.append(f"{pad.name}: {term}")
    assert not treffers, f"Onverwachte betaalintegratie gevonden: {treffers}"


def test_uitbetalingsstatus_kent_geen_automatische_betaling():
    """Er is geen status die zegt dat het systeem zelf heeft betaald."""
    waarden = {str(s) for s in UitbetalingStatus}
    assert "handmatig-voldaan" in waarden
    for waarde in waarden:
        assert "automatisch" not in waarde


async def test_goedkeuring_zet_klaar_maar_betaalt_niet(sessie):
    """De knop 'Goedkeuren' levert een werklijst op, geen overboeking."""
    from app.payouts.opdrachten import keur_uitbetaling_goed

    tekst = await keur_uitbetaling_goed(
        sessie,
        {
            "soort": "bonus",
            "begunstigde_naam": "Sanne de Vries",
            "bedrag_cent": 2000,
            "omschrijving": "Vriendenbonus Tom Hendriks",
        },
        None,
    )

    opdracht = (await sessie.execute(select(Uitbetalingsopdracht))).scalars().one()
    assert opdracht.status == str(UitbetalingStatus.KLAAR_VOOR_EXPORT)
    assert opdracht.goedgekeurd_op is not None
    assert opdracht.handmatig_voldaan_op is None
    assert "klaargezet voor handmatige overboeking" in tekst


async def test_export_bevat_geen_rekeningnummers(sessie, tmp_path, monkeypatch):
    """Dataminimalisatie: het exportbestand bevat geen betaalgegevens."""
    from app.config import get_settings
    from app.payouts.opdrachten import exporteer_openstaande_opdrachten, keur_uitbetaling_goed

    instellingen = get_settings()
    monkeypatch.setattr(instellingen, "uitbetaling_export_map", str(tmp_path))

    await keur_uitbetaling_goed(
        sessie,
        {"begunstigde_naam": "Lisa Mulder", "bedrag_cent": 4000, "omschrijving": "Levelbonus"},
        None,
    )

    inhoud, aantal = await exporteer_openstaande_opdrachten(sessie)

    assert aantal == 1
    assert "Lisa Mulder" in inhoud
    assert "40.00" in inhoud
    assert "iban" not in inhoud.lower()
    assert list(tmp_path.glob("uitbetalingen-*.csv"))


async def test_handmatig_voldaan_komt_in_de_audit_trail(sessie, tmp_path, monkeypatch):
    from app.config import get_settings
    from app.payouts.opdrachten import keur_uitbetaling_goed, markeer_handmatig_voldaan

    monkeypatch.setattr(get_settings(), "uitbetaling_export_map", str(tmp_path))
    await keur_uitbetaling_goed(
        sessie, {"begunstigde_naam": "Tom", "bedrag_cent": 2000}, None
    )
    opdracht = (await sessie.execute(select(Uitbetalingsopdracht))).scalars().one()

    await markeer_handmatig_voldaan(sessie, opdracht.id)

    assert opdracht.status == str(UitbetalingStatus.HANDMATIG_VOLDAAN)
    regels = (
        (await sessie.execute(select(Activiteit).where(Activiteit.afdeling == "financieel")))
        .scalars()
        .all()
    )
    assert any("handmatig voldaan" in r.tekst for r in regels)
