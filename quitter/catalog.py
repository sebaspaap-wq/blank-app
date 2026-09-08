"""Wat QUITTER verkoopt, wat het kost en wat er onder de streep overblijft.

Elk getal met AANNAME ernaast is een schatting die vervangen moet worden zodra
de echte inkoopprijzen van de fabrikant binnen zijn. Alles rekent door: pas een
kostenpost aan en de marges, de break-evenprijs per klant en de scenario's
schuiven mee. Zie ook: quitter/finance.py en het tabblad Marge in de cockpit.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .taper import SCHEMAS, Schema

# --------------------------------------------------------------------------
# Kostenaannames
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Kosten:
    """Alle kosten per order, buiten marketing om."""

    # AANNAME: inkoopprijs per stuk kauwgom bij afname van 50.000+ stuks.
    # Ter ijking: consumentenprijs in de drogist ligt rond 0,25-0,30 per stuk.
    # Onder de 0,10 wordt dit bedrijf pas echt winstgevend — daar moet de
    # onderhandeling met de fabrikant over gaan.
    prijs_per_stuk: dict[int, float] = field(
        default_factory=lambda: {4: 0.16, 2: 0.14}
    )
    tin: float = 2.20        # AANNAME: metalen pocketblik met schuifhuls, vanaf 1.000 stuks
    verzenddoos: float = 0.90  # AANNAME: brievenbusdoos met opdruk + vulling
    drukwerk: float = 1.10     # AANNAME: afbouwkaart, welkomstkaart, SmPC/bijsluiter
    verzending: float = 4.95   # AANNAME: PostNL pakket NL, klein tarief
    betaalkosten_vast: float = 0.29   # Mollie/Stripe per transactie
    betaalkosten_procent: float = 0.025
    retourpercentage: float = 0.03    # ongeopend teruggestuurd, product blijft verkoopbaar
    verlies_percentage: float = 0.01  # breuk, kwijtgeraakte pakketten, coulance

    def gum_kosten(self, schema: Schema) -> float:
        return sum(self.prijs_per_stuk[mg] * n for mg, n in schema.stuks_per_sterkte().items())

    def verpakking(self) -> float:
        return self.tin + self.verzenddoos + self.drukwerk


KOSTEN = Kosten()

# BTW. Een geregistreerd geneesmiddel valt in Nederland onder het lage tarief.
# VERIFIEREN met de Belastingdienst zodra de handelsvergunning rond is: zolang
# je het programma zonder geregistreerd geneesmiddel verkoopt, is het 21%.
BTW_GENEESMIDDEL = 0.09
BTW_ALGEMEEN = 0.21


# --------------------------------------------------------------------------
# Producten
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Product:
    sku: str
    naam: str
    ondertitel: str
    prijs: float           # consumentenprijs inclusief btw
    schema_sleutel: str
    voor_wie: str
    btw: float = BTW_GENEESMIDDEL

    @property
    def schema(self) -> Schema:
        return SCHEMAS[self.schema_sleutel]

    @property
    def prijs_ex_btw(self) -> float:
        return self.prijs / (1 + self.btw)

    def kostprijs(self, kosten: Kosten = KOSTEN) -> float:
        """Alles wat één verzonden order kost, exclusief marketing."""
        product = kosten.gum_kosten(self.schema) + kosten.verpakking()
        logistiek = kosten.verzending
        betaal = kosten.betaalkosten_vast + kosten.betaalkosten_procent * self.prijs
        risico = (kosten.retourpercentage * (kosten.verzending + kosten.verpakking())
                  + kosten.verlies_percentage * (product + kosten.verzending))
        return product + logistiek + betaal + risico

    def marge(self, kosten: Kosten = KOSTEN) -> float:
        """Wat er per order overblijft vóór advertentiekosten."""
        return self.prijs_ex_btw - self.kostprijs(kosten)

    def marge_procent(self, kosten: Kosten = KOSTEN) -> float:
        return self.marge(kosten) / self.prijs_ex_btw

    def max_cac(self, gewenste_winst: float = 25.0, kosten: Kosten = KOSTEN) -> float:
        """Het maximum dat je per klant aan advertenties mag uitgeven."""
        return self.marge(kosten) - gewenste_winst

    def regel(self, kosten: Kosten = KOSTEN) -> str:
        return (
            f"{self.sku:<8} {self.naam:<24} €{self.prijs:>6.2f}  "
            f"kostprijs €{self.kostprijs(kosten):>6.2f}  "
            f"marge €{self.marge(kosten):>6.2f} ({self.marge_procent(kosten)*100:>4.1f}%)  "
            f"max CAC €{self.max_cac(kosten=kosten):>6.2f}"
        )


PROGRAMMAS: list[Product] = [
    Product(
        sku="Q90-L",
        naam="QUITTER 90 Licht",
        ondertitel="Voor wie tot 10 sigaretten per dag rookt",
        prijs=149.00,
        schema_sleutel="licht",
        voor_wie="Je rookt maximaal een half pakje en je eerste sigaret kan wachten tot na het ontbijt.",
    ),
    Product(
        sku="Q90-S",
        naam="QUITTER 90 Standaard",
        ondertitel="Voor wie een pakje per dag rookt",
        prijs=199.00,
        schema_sleutel="standaard",
        voor_wie="Je rookt tussen de 10 en 20 sigaretten per dag en de eerste komt binnen een uur na het opstaan.",
    ),
    Product(
        sku="Q90-Z",
        naam="QUITTER 90 Zwaar",
        ondertitel="Voor wie meer dan een pakje per dag rookt",
        prijs=249.00,
        schema_sleutel="zwaar",
        voor_wie="Je rookt meer dan 20 sigaretten per dag, of je eerste sigaret komt binnen vijf minuten na het opstaan.",
    ),
]


# --------------------------------------------------------------------------
# Wat de gemiddelde order groter maakt
# --------------------------------------------------------------------------
# Dit is waar het geld zit. Een tweede product in dezelfde doos kost bijna niets
# extra aan verzending en marketing, en tilt de gemiddelde orderwaarde omhoog.
# Elke euro extra AOV is een euro die je meer mag bieden op Facebook.


@dataclass(frozen=True)
class Extra:
    sku: str
    naam: str
    prijs: float
    kostprijs: float
    soort: str  # "bump" (afrekenscherm), "upsell" (na bestelling), "abonnement"
    pitch: str

    @property
    def marge(self) -> float:
        return self.prijs / (1 + BTW_ALGEMEEN) - self.kostprijs


EXTRAS: list[Extra] = [
    Extra(
        sku="X-TIN2",
        naam="Tweede blikje",
        prijs=14.00,
        kostprijs=2.20,
        soort="bump",
        pitch="Eén in je jas, één in de auto. Je bent nooit zonder.",
    ),
    Extra(
        sku="X-PARTNER",
        naam="Partnerkorting: tweede programma",
        prijs=129.00,
        kostprijs=95.00,
        soort="bump",
        pitch="Samen stoppen werkt beter dan alleen. Tweede programma met 35% korting.",
    ),
    Extra(
        sku="X-RESET",
        naam="QUITTER Reset",
        prijs=59.00,
        kostprijs=28.00,
        soort="upsell",
        pitch="Teruggevallen? Vier weken 2 mg om terug op schema te komen, zonder opnieuw te beginnen.",
    ),
    Extra(
        sku="X-COACH",
        naam="QUITTER Coach+",
        prijs=9.00,
        kostprijs=0.60,
        soort="abonnement",
        pitch="De app: dagelijks inchecken, trekmomenten loggen, en op je zwaarste uur een bericht dat je door dat uur trekt.",
    ),
]


# --------------------------------------------------------------------------
# Overzichten
# --------------------------------------------------------------------------


def product(sku: str) -> Product:
    for p in PROGRAMMAS:
        if p.sku == sku:
            return p
    raise KeyError(f"onbekende sku: {sku}")


def product_voor_schema(sleutel: str) -> Product:
    for p in PROGRAMMAS:
        if p.schema_sleutel == sleutel:
            return p
    raise KeyError(f"geen programma voor schema: {sleutel}")


def prijslijst(kosten: Kosten = KOSTEN) -> str:
    regels = ["PROGRAMMA'S", "-" * 104]
    regels += [p.regel(kosten) for p in PROGRAMMAS]
    regels += ["", "EXTRA'S", "-" * 104]
    for e in EXTRAS:
        regels.append(
            f"{e.sku:<10} {e.naam:<34} €{e.prijs:>6.2f}  marge €{e.marge:>6.2f}  ({e.soort})"
        )
    return "\n".join(regels)
