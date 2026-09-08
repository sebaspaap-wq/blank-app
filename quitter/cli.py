"""De opdrachtregel van QUITTER.

    uv run quitter team                       # wie werkt hier
    uv run quitter marge                      # het rekenmodel
    uv run quitter schema standaard           # het afbouwschema
    uv run quitter inpaklijst Q90-S           # wat er in de doos gaat
    uv run quitter check "je tekst hier"      # reclameregels
    uv run quitter vraag REGIE "..."          # laat het team werken (kost API-tokens)
    uv run quitter dagmails standaard 1 14    # laat COACH mails schrijven
"""

from __future__ import annotations

import sys

from . import tools as T
from .agents import TEAM, organigram, voer_uit
from .catalog import prijslijst
from .finance import rapport
from .taper import SCHEMAS


def _hulp() -> int:
    print(__doc__)
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in {"-h", "--help", "help"}:
        return _hulp()

    commando, *rest = argv

    if commando == "team":
        print(organigram())
        return 0

    if commando == "marge":
        print(prijslijst())
        print()
        print(rapport())
        return 0

    if commando == "schema":
        sleutel = (rest[0] if rest else "standaard").lower()
        if sleutel not in SCHEMAS:
            print(f"Kies uit: {', '.join(SCHEMAS)}")
            return 1
        print(SCHEMAS[sleutel].tabel())
        return 0

    if commando == "inpaklijst":
        print(T.inpaklijst(rest[0] if rest else "Q90-S"))
        return 0

    if commando == "check":
        if not rest:
            print("Geef een tekst mee om te controleren.")
            return 1
        print(T.controleer_tekst(" ".join(rest)))
        return 0

    if commando == "vraag":
        if len(rest) < 2:
            print(f"Gebruik: quitter vraag <AGENT> \"<opdracht>\"\nAgents: {', '.join(TEAM)}")
            return 1
        naam, *opdracht = rest
        resultaat = voer_uit(naam, " ".join(opdracht))
        print(resultaat.tekst)
        print(
            f"\n--- {resultaat.agent}: {len(resultaat.gereedschap_gebruikt)} keer gereedschap, "
            f"{resultaat.seconden:.0f}s, ongeveer ${resultaat.kosten_dollar:.2f}"
        )
        return 0

    if commando == "dagmails":
        programma = rest[0] if rest else "standaard"
        van = int(rest[1]) if len(rest) > 1 else 1
        tot = int(rest[2]) if len(rest) > 2 else van
        opdracht = (
            f"Schrijf de dagelijkse mails voor het programma '{programma}', dag {van} tot en met {tot}. "
            f"Haal per dag het dagplan op zodat de aantallen kloppen. Sla elke mail op als "
            f"content/email/{programma}/dag-XX.md met de dag in twee cijfers. Geef aan het eind een "
            f"lijst van de bestanden die je hebt gemaakt."
        )
        resultaat = voer_uit("COACH", opdracht)
        print(resultaat.tekst)
        return 0

    print(f"Onbekend commando '{commando}'.\n")
    return _hulp()


if __name__ == "__main__":
    raise SystemExit(main())
