# QUITTER

**90 dagen. Volgens schema.**

> QUITTER haalt de nicotine er in 90 dagen uit — volgens schema, niet op wilskracht.

Een afbouwprogramma van negentig dagen met nicotinekauwgom in aflopende sterkte: 4 mg,
dan 2 mg, dan niets. In een metalen blikje dat in je broekzak past, met elke ochtend één
mail die vertelt wat je die dag doet.

Deze repository bevat het hele bedrijf: het plan, de website, het rekenmodel, de
afbouwschema's, de reclameregels en het AI-team dat er dagelijks mee werkt.

---

## Beginnen

```bash
uv sync

uv run streamlit run streamlit_app.py     # de cockpit — hier bestuur je het bedrijf
uv run quitter marge                      # het rekenmodel
uv run quitter schema standaard           # het afbouwschema
uv run quitter team                       # wie er in het AI-team zit
uv run quitter check "je advertentietekst" # mag dit naar buiten?

python3 -m http.server -d site 8080       # de website bekijken
uv run python -m pytest tests -q          # de tests
```

Voor het AI-team heb je een sleutel nodig: `export ANTHROPIC_API_KEY=...`

---

## Wat waar staat

```
docs/           Het bedrijfsplan. Begin bij docs/00-lees-dit-eerst.md
site/           De website. Tien pagina's, klaar om te uploaden.
quitter/        Het systeem: merk, catalogus, schema's, rekenmodel, regels, agents.
content/        Wat het team produceert: advertenties, coachmails, social.
data/           Voorraad, orders, en het logboek van de agents.
tests/          Tests die voorkomen dat het bedrijf iets doms doet.
streamlit_app.py De cockpit.
```

| Document | Waarover |
|---|---|
| `docs/00-lees-dit-eerst.md` | Overzicht en de eerste stappen |
| `docs/01-strategie.md` | Markt, klant, concurrentie, risico's |
| `docs/02-merk.md` | Naam, domein, toon, kleur, het blikje |
| `docs/03-product-en-programma.md` | De drie programma's en het afbouwschema |
| `docs/04-compliance.md` | Wat mag en wat niet — de belangrijkste blokkade |
| `docs/05-financieel.md` | Marges, scenario's, wanneer dit je baan vervangt |
| `docs/06-marketing.md` | Trechter, Facebook, wat je meet |
| `docs/07-operatie.md` | Inpakken, inkopen, retour, klantenservice |
| `docs/08-mae-pharma.md` | De twintig vragen aan de leverancier |
| `docs/09-het-ai-team.md` | Wie de agents zijn en wat ze kunnen |
| `docs/10-roadmap.md` | Vier fases, van vandaag tot opschalen |

---

## Drie dingen om te weten

**Nicotinekauwgom is een geneesmiddel.** Onder eigen merk verkopen kan niet zonder de
juiste vergunning. Dat gesprek met de fabrikant blokkeert alles wat erna komt.
Zie `docs/04-compliance.md` en `docs/08-mae-pharma.md`.

**De site draait in wachtlijstmodus.** Bezoekers kunnen de zelftest doen en hun e-mailadres
achterlaten, maar nog niet bestellen. Zet `var MODUS = "wachtlijst"` in
`site/assets/app.js` op `"verkoop"` zodra je mag leveren.

**De inkoopprijs van kauwgom is het hele verdienmodel.** Bij €0,16 per stuk houd je €87
over per order; bij €0,09 is dat €124. Daar gaat elke onderhandeling over.
`uv run quitter marge` laat het zien.

---

## Eén bron van waarheid

Prijzen staan in `quitter/catalog.py`. Schema's in `quitter/taper.py`. De merkbriefing in
`quitter/brand.py`. De reclameregels in `quitter/compliance.py`.

Verander iets daar, draai `uv run python -m quitter.site_build`, en de website, de cockpit,
de agents en de documentatie rekenen met dezelfde getallen.
