# QUITTER — lees dit eerst

**QUITTER haalt de nicotine er in 90 dagen uit — volgens schema, niet op wilskracht.**

Dat is de rode draad. Alles in dit project komt daaruit voort: het product, de website,
de advertenties, de dagelijkse mails, zelfs de toon waarop de klantenservice antwoordt.
Kun je iets niet herleiden tot die zin, dan hoort het niet bij QUITTER.

---

## Wat is er gebouwd

| Waar | Wat |
|---|---|
| `docs/` | Het bedrijfsplan. Strategie, merk, product, regels, geld, marketing, operatie, roadmap. |
| `site/` | De volledige website. Tien pagina's, klaar om te uploaden. |
| `quitter/` | Het systeem: catalogus, afbouwschema's, rekenmodel, reclameregels, en het AI-team. |
| `streamlit_app.py` | De cockpit. Eén scherm waarop je het bedrijf bestuurt. |
| `content/` | Wat de agents produceren: advertenties, mails, social posts. |
| `tests/` | Tests die voorkomen dat het bedrijf per ongeluk iets doms doet. |

Aan de slag:

```bash
uv sync
uv run streamlit run streamlit_app.py     # de cockpit
uv run quitter marge                      # het rekenmodel in de terminal
uv run quitter team                       # wie er in het AI-team zit
python3 -m http.server -d site 8080       # de website bekijken
```

---

## De drie dingen die je moet weten

### 1. Eén ding blokkeert alles: de handelsvergunning

Nicotinekauwgom is in Nederland een **geneesmiddel**. Onder je eigen merk verkopen kan
niet zomaar: daar hoort een handelsvergunning bij, of een constructie waarbij je onder
de vergunning van de fabrikant verkoopt. Dat is het gesprek dat je met MAE Pharma voert.

Zolang dat niet rond is, verkoop je geen kauwgom. Wat je wél kunt doen staat in stap 2.
De volledige uitleg staat in `docs/04-compliance.md`, de vragen die je aan MAE Pharma
moet stellen in `docs/08-mae-pharma.md`.

### 2. Begin vandaag met de wachtlijst

De website staat klaar en draait standaard in **wachtlijstmodus**: bezoekers kunnen de
zelftest doen en hun e-mailadres achterlaten, maar nog niet bestellen. Zet dat online
zolang je op papieren wacht. Elk adres op die lijst is straks een klant die je geen
advertentiegeld kost. Zet in `site/assets/app.js` de regel `var MODUS = "wachtlijst"`
op `"verkoop"` zodra je mag leveren.

### 3. De inkoopprijs is het hele verdienmodel

Bij een inkoopprijs van €0,16 per stuk kauwgom houd je ongeveer €87 over per order en
mag een klant je maximaal €62 aan advertenties kosten. Bij €0,09 per stuk wordt dat
€124 marge en €99 per klant — en dan wordt Facebook ineens een makkelijke markt.

Onder de €0,10 per stuk is dit een goed bedrijf. Boven de €0,20 is het een moeizaam
bedrijf. Dat is waar je onderhandeling over moet gaan, en over niets anders.
Zie `docs/05-financieel.md`.

---

## De volgorde

1. **MAE Pharma** — onder welke vergunning, tegen welke prijs, met welke minimale afname.
2. **quitter90.nl vastleggen** en de bv oprichten.
3. **Wachtlijst online** — verzamelen terwijl je wacht.
4. **Webshop melden bij de IGJ** en het EU-logo voeren.
5. **Advertenties laten toetsen** door de Keuringsraad.
6. **Eerste 25 dozen** zelf inpakken en versturen. Pas daarna geld in advertenties.

De uitgewerkte planning staat in `docs/10-roadmap.md`.

---

## Wat is er nog niet

Eerlijk zijn over de gaten is nuttiger dan doen alsof ze er niet zijn:

- **Geen betaalprovider.** De bestelpagina heeft een knop zonder Mollie erachter.
- **Geen echte inkoopprijzen.** Alles met AANNAME erbij moet vervangen worden.
- **Geen juridische toets.** De voorwaarden en de privacyverklaring zijn een goede
  eerste versie, geen eindversie.
- **Geen 90 geschreven mails.** Het systeem staat klaar en COACH schrijft ze, maar
  ze zijn nog niet gemaakt (dat kost API-tokens en een sleutel).
- **Geen logo-ontwerp door een ontwerper.** Er ligt een werkbare SVG, geen huisstijlboek.
