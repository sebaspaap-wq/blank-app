"""Het afbouwschema — het hart van QUITTER.

90 dagen, verdeeld in zes blokken van 15 dagen. Per blok staat vast hoeveel
stuks kauwgom per dag en in welke sterkte. Het schema loopt van 4 mg via 2 mg
naar nul. De laatste twee blokken zijn bewust laag: daar leert iemand de trek
uitzitten met steeds minder nicotine, in plaats van in één keer te springen.

Alle aantallen blijven binnen de gangbare doseergrenzen voor nicotinekauwgom
(maximaal 15 stuks per dag bij 4 mg, 24 stuks bij 2 mg). Het definitieve schema
moet worden getoetst aan de SmPC van de fabrikant — zie docs/04-compliance.md.
"""

from __future__ import annotations

from dataclasses import dataclass

BLOK_LENGTE = 15
AANTAL_BLOKKEN = 6
PROGRAMMA_DAGEN = BLOK_LENGTE * AANTAL_BLOKKEN  # 90

MAX_STUKS_PER_DAG = {4: 15, 2: 24}


@dataclass(frozen=True)
class Blok:
    """Eén blok van 15 dagen."""

    nummer: int  # 1..6
    sterkte_mg: int  # 4 of 2
    stuks_per_dag: int
    kop: str  # wat er in dit blok gebeurt, in mensentaal
    doel: str

    @property
    def dag_van(self) -> int:
        return (self.nummer - 1) * BLOK_LENGTE + 1

    @property
    def dag_tot(self) -> int:
        return self.nummer * BLOK_LENGTE

    @property
    def stuks_totaal(self) -> int:
        return self.stuks_per_dag * BLOK_LENGTE

    def valideer(self) -> None:
        if self.sterkte_mg not in MAX_STUKS_PER_DAG:
            raise ValueError(f"blok {self.nummer}: sterkte {self.sterkte_mg} mg bestaat niet")
        maximum = MAX_STUKS_PER_DAG[self.sterkte_mg]
        if not 0 < self.stuks_per_dag <= maximum:
            raise ValueError(
                f"blok {self.nummer}: {self.stuks_per_dag} stuks van {self.sterkte_mg} mg "
                f"overschrijdt het maximum van {maximum} per dag"
            )


