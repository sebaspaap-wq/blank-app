"""Het rekenmodel: wat verdient QUITTER, en waar zit de knop die het meeste doet.

Dit bestand bestaat om één vraag te beantwoorden: bij welke inkoopprijs,
welke advertentiekosten en welk aantal orders per maand houdt dit bedrijf geld
over? De conclusie staat uitgeschreven in docs/05-financieel.md, maar de
getallen komen hier vandaan — pas een aanname aan en alles rekent opnieuw.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from .catalog import EXTRAS, KOSTEN, PROGRAMMAS, Kosten, Product

# Verdeling van orders over de drie programma's. AANNAME op basis van de
# rookverdeling in Nederland: de meeste rokers zitten rond een pakje per dag.
MIX = {"Q90-L": 0.25, "Q90-S": 0.50, "Q90-Z": 0.25}

# Hoeveel procent van de klanten een extra meeneemt. AANNAME, aan te scherpen
# zodra de eerste honderd orders binnen zijn.
BUMP_ACCEPTATIE = {"X-TIN2": 0.30, "X-PARTNER": 0.08}
UPSELL_ACCEPTATIE = {"X-RESET": 0.06}


@dataclass(frozen=True)
class VasteKosten:
    """Wat het bedrijf per maand kost, ook als je nul verkoopt."""

    hosting_en_tools: float = 45.0     # domein, hosting, mailtool, boekhouding
    ai_kosten: float = 60.0            # het agentteam: content, support, coaching
    opslag: float = 0.0                # zolang je zelf inpakt vanuit huis
    verzekering_en_kvk: float = 40.0   # AANNAME: aansprakelijkheid + bankkosten
    boekhouder: float = 75.0           # AANNAME: bv-administratie

    def totaal(self) -> float:
        return (self.hosting_en_tools + self.ai_kosten + self.opslag
                + self.verzekering_en_kvk + self.boekhouder)


VASTE_KOSTEN = VasteKosten()


def gemiddelde_orderwaarde(kosten: Kosten = KOSTEN) -> tuple[float, float]:
    """(omzet incl. btw, marge) van een gemiddelde order, inclusief extra's."""
    omzet = 0.0
    marge = 0.0
    for p in PROGRAMMAS:
        aandeel = MIX[p.sku]
        omzet += aandeel * p.prijs
        marge += aandeel * p.marge(kosten)
    for extra in EXTRAS:
        kans = BUMP_ACCEPTATIE.get(extra.sku, UPSELL_ACCEPTATIE.get(extra.sku, 0.0))
        omzet += kans * extra.prijs
        marge += kans * extra.marge
    return omzet, marge


@dataclass
class Scenario:
    naam: str
    orders_per_maand: int
    cac: float                 # advertentiekosten per betalende klant
    kosten: Kosten = KOSTEN
    vaste_kosten: VasteKosten = VASTE_KOSTEN
    uur_per_order: float = 0.12  # ~7 minuten inpakken, plakken, wegbrengen

    def bereken(self) -> dict:
        aov, marge_per_order = gemiddelde_orderwaarde(self.kosten)
        bruto = marge_per_order * self.orders_per_maand
        advertenties = self.cac * self.orders_per_maand
        vast = self.vaste_kosten.totaal()
        winst = bruto - advertenties - vast
        uren = self.uur_per_order * self.orders_per_maand
        return {
            "scenario": self.naam,
            "orders": self.orders_per_maand,
            "omzet_incl_btw": aov * self.orders_per_maand,
            "aov": aov,
            "marge_per_order": marge_per_order,
            "brutomarge": bruto,
            "advertentiekosten": advertenties,
            "vaste_kosten": vast,
            "winst_voor_belasting": winst,
            "winst_per_order": winst / self.orders_per_maand if self.orders_per_maand else 0.0,
            "roas": (aov * self.orders_per_maand / advertenties) if advertenties else float("inf"),
            "inpakuren_per_maand": uren,
        }


def break_even_orders(cac: float, kosten: Kosten = KOSTEN,
                      vaste_kosten: VasteKosten = VASTE_KOSTEN) -> float:
    """Hoeveel orders per maand je nodig hebt om quitte te spelen."""
    _, marge = gemiddelde_orderwaarde(kosten)
    per_order = marge - cac
    if per_order <= 0:
        return float("inf")
    return vaste_kosten.totaal() / per_order


