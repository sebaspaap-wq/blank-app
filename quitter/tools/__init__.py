"""Het gereedschap dat de agents mogen gebruiken.

Dit zijn gewone Python-functies. quitter/agents/base.py hangt er de
Anthropic-tooldecorator omheen, zodat dit bestand ook los te testen is zonder
dat er ooit een API-call aan te pas komt.

De docstrings zijn niet voor ons — die worden letterlijk het gereedschapsboekje
dat het model leest. Schrijf ze dus alsof je het aan een nieuwe medewerker
uitlegt: wat doet het, wanneer gebruik je het, wat krijg je terug.
"""

from __future__ import annotations

import csv
import json
from datetime import date

from ..brand import MERK
from ..catalog import EXTRAS, PROGRAMMAS, product
from ..compliance import instructie_voor_agents, rapporteer
from ..finance import Scenario, gevoeligheid_inkoop, rapport
from ..paths import DATA, WORTEL, veilig_pad
from ..taper import SCHEMAS, VRAGEN, bepaal_programma

# --------------------------------------------------------------------------
# Kennis over het merk en de regels
# --------------------------------------------------------------------------


def merkbriefing() -> str:
    """Geeft de volledige merkbriefing van QUITTER.

    Gebruik dit voordat je iets schrijft dat een klant onder ogen krijgt: de
    rode draad van het bedrijf, de payoff, de toon die we wel en niet gebruiken,
    en de zinnen die van ons zijn en die je mag hergebruiken.
    """
    return MERK.briefing()


def reclameregels() -> str:
    """Geeft de regels voor wat je wel en niet over het product mag beweren.

    QUITTER verkoopt een geneesmiddel, dus publieksreclame is aan strengere
    regels gebonden dan bij een gewone webshop. Lees dit voordat je advertenties,
    landingspagina's of mails schrijft.
    """
    return instructie_voor_agents()


def controleer_tekst(tekst: str) -> str:
    """Controleert een tekst op verboden of riskante claims.

    Draai dit over ELKE tekst die naar buiten gaat: advertenties, pagina's,
    e-mails, antwoorden aan klanten. Je krijgt per bevinding terug wat er mis is
    en hoe je het beter kunt formuleren, of de melding dat de tekst schoon is.

    Args:
        tekst: De volledige tekst die je wilt controleren.
    """
    return rapporteer(tekst)


# --------------------------------------------------------------------------
# Product en programma
# --------------------------------------------------------------------------


def programma_overzicht() -> str:
    """Geeft alle drie de QUITTER-programma's met prijs, doelgroep en marge.

    Gebruik dit als je moet weten wat we verkopen, aan wie, en voor hoeveel.
    """
    regels = []
    for p in PROGRAMMAS:
        s = p.schema
        stuks = ", ".join(f"{n}x {mg} mg" for mg, n in s.stuks_per_sterkte().items())
        regels.append(
            f"{p.sku} — {p.naam} (€{p.prijs:.2f})\n"
            f"  {p.ondertitel}\n"
            f"  Voor wie: {p.voor_wie}\n"
            f"  In de doos: {stuks} ({s.totaal_stuks()} stuks totaal)\n"
            f"  Marge per order: €{p.marge():.2f} — je mag hier maximaal "
            f"€{p.max_cac():.2f} per klant aan advertenties uitgeven."
        )
    regels.append("\nExtra's die klanten erbij kunnen kopen:")
    for e in EXTRAS:
        regels.append(f"  {e.sku} — {e.naam} (€{e.prijs:.2f}, {e.soort}): {e.pitch}")
    return "\n".join(regels)


def afbouwschema(programma: str) -> str:
    """Geeft het volledige 90-dagen afbouwschema van één programma.

    Args:
        programma: 'licht', 'standaard' of 'zwaar'.
    """
    sleutel = programma.strip().lower()
    if sleutel not in SCHEMAS:
        return f"Onbekend programma '{programma}'. Kies uit: {', '.join(SCHEMAS)}."
    return SCHEMAS[sleutel].tabel()


def dagplan(programma: str, dag: int) -> str:
    """Geeft precies wat een klant op een bepaalde dag van het programma doet.

    Dit is de bron voor de dagelijkse coachmail: welke sterkte, hoeveel stuks,
    in welk blok iemand zit en hoeveel dagen er nog te gaan zijn. Verzin deze
    getallen nooit zelf — haal ze hier op.

    Args:
        programma: 'licht', 'standaard' of 'zwaar'.
        dag: Dagnummer in het programma, 1 tot en met 90.
    """
    sleutel = programma.strip().lower()
    if sleutel not in SCHEMAS:
        return f"Onbekend programma '{programma}'. Kies uit: {', '.join(SCHEMAS)}."
    try:
        plan = SCHEMAS[sleutel].dagplan(int(dag))
    except ValueError as e:
        return str(e)
    return json.dumps(plan, ensure_ascii=False, indent=2)