@dataclass(frozen=True)
class Schema:
    """Het volledige 90-dagenschema van één programma."""

    sleutel: str
    blokken: tuple[Blok, ...]

    def __post_init__(self) -> None:
        if len(self.blokken) != AANTAL_BLOKKEN:
            raise ValueError(f"{self.sleutel}: verwacht {AANTAL_BLOKKEN} blokken")
        vorige_dosis = None
        for blok in self.blokken:
            blok.valideer()
            dosis = blok.sterkte_mg * blok.stuks_per_dag
            if vorige_dosis is not None and dosis > vorige_dosis:
                raise ValueError(
                    f"{self.sleutel}: blok {blok.nummer} gaat omhoog in nicotine "
                    f"({vorige_dosis} mg -> {dosis} mg). Een afbouwschema loopt alleen omlaag."
                )
            vorige_dosis = dosis

    def blok_op_dag(self, dag: int) -> Blok:
        if not 1 <= dag <= PROGRAMMA_DAGEN:
            raise ValueError(f"dag {dag} valt buiten het programma van {PROGRAMMA_DAGEN} dagen")
        return self.blokken[(dag - 1) // BLOK_LENGTE]

    def stuks_per_sterkte(self) -> dict[int, int]:
        """Hoeveel stuks van elke sterkte er in totaal in de doos moeten."""
        totalen: dict[int, int] = {}
        for blok in self.blokken:
            totalen[blok.sterkte_mg] = totalen.get(blok.sterkte_mg, 0) + blok.stuks_totaal
        return dict(sorted(totalen.items(), reverse=True))

    def totaal_stuks(self) -> int:
        return sum(self.stuks_per_sterkte().values())

    def totaal_nicotine_mg(self) -> int:
        return sum(mg * n for mg, n in self.stuks_per_sterkte().items())

    def dagplan(self, dag: int) -> dict:
        """Wat de klant op deze dag doet. Dit voedt de dagelijkse coachmail."""
        blok = self.blok_op_dag(dag)
        dag_in_blok = (dag - 1) % BLOK_LENGTE + 1
        gebruikt = sum(b.stuks_totaal for b in self.blokken[: blok.nummer - 1])
        gebruikt += blok.stuks_per_dag * (dag_in_blok - 1)
        return {
            "dag": dag,
            "blok": blok.nummer,
            "dag_in_blok": dag_in_blok,
            "sterkte_mg": blok.sterkte_mg,
            "stuks_vandaag": blok.stuks_per_dag,
            "kop": blok.kop,
            "doel": blok.doel,
            "resterende_dagen": PROGRAMMA_DAGEN - dag,
            "stuks_tot_nu": gebruikt + blok.stuks_per_dag,
            "eerste_dag_van_blok": dag_in_blok == 1,
            "laatste_dag": dag == PROGRAMMA_DAGEN,
        }

    def alle_dagen(self) -> list[dict]:
        return [self.dagplan(d) for d in range(1, PROGRAMMA_DAGEN + 1)]

    def tabel(self) -> str:
        """Het schema als tekst — gaat zo op de afbouwkaart in de doos."""
        regels = [
            f"{'Blok':<5} {'Dagen':<10} {'Sterkte':<9} {'Per dag':<9} {'Totaal':<8} Wat je doet",
            "-" * 88,
        ]
        for b in self.blokken:
            regels.append(
                f"{b.nummer:<5} {f'{b.dag_van}-{b.dag_tot}':<10} {f'{b.sterkte_mg} mg':<9} "
                f"{f'{b.stuks_per_dag}x':<9} {b.stuks_totaal:<8} {b.kop}"
            )
        totalen = ", ".join(f"{n} stuks van {mg} mg" for mg, n in self.stuks_per_sterkte().items())
        regels.append("-" * 88)
        regels.append(f"Totaal: {totalen} ({self.totaal_stuks()} stuks, {self.totaal_nicotine_mg()} mg)")
        return "\n".join(regels)


# --------------------------------------------------------------------------
# De drie schema's
# --------------------------------------------------------------------------
# Blokteksten zijn bewust concreet: ze vertellen wat er die twee weken gebeurt,
# niet hoe iemand zich hoort te voelen.

SCHEMA_LICHT = Schema(
    "licht",
    (
        Blok(1, 2, 8, "Vervangen", "Elke sigaret die je normaal rookte, wordt een stuk kauwgom."),
        Blok(2, 2, 7, "Vasthouden", "Je lichaam went aan nicotine zonder rook. Niets minderen."),
        Blok(3, 2, 6, "Eerste stap omlaag", "Eén stuk minder. Je merkt het nauwelijks, en dat is het punt."),
        Blok(4, 2, 5, "Ritme", "Je gebruikt op vaste momenten, niet meer op gevoel."),
        Blok(5, 2, 3, "Uitdunnen", "Alleen nog rond de twee zwaarste momenten van je dag."),
        Blok(6, 2, 2, "Naar nul", "Twee stuks, dan één, dan het doosje in de la."),
    ),
)

SCHEMA_STANDAARD = Schema(
    "standaard",
    (
        Blok(1, 4, 10, "Vervangen", "Je stopt met roken op dag 1. Elke sigaret wordt een stuk 4 mg."),
        Blok(2, 4, 8, "Stabiel", "De ergste dagen liggen achter je. Twee stuks minder, verder niets."),
        Blok(3, 2, 8, "Halve sterkte", "Zelfde aantal, halve dosis. De grootste stap van het programma."),
        Blok(4, 2, 6, "Minderen", "Je kauwt nog op vaste momenten, niet meer bij elke prikkel."),
        Blok(5, 2, 4, "Uitdunnen", "Vier vaste momenten per dag. De rest zit je uit."),
        Blok(6, 2, 2, "Naar nul", "Afbouwen tot nul. Dag 90 gebruik je niets meer."),
    ),
)

SCHEMA_ZWAAR = Schema(
    "zwaar",
    (
        Blok(1, 4, 12, "Vervangen", "Je stopt met roken op dag 1. Twaalf stuks 4 mg, verspreid over de dag."),
        Blok(2, 4, 10, "Stabiel", "Je houdt de nicotine op peil terwijl je lichaam went aan geen rook."),
        Blok(3, 4, 8, "Eerste stap omlaag", "Vier stuks minder dan waar je begon. Nog steeds 4 mg."),
        Blok(4, 2, 8, "Halve sterkte", "Zelfde aantal, halve dosis. De grootste stap van het programma."),
        Blok(5, 2, 5, "Uitdunnen", "Vijf vaste momenten. Je leert de trek uitzitten in plaats van hem wegkauwen."),
        Blok(6, 2, 3, "Naar nul", "Drie, dan twee, dan niets. Dag 90 is het doosje leeg."),
    ),
)

SCHEMAS: dict[str, Schema] = {
    "licht": SCHEMA_LICHT,
    "standaard": SCHEMA_STANDAARD,
    "zwaar": SCHEMA_ZWAAR,
}


# --------------------------------------------------------------------------
# Zelftest: welk programma past bij deze roker?
# --------------------------------------------------------------------------
# Verkorte Fagerström-logica: hoeveel je rookt en hoe snel na het opstaan je
# eerste sigaret komt, voorspellen samen het beste de zwaarte van de verslaving.

VRAGEN = [
    {
        "id": "aantal",
        "vraag": "Hoeveel sigaretten rook je op een gemiddelde dag?",
        "opties": [
            {"label": "10 of minder", "punten": 0},
            {"label": "11 tot 20", "punten": 2},
            {"label": "21 tot 30", "punten": 3},
            {"label": "Meer dan 30", "punten": 4},
        ],
    },
    {
        "id": "eerste",
        "vraag": "Hoe lang na het opstaan rook je je eerste sigaret?",
        "opties": [
            {"label": "Binnen 5 minuten", "punten": 4},
            {"label": "Na 6 tot 30 minuten", "punten": 3},
            {"label": "Na 31 tot 60 minuten", "punten": 1},
            {"label": "Later dan een uur", "punten": 0},
        ],
    },
    {
        "id": "nacht",
        "vraag": "Word je 's nachts wel eens wakker om te roken?",
        "opties": [{"label": "Ja", "punten": 2}, {"label": "Nee", "punten": 0}],
    },
    {
        "id": "pogingen",
        "vraag": "Hoe vaak heb je al geprobeerd te stoppen?",
        "opties": [
            {"label": "Dit wordt de eerste keer", "punten": 0},
            {"label": "Eén of twee keer", "punten": 1},
            {"label": "Drie keer of vaker", "punten": 2},
        ],
    },
]


def bepaal_programma(antwoorden: dict[str, int]) -> tuple[str, int]:
    """Vertaal de punten van de zelftest naar een programmasleutel.

    `antwoorden` mapt vraag-id naar het aantal punten van het gekozen antwoord.
    Geeft (sleutel, totaalscore) terug.
    """
    geldige_ids = {v["id"] for v in VRAGEN}
    onbekend = set(antwoorden) - geldige_ids
    if onbekend:
        raise ValueError(f"onbekende vragen in antwoorden: {sorted(onbekend)}")
    score = sum(antwoorden.values())
    if score <= 2:
        return "licht", score
    if score <= 6:
        return "standaard", score
    return "zwaar", score


def max_score() -> int:
    return sum(max(o["punten"] for o in v["opties"]) for v in VRAGEN)
