"""Genereert site/assets/data.js uit de catalogus.

Zo staan de prijzen, de schema's en de zelftest op precies één plek. Verander
een prijs in quitter/catalog.py, draai dit script, en de website klopt weer.

    uv run python -m quitter.site_build
"""

from __future__ import annotations

import json

from .brand import MERK, PAYOFF, RODE_DRAAD
from .catalog import EXTRAS, PROGRAMMAS
from .paths import SITE
from .taper import SCHEMAS, VRAGEN


def bouw() -> dict:
    programmas = []
    for p in PROGRAMMAS:
        s = p.schema
        programmas.append({
            "sku": p.sku,
            "naam": p.naam,
            "ondertitel": p.ondertitel,
            "prijs": p.prijs,
            "voorWie": p.voor_wie,
            "schema": p.schema_sleutel,
            "stuks": {str(mg): n for mg, n in s.stuks_per_sterkte().items()},
            "totaalStuks": s.totaal_stuks(),
            "blokken": [
                {
                    "nummer": b.nummer,
                    "dagVan": b.dag_van,
                    "dagTot": b.dag_tot,
                    "sterkte": b.sterkte_mg,
                    "perDag": b.stuks_per_dag,
                    "kop": b.kop,
                    "doel": b.doel,
                }
                for b in s.blokken
            ],
        })

    return {
        "merk": {
            "naam": MERK.naam,
            "domein": MERK.domein,
            "payoff": PAYOFF,
            "rodeDraad": RODE_DRAAD,
        },
        "programmas": programmas,
        "extras": [
            {"sku": e.sku, "naam": e.naam, "prijs": e.prijs, "soort": e.soort, "pitch": e.pitch}
            for e in EXTRAS
        ],
        "zelftest": VRAGEN,
        "grenzen": {"licht": 2, "standaard": 6},
    }


def schrijf() -> str:
    gegevens = bouw()
    inhoud = (
        "/* Automatisch gegenereerd door quitter/site_build.py — niet met de hand aanpassen.\n"
        "   Pas prijzen aan in quitter/catalog.py en schema's in quitter/taper.py. */\n"
        "window.QUITTER_DATA = "
        + json.dumps(gegevens, ensure_ascii=False, indent=2)
        + ";\n"
    )
    doel = SITE / "assets" / "data.js"
    doel.parent.mkdir(parents=True, exist_ok=True)
    doel.write_text(inhoud, encoding="utf-8")
    return str(doel)


if __name__ == "__main__":
    print(f"Geschreven: {schrijf()}")