def zelftest() -> str:
    """Geeft de vragen van de zelftest waarmee klanten hun programma kiezen.

    Handig als je de quiz op de site beschrijft of een klant wilt uitleggen
    waarom hij bij een bepaald programma uitkomt.
    """
    regels = []
    for v in VRAGEN:
        opties = " | ".join(f"{o['label']} ({o['punten']}p)" for o in v["opties"])
        regels.append(f"{v['vraag']}\n  {opties}")
    regels.append("\nUitslag: 0-2 punten = licht, 3-6 = standaard, 7 of meer = zwaar.")
    return "\n".join(regels)


def adviseer_programma(sigaretten_per_dag: int, minuten_tot_eerste_sigaret: int,
                       eerdere_stoppogingen: int = 0) -> str:
    """Bepaalt welk QUITTER-programma bij een roker past.

    Gebruik dit als een klant vraagt welk programma hij nodig heeft.

    Args:
        sigaretten_per_dag: Aantal sigaretten dat de klant per dag rookt.
        minuten_tot_eerste_sigaret: Minuten tussen opstaan en de eerste sigaret.
        eerdere_stoppogingen: Hoe vaak de klant al geprobeerd heeft te stoppen.
    """
    aantal = 0 if sigaretten_per_dag <= 10 else 2 if sigaretten_per_dag <= 20 else 3 if sigaretten_per_dag <= 30 else 4
    eerste = 4 if minuten_tot_eerste_sigaret <= 5 else 3 if minuten_tot_eerste_sigaret <= 30 else 1 if minuten_tot_eerste_sigaret <= 60 else 0
    pogingen = 0 if eerdere_stoppogingen == 0 else 1 if eerdere_stoppogingen <= 2 else 2
    sleutel, score = bepaal_programma(
        {"aantal": aantal, "eerste": eerste, "pogingen": pogingen}
    )
    from ..catalog import product_voor_schema

    p = product_voor_schema(sleutel)
    return (
        f"Score {score}. Advies: {p.naam} ({p.sku}, €{p.prijs:.2f}).\n"
        f"Reden: {p.voor_wie}\n\n{SCHEMAS[sleutel].tabel()}"
    )


# --------------------------------------------------------------------------
# Geld
# --------------------------------------------------------------------------


def financieel_rapport() -> str:
    """Geeft het complete rekenmodel: marge per order, scenario's en break-even.

    Gebruik dit voordat je iets zegt over prijzen, kortingen of
    advertentiebudgetten. Hier staat hoeveel je per klant mag uitgeven.
    """
    return rapport()


def doorrekenen(orders_per_maand: int, kosten_per_klant: float) -> str:
    """Rekent een maand door bij een gegeven aantal orders en advertentiekosten.

    Args:
        orders_per_maand: Hoeveel bestellingen je per maand verwacht.
        kosten_per_klant: Wat een betalende klant je aan advertenties kost (CAC).
    """
    r = Scenario("doorrekening", int(orders_per_maand), float(kosten_per_klant)).bereken()
    return json.dumps(r, ensure_ascii=False, indent=2, default=float)


def inkoop_gevoeligheid() -> str:
    """Laat zien wat de inkoopprijs van kauwgom met de marge doet.

    De belangrijkste tabel van het bedrijf: de prijs per stuk kauwgom bepaalt
    of er ruimte is om te adverteren. Gebruik dit bij onderhandelingen met de
    fabrikant en bij de vraag of een korting kan.
    """
    rijen = gevoeligheid_inkoop([0.22, 0.18, 0.16, 0.12, 0.09, 0.06])
    uit = ["inkoop 4mg | marge/order | max CAC | break-even orders bij CAC €50"]
    for r in rijen:
        be = r["break_even_orders_bij_cac_50"]
        uit.append(
            f"€{r['prijs_4mg']:.2f} | €{r['marge_per_order']:.2f} | "
            f"€{r['max_cac_bij_25_winst']:.2f} | "
            f"{'onmogelijk' if be == float('inf') else f'{be:.0f}'}"
        )
    return "\n".join(uit)


# --------------------------------------------------------------------------
# Winkel: voorraad en orders
# --------------------------------------------------------------------------


def voorraad() -> str:
    """Geeft de actuele voorraad en waarschuwt bij artikelen onder het minimum."""
    pad = DATA / "voorraad.json"
    gegevens = json.loads(pad.read_text(encoding="utf-8"))
    regels = [f"Voorraad per {gegevens['bijgewerkt']}:"]
    for a in gegevens["artikelen"]:
        vlag = "  ⚠ BIJBESTELLEN" if a["aantal"] < a["min_voorraad"] else ""
        regels.append(f"  {a['sku']:<8} {a['naam']:<38} {a['aantal']:>7} {a['eenheid']}{vlag}")
    return "\n".join(regels)


def orders(status: str = "alle") -> str:
    """Geeft de bestellingen uit het orderbestand.

    Args:
        status: Filter op status ('nieuw', 'verzonden', 'geannuleerd') of 'alle'.
    """
    pad = DATA / "orders.csv"
    with pad.open(encoding="utf-8", newline="") as f:
        rijen = list(csv.DictReader(f))
    if status != "alle":
        rijen = [r for r in rijen if r.get("status") == status]
    if not rijen:
        return "Geen bestellingen gevonden. Het orderbestand is nog leeg."
    kop = " | ".join(rijen[0].keys())
    return "\n".join([kop] + [" | ".join(r.values()) for r in rijen])


