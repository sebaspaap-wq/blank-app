"""De cockpit van QUITTER.

Alles wat je nodig hebt om het bedrijf te besturen op één scherm: wat je
verdient, wat er in de doos gaat, wat het team voor je kan doen, en of een
tekst naar buiten mag.

    uv run streamlit run streamlit_app.py
"""

from __future__ import annotations

import json
import os
from dataclasses import replace

import pandas as pd
import streamlit as st

from quitter.brand import COPY_BANK, MERK, PALET
from quitter.catalog import BTW_GENEESMIDDEL, EXTRAS, KOSTEN, PROGRAMMAS, Kosten
from quitter.compliance import Ernst, controleer
from quitter.finance import (
    SCENARIOS,
    VASTE_KOSTEN,
    Scenario,
    break_even_orders,
    gemiddelde_orderwaarde,
    gevoeligheid_inkoop,
    jaarprojectie,
)
from quitter.paths import DATA
from quitter.taper import SCHEMAS
from quitter.tools import inpaklijst

st.set_page_config(page_title="QUITTER — cockpit", page_icon="🚬", layout="wide")

st.markdown(
    """
    <style>
      h1, h2, h3 { letter-spacing: -0.02em; }
      .rode-draad {
        border-left: 3px solid #FF4B26; padding: 6px 0 6px 16px;
        color: #DCD9D2; font-size: 17px; margin-bottom: 8px;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("QUITTER")
st.markdown(f'<div class="rode-draad">{MERK.rode_draad}</div>', unsafe_allow_html=True)

tabs = st.tabs(
    ["Geld", "Programma's", "Inpakken", "Team", "Merktoets", "Merk", "Wat nu"]
)

# ==========================================================================
# GELD
# ==========================================================================
with tabs[0]:
    st.subheader("Wat verdient dit bedrijf?")
    st.caption(
        "Alle getallen komen uit quitter/catalog.py en quitter/finance.py. "
        "Schuif aan de inkoopprijs en alles rekent opnieuw."
    )

    kolom1, kolom2 = st.columns([1, 2])
    with kolom1:
        prijs4 = st.slider("Inkoopprijs per stuk 4 mg (€)", 0.04, 0.30, 0.16, 0.01)
        prijs2 = st.slider("Inkoopprijs per stuk 2 mg (€)", 0.03, 0.28, 0.14, 0.01)
        tin = st.slider("Metalen blikje (€)", 0.50, 6.00, KOSTEN.tin, 0.10)
        verzending = st.slider("Verzending per order (€)", 0.00, 9.00, KOSTEN.verzending, 0.05)
        cac = st.slider("Advertentiekosten per klant (€)", 0.0, 150.0, 45.0, 5.0)
        orders = st.number_input("Orders per maand", 1, 5000, 100, 10)

    kosten = replace(
        KOSTEN, prijs_per_stuk={4: prijs4, 2: prijs2}, tin=tin, verzending=verzending
    )
    aov, marge = gemiddelde_orderwaarde(kosten)
    scenario = Scenario("nu", int(orders), cac, kosten).bereken()
    be = break_even_orders(cac, kosten)

    with kolom2:
        m1, m2, m3 = st.columns(3)
        m1.metric("Marge per order", f"€{marge:,.2f}", f"{marge/(aov/1.09)*100:.0f}% van de omzet")
        m2.metric("Winst per maand", f"€{scenario['winst_voor_belasting']:,.0f}")
        m3.metric(
            "Break-even",
            "onhaalbaar" if be == float("inf") else f"{be:.0f} orders",
            "bij deze advertentiekosten",
        )
        n1, n2, n3 = st.columns(3)
        n1.metric("Omzet per maand", f"€{scenario['omzet_incl_btw']:,.0f}")
        n2.metric("Advertentiebudget", f"€{scenario['advertentiekosten']:,.0f}")
        n3.metric("Inpakken", f"{scenario['inpakuren_per_maand']:.0f} uur/mnd")

        if marge - cac <= 0:
            st.error(
                f"Bij €{cac:.0f} per klant verlies je €{cac - marge:.2f} op elke bestelling. "
                "Verlaag de advertentiekosten, verhoog de prijs, of onderhandel de inkoop omlaag."
            )
        elif scenario["winst_voor_belasting"] < 0:
            st.warning(
                f"Je verdient wel per order, maar nog niet genoeg om de vaste kosten "
                f"(€{VASTE_KOSTEN.totaal():.0f}/maand) te dekken. Je hebt {be:.0f} orders per maand nodig."
            )
        else:
            st.success(
                f"Elke order levert €{marge - cac:.2f} op na advertenties. "
                f"Vanaf {be:.0f} orders per maand houd je geld over."
            )

    st.divider()
    st.subheader("De belangrijkste knop: de inkoopprijs")
    st.caption(
        "De prijs per stuk kauwgom bepaalt of er ruimte is om te adverteren. Dit is waar de "
        "onderhandeling met de fabrikant over moet gaan — niets anders in dit model heeft zoveel effect."
    )
    tabel = pd.DataFrame(gevoeligheid_inkoop([0.24, 0.20, 0.16, 0.12, 0.09, 0.06], kosten))
    tabel = tabel.rename(columns={
        "prijs_4mg": "inkoop 4 mg", "prijs_2mg": "inkoop 2 mg",
        "marge_per_order": "marge per order", "marge_procent": "marge %",
        "max_cac_bij_25_winst": "max per klant", "break_even_orders_bij_cac_50": "break-even bij €50",
    })
    st.dataframe(tabel.style.format({
        "inkoop 4 mg": "€{:.2f}", "inkoop 2 mg": "€{:.2f}",
        "marge per order": "€{:.2f}", "marge %": "{:.0%}",
        "max per klant": "€{:.2f}", "break-even bij €50": "{:.0f}",
    }), use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Twaalf maanden vooruit")
    groei = st.slider("Groei per maand", 0.0, 0.60, 0.20, 0.05, format="%.0f%%")
    projectie = pd.DataFrame(jaarprojectie(int(orders), groei, cac, 12, kosten))
    st.line_chart(
        projectie.set_index("maand")[["omzet_incl_btw", "winst_voor_belasting", "cumulatieve_winst"]],
        color=["#FF4B26", "#DDFF57", "#6E706B"],
    )
    laatste = projectie.iloc[-1]
    st.caption(
        f"Bij {groei*100:.0f}% groei per maand sta je in maand 12 op {laatste['orders']:.0f} orders, "
        f"€{laatste['omzet_incl_btw']:,.0f} omzet en €{laatste['winst_voor_belasting']:,.0f} winst per maand. "
        f"Over het hele jaar: €{laatste['cumulatieve_winst']:,.0f}."
    )

    with st.expander("De vaste scenario's"):
        st.dataframe(
            pd.DataFrame([replace(s, kosten=kosten).bereken() for s in SCENARIOS]),
            use_container_width=True, hide_index=True,
        )

# ==========================================================================
# PROGRAMMA'S
# ==========================================================================
with tabs[1]:
    st.subheader("De drie programma's")
    kolommen = st.columns(3)
    for kolom, p in zip(kolommen, PROGRAMMAS):
        with kolom:
            st.markdown(f"### {p.naam}")
            st.caption(p.ondertitel)
            st.metric("Prijs", f"€{p.prijs:.0f}", f"marge €{p.marge():.0f}")
            st.write(p.voor_wie)
            stuks = " + ".join(f"{n}× {mg} mg" for mg, n in p.schema.stuks_per_sterkte().items())
            st.caption(f"In de doos: {stuks} ({p.schema.totaal_stuks()} stuks)")

    st.divider()
    keuze = st.selectbox("Bekijk het afbouwschema", list(SCHEMAS), index=1)
    schema = SCHEMAS[keuze]
    st.code(schema.tabel(), language=None)

    dag = st.slider("Wat doet een klant op dag…", 1, 90, 31)
    plan = schema.dagplan(dag)
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Sterkte", f"{plan['sterkte_mg']} mg")
    k2.metric("Stuks vandaag", plan["stuks_vandaag"])
    k3.metric("Blok", f"{plan['blok']} van 6")
    k4.metric("Nog te gaan", f"{plan['resterende_dagen']} dagen")
    st.info(f"**{plan['kop']}** — {plan['doel']}")

    st.divider()
    st.subheader("Extra's die de order groter maken")
    st.dataframe(
        pd.DataFrame([
            {"sku": e.sku, "naam": e.naam, "prijs": e.prijs,
             "marge": round(e.marge, 2), "soort": e.soort, "pitch": e.pitch}
            for e in EXTRAS
        ]),
        use_container_width=True, hide_index=True,
    )

# ==========================================================================
# INPAKKEN
# ==========================================================================
with tabs[2]:
    st.subheader("Wat gaat er in de doos")
    sku = st.radio("Programma", [p.sku for p in PROGRAMMAS], horizontal=True, index=1)
    st.code(inpaklijst(sku), language=None)

    st.divider()
    st.subheader("Voorraad")
    voorraadbestand = DATA / "voorraad.json"
    gegevens = json.loads(voorraadbestand.read_text(encoding="utf-8"))
    tabel = pd.DataFrame(gegevens["artikelen"])
    tabel["tekort"] = tabel["aantal"] < tabel["min_voorraad"]
    st.dataframe(tabel, use_container_width=True, hide_index=True)
    tekorten = tabel[tabel["tekort"]]["naam"].tolist()
    if tekorten:
        st.warning("Bijbestellen: " + ", ".join(tekorten))

    st.divider()
    st.subheader("Hoeveel moet ik inkopen?")
    aantal_orders = st.number_input("Voor hoeveel orders?", 1, 5000, 100, 10, key="inkoop")
    from quitter.finance import MIX

    nodig: dict[int, int] = {}
    for p in PROGRAMMAS:
        deel = MIX[p.sku] * aantal_orders
        for mg, n in p.schema.stuks_per_sterkte().items():
            nodig[mg] = nodig.get(mg, 0) + int(n * deel)
    for mg, n in sorted(nodig.items(), reverse=True):
        st.write(f"- **{n:,} stuks {mg} mg** kauwgom")
    st.write(f"- **{aantal_orders} blikjes**, **{aantal_orders} verzenddozen**, "
             f"**{aantal_orders} afbouwkaarten**, **{aantal_orders} bijsluiters**")
    kosten_inkoop = sum(KOSTEN.prijs_per_stuk[mg] * n for mg, n in nodig.items())
    st.caption(f"Kauwgom kost bij deze aantallen ongeveer €{kosten_inkoop:,.0f} bij de huidige aanname.")

# ==========================================================================
# TEAM
# ==========================================================================
with tabs[3]:
    st.subheader("Het AI-team")
    from quitter.agents import TEAM

    for naam, medewerker in TEAM.items():
        with st.expander(f"{naam} — {medewerker.rol}"):
            st.write(medewerker.opdracht)
            st.caption("Gereedschap: " + ", ".join(
                getattr(f, "__name__", str(f)) for f in medewerker.tools
            ))

    st.divider()
    st.subheader("Geef een opdracht")
    heeft_sleutel = bool(os.environ.get("ANTHROPIC_API_KEY"))
    if not heeft_sleutel:
        st.info(
            "Zet eerst je sleutel: `export ANTHROPIC_API_KEY=...` en start de cockpit opnieuw. "
            "Zonder sleutel werkt alles hierboven wel, alleen het team niet."
        )
    wie = st.selectbox("Wie", list(TEAM), index=0)
    opdracht = st.text_area(
        "Wat moet er gebeuren?",
        placeholder="Schrijf vijf Facebook-advertenties voor mensen die al eerder gefaald zijn met stoppen.",
        height=110,
    )
    if st.button("Uitvoeren", type="primary", disabled=not (heeft_sleutel and opdracht.strip())):
        with st.spinner(f"{wie} is bezig…"):
            from quitter.agents import voer_uit

            resultaat = voer_uit(wie, opdracht)
        st.markdown(resultaat.tekst)
        st.caption(
            f"{len(resultaat.gereedschap_gebruikt)} keer gereedschap gebruikt · "
            f"{resultaat.seconden:.0f} seconden · ongeveer ${resultaat.kosten_dollar:.2f}"
        )

    logboek = DATA / "agent-log.jsonl"
    if logboek.exists():
        with st.expander("Logboek — wat het team tot nu toe gedaan heeft"):
            regels = [json.loads(r) for r in logboek.read_text(encoding="utf-8").splitlines() if r.strip()]
            st.dataframe(
                pd.DataFrame(regels)[["moment", "agent", "opdracht", "seconden", "kosten_dollar"]],
                use_container_width=True, hide_index=True,
            )

# ==========================================================================
# MERKTOETS
# ==========================================================================
with tabs[4]:
    st.subheader("Mag dit naar buiten?")
    st.caption(
        "Plak hier elke advertentie, mail of pagina voordat je hem publiceert. "
        "Rood is blokkerend, geel vraagt om een tweede blik."
    )
    tekst = st.text_area("Tekst", height=200, placeholder="Plak hier je advertentietekst…")
    if tekst.strip():
        bevindingen = controleer(tekst)
        if not bevindingen:
            st.success("Geen bevindingen. Deze tekst komt door de merktoets.")
        for b in bevindingen:
            melding = st.error if b.regel.ernst is Ernst.BLOKKEREND else st.warning
            melding(
                f"**{b.regel.code} — “{b.fragment}”**\n\n"
                f"{b.regel.waarom}\n\n*Beter:* {b.regel.beter}"
            )
        if "kauwgom" in tekst.lower() and "bijsluiter" not in tekst.lower():
            st.warning(
                "De kauwgom wordt genoemd maar 'Lees voor gebruik de bijsluiter' staat er niet bij."
            )

# ==========================================================================
# MERK
# ==========================================================================
with tabs[5]:
    st.subheader("De rode draad")
    st.markdown(f"### {MERK.rode_draad}")
    st.caption(
        "Elke tekst, elke advertentie en elk ontwerp moet hierop terug te voeren zijn. "
        "Kun je een zin niet herleiden tot deze zin, dan hoort hij niet bij QUITTER."
    )
    st.divider()
    k1, k2 = st.columns(2)
    with k1:
        st.markdown("**Wel**")
        for t in MERK.toon_wel:
            st.write("- " + t)
    with k2:
        st.markdown("**Niet**")
        for t in MERK.toon_niet:
            st.write("- " + t)
    st.divider()
    st.markdown("**Zinnen die van ons zijn**")
    for z in COPY_BANK:
        st.write("› " + z)
    st.divider()
    st.markdown("**Kleuren**")
    st.markdown(
        "".join(
            f'<div style="display:inline-block;margin:0 14px 14px 0;text-align:center">'
            f'<div style="width:84px;height:56px;border-radius:8px;background:{k.hex};'
            f'border:1px solid #2A2C29"></div>'
            f'<div style="font-size:12px;color:#9A9C96;margin-top:6px">{k.naam}<br>{k.hex}</div></div>'
            for k in PALET
        ),
        unsafe_allow_html=True,
    )

# ==========================================================================
# WAT NU
# ==========================================================================
with tabs[6]:
    st.subheader("Wat er nu moet gebeuren")
    st.caption("De volgorde is niet vrijblijvend: stap 1 blokkeert alles wat erna komt.")
    stappen = [
        ("Krijg duidelijkheid van MAE Pharma", True,
         "Onder welke handelsvergunning mag je verkopen, wat kost een stuk bij welke afname, "
         "en wat is de minimale eerste order? Zonder dit antwoord is er geen bedrijf. "
         "De vragenlijst staat in docs/08-mae-pharma.md."),
        ("Registreer quitter90.nl en richt de bv op", False,
         "Domein vastleggen, bv oprichten, zakelijke rekening, Mollie-account aanvragen."),
        ("Zet de wachtlijstpagina online", False,
         "De site staat klaar in site/. Zet hem live en verzamel e-mailadressen terwijl je "
         "op de papieren wacht. Elk adres is straks een klant die je niets kost."),
        ("Meld de webshop aan bij de IGJ", False,
         "Online verkoop van geneesmiddelen moet gemeld worden en de site moet het Europese "
         "logo voeren. Zie docs/04-compliance.md."),
        ("Laat de eerste advertenties toetsen", False,
         "Publieksreclame voor zelfzorggeneesmiddelen gaat langs de Keuringsraad. "
         "Reken op doorlooptijd — begin ruim voor je lanceert."),
        ("Eerste 25 dozen zelf inpakken en versturen", False,
         "Klein beginnen, elk foutje eruit halen, en pas daarna geld in advertenties steken."),
    ]
    for titel, gedaan, uitleg in stappen:
        st.checkbox(f"**{titel}**", value=gedaan, key=f"stap-{titel}")
        st.caption(uitleg)

    st.divider()
    st.markdown(
        "**De hele opzet staat in `docs/`.** Begin bij `docs/00-lees-dit-eerst.md`."
    )