def max_cac(gewenste_winst_per_order: float = 25.0, kosten: Kosten = KOSTEN) -> float:
    """Het plafond van je advertentiebod per klant."""
    _, marge = gemiddelde_orderwaarde(kosten)
    return marge - gewenste_winst_per_order


def gevoeligheid_inkoop(prijzen_4mg: list[float], kosten: Kosten = KOSTEN) -> list[dict]:
    """Wat gebeurt er met de marge als de inkoopprijs van kauwgom verandert?

    Dit is de belangrijkste tabel van het hele bedrijf. De inkoopprijs per stuk
    is de enige kostenpost die groot genoeg is om het verdienmodel te maken of
    te breken.
    """
    rijen = []
    for prijs4 in prijzen_4mg:
        prijs2 = round(prijs4 * 0.875, 4)  # 2 mg is doorgaans iets goedkoper
        aangepast = replace(kosten, prijs_per_stuk={4: prijs4, 2: prijs2})
        aov, marge = gemiddelde_orderwaarde(aangepast)
        rijen.append({
            "prijs_4mg": prijs4,
            "prijs_2mg": prijs2,
            "marge_per_order": marge,
            "marge_procent": marge / (aov / 1.09),
            "max_cac_bij_25_winst": marge - 25.0,
            "break_even_orders_bij_cac_50": break_even_orders(50.0, aangepast),
        })
    return rijen


def jaarprojectie(start_orders: int, groei_per_maand: float, cac: float,
                  maanden: int = 12, kosten: Kosten = KOSTEN) -> list[dict]:
    """Twaalf maanden vooruit, met vaste groei per maand."""
    rijen = []
    orders = float(start_orders)
    cumulatief = 0.0
    for maand in range(1, maanden + 1):
        s = Scenario(f"maand {maand}", max(1, round(orders)), cac, kosten)
        r = s.bereken()
        cumulatief += r["winst_voor_belasting"]
        r["cumulatieve_winst"] = cumulatief
        r["maand"] = maand
        rijen.append(r)
        orders *= 1 + groei_per_maand
    return rijen


SCENARIOS = [
    Scenario("Voorzichtig — 30 orders/maand, dure klanten", 30, 60.0),
    Scenario("Realistisch — 100 orders/maand", 100, 45.0),
    Scenario("Het werkt — 300 orders/maand", 300, 40.0),
    Scenario("Vervang je baan — 750 orders/maand", 750, 38.0),
]


def rapport(kosten: Kosten = KOSTEN) -> str:
    aov, marge = gemiddelde_orderwaarde(kosten)
    regels = [
        "GEMIDDELDE ORDER",
        f"  Orderwaarde incl. btw   €{aov:8.2f}",
        f"  Marge na alle kosten    €{marge:8.2f}   (voor advertenties)",
        f"  Plafond advertentiebod  €{max_cac(kosten=kosten):8.2f}   (bij €25 winst per order)",
        "",
        "SCENARIO'S PER MAAND",
        f"  {'scenario':<44}{'orders':>7}{'omzet':>11}{'ads':>10}{'winst':>11}{'uren':>7}",
    ]
    for s in SCENARIOS:
        r = replace(s, kosten=kosten).bereken()
        regels.append(
            f"  {r['scenario']:<44}{r['orders']:>7}"
            f"{r['omzet_incl_btw']:>11,.0f}{r['advertentiekosten']:>10,.0f}"
            f"{r['winst_voor_belasting']:>11,.0f}{r['inpakuren_per_maand']:>7.0f}"
        )
    regels += ["", "ALS DE INKOOPPRIJS VAN KAUWGOM VERANDERT (per stuk 4 mg)",
               f"  {'inkoop':>8}{'marge/order':>13}{'marge %':>10}{'max CAC':>10}{'break-even orders':>20}"]
    for r in gevoeligheid_inkoop([0.22, 0.18, 0.16, 0.12, 0.09, 0.06], kosten):
        be = r["break_even_orders_bij_cac_50"]
        be_txt = "onmogelijk" if be == float("inf") else f"{be:.0f}"
        regels.append(
            f"  €{r['prijs_4mg']:>7.2f}{r['marge_per_order']:>13.2f}"
            f"{r['marge_procent']*100:>9.1f}%{r['max_cac_bij_25_winst']:>10.2f}{be_txt:>20}"
        )
    return "\n".join(regels)