def inpaklijst(sku: str) -> str:
    """Maakt de inpaklijst voor één programma: wat gaat er precies in de doos.

    Gebruik dit als je zelf gaat inpakken of als je iemand anders moet vertellen
    hoe een doos eruitziet.

    Args:
        sku: Q90-L, Q90-S of Q90-Z.
    """
    try:
        p = product(sku.strip().upper())
    except KeyError as e:
        return str(e)
    s = p.schema
    regels = [f"INPAKLIJST — {p.naam} ({p.sku})", ""]
    for mg, n in s.stuks_per_sterkte().items():
        regels.append(f"  [ ] {n} stuks kauwgom {mg} mg (in blisters)")
    regels += [
        "  [ ] 1 metalen blikje met schuifhuls",
        "  [ ] 1 afbouwkaart op creditcardformaat (schema van dit programma)",
        "  [ ] 1 welkomstkaart met de startcode voor de dagelijkse mail",
        "  [ ] 1 bijsluiter (SmPC) — verplicht, nooit vergeten",
        "  [ ] 1 verzenddoos met opdruk",
        "",
        f"  Controle: {s.totaal_stuks()} stuks totaal, {s.totaal_nicotine_mg()} mg nicotine.",
        "  Sluitzegel op de doos: zonder zegel geen retour bij geopend product.",
    ]
    return "\n".join(regels)


def noteer_voorraad(sku: str, nieuw_aantal: int) -> str:
    """Werkt de voorraad van één artikel bij.

    Args:
        sku: Artikelcode uit de voorraadlijst, bijvoorbeeld GUM-4MG of TIN.
        nieuw_aantal: Het nieuwe aantal op voorraad.
    """
    pad = DATA / "voorraad.json"
    gegevens = json.loads(pad.read_text(encoding="utf-8"))
    for a in gegevens["artikelen"]:
        if a["sku"] == sku.strip().upper():
            oud = a["aantal"]
            a["aantal"] = int(nieuw_aantal)
            gegevens["bijgewerkt"] = date.today().isoformat()
            pad.write_text(json.dumps(gegevens, ensure_ascii=False, indent=2), encoding="utf-8")
            return f"{sku}: {oud} → {nieuw_aantal}."
    return f"Onbekend artikel '{sku}'. Bekijk eerst de voorraad."


# --------------------------------------------------------------------------
# Werk opslaan
# --------------------------------------------------------------------------


def schrijf_bestand(pad: str, inhoud: str) -> str:
    """Slaat werk op in het project. Zo lever je iets af.

    Alleen paden binnen content/, site/ en data/ zijn toegestaan. Gebruik dit
    voor advertentieteksten (content/ads/), mails (content/email/), social posts
    (content/social/) en webpagina's (site/).

    Args:
        pad: Pad ten opzichte van de projectmap, bijvoorbeeld 'content/ads/facebook-week1.md'.
        inhoud: De volledige inhoud van het bestand.
    """
    try:
        doel = veilig_pad(pad, schrijven=True)
    except PermissionError as e:
        return f"Geweigerd: {e}"
    doel.parent.mkdir(parents=True, exist_ok=True)
    doel.write_text(inhoud, encoding="utf-8")
    return f"Opgeslagen: {pad} ({len(inhoud)} tekens)."


def lees_bestand(pad: str) -> str:
    """Leest een bestand uit het project.

    Args:
        pad: Pad ten opzichte van de projectmap, bijvoorbeeld 'docs/05-financieel.md'.
    """
    try:
        bron = veilig_pad(pad, schrijven=False)
    except PermissionError as e:
        return f"Geweigerd: {e}"
    if not bron.exists():
        return f"Bestaat niet: {pad}"
    return bron.read_text(encoding="utf-8")


def toon_map(pad: str = "content") -> str:
    """Laat zien welke bestanden er in een map staan.

    Args:
        pad: Map ten opzichte van de projectmap, bijvoorbeeld 'content/ads'.
    """
    try:
        map_pad = veilig_pad(pad, schrijven=False)
    except PermissionError as e:
        return f"Geweigerd: {e}"
    if not map_pad.exists():
        return f"Bestaat niet: {pad}"
    items = sorted(p.relative_to(WORTEL) for p in map_pad.rglob("*") if p.is_file())
    return "\n".join(str(i) for i in items) or "(leeg)"


ALLE_TOOLS = [
    merkbriefing, reclameregels, controleer_tekst,
    programma_overzicht, afbouwschema, dagplan, zelftest, adviseer_programma,
    financieel_rapport, doorrekenen, inkoop_gevoeligheid,
    voorraad, orders, inpaklijst, noteer_voorraad,
    schrijf_bestand, lees_bestand, toon_map,
]
