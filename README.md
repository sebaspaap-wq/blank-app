# WOSZ — AI-organisatie

Systeem van vier gescheiden AI-agents (Marketing, Matching, Support, Financieel)
die de dagelijkse operatie van WOSZ uitvoeren, gecoordineerd door een
Directie-agent die rapporteert aan Sebas.

**Status:** alle vier de agents draaien — Matching, Support, Financieel en Marketing.

```
backend/    FastAPI-backend met de agents, de escalatiemotor en de event-bus
frontend/   wosz-app.html — het bestaande dashboard, gekoppeld aan de backend
docs/       De bouwopdracht en het architectuuroverzicht
```

## Aan de slag — gratis en lokaal

Het systeem draait volledig zonder Anthropic-key en zonder database-installatie.
Je hebt alleen [`uv`](https://docs.astral.sh/uv/) nodig.

```bash
cd backend
uv venv --python 3.11 .venv
uv pip install --python .venv/bin/python -e .
cp .env.example .env          # standaard al goed: SQLite, geen API-key
.venv/bin/python -m app.db.seed
.venv/bin/python -m uvicorn app.main:app --reload
```

In een tweede terminal:

```bash
cd frontend && python3 -m http.server 8090
```

Open <http://localhost:8090/wosz-app.html> en klik op **Demo: directie**.

Zonder API-key beslissen de agents op vaste regels in plaats van met Claude;
al het andere werkt hetzelfde. Zie [`backend/README.md`](backend/README.md) voor
de volledige uitleg en de eerste commando's om de agents aan het werk te zetten.

## Twee dingen om te weten voordat je verder bouwt

**Geld gaat nooit automatisch de deur uit.** Er zit geen betaalintegratie in dit
systeem. Uitbetalen kan alleen doordat Sebas het zelf doet, na goedkeuring in het
dashboard. Dat is architecturaal afgedwongen, niet als regel voor een AI —
zie [`backend/app/payouts/README.md`](backend/app/payouts/README.md).

**De arbeidsrechtelijke toets komt eerst.** Randvoorwaarde 6.1 van de
bouwopdracht: laat een arbeidsjurist beoordelen of het model onder de Waadi valt
vóórdat hier echte medewerkersdata of transacties doorheen gaan.
