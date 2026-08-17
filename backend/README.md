# WOSZ AI-organisatie — backend

Backend voor de vier gescheiden afdelingsagents (Marketing, Matching, Support,
Financieel) en de coordinerende Directie-agent, zoals beschreven in
[`docs/wosz-ai-systeem-bouwopdracht.md`](../docs/wosz-ai-systeem-bouwopdracht.md).

**Status: Fase 1 af.** De Matching-agent draait op echte data en voedt het
bestaande directiedashboard. Support, Financieel en Marketing volgen in Fase 2
en 3; wat daarvan nu al bestaat, staat verderop expliciet benoemd.

---

## Snel starten

```bash
cd backend
uv venv --python 3.11 .venv
uv pip install --python .venv/bin/python -e ".[dev]"

cp .env.example .env          # vul je eigen waarden in
.venv/bin/python -m app.db.seed
.venv/bin/python -m uvicorn app.main:app --reload
```

De API draait dan op <http://localhost:8000>, met documentatie op `/docs`.

Het dashboard erbij:

```bash
cd ../frontend && python3 -m http.server 8090
# open http://localhost:8090/wosz-app.html en klik "Demo: directie"
```

Wijst je backend ergens anders heen, zet dan vóór het laden van de pagina
`window.WOSZ_API_BASE = 'https://...'`. Vergeet niet die origin toe te voegen
aan `WOSZ_CORS_ORIGINS`.

Tests draaien zonder netwerk en zonder PostgreSQL:

```bash
.venv/bin/python -m pytest
```

---

## Hoe het in elkaar zit

```
app/
  config.py        Settings + AgentSettings (twee gescheiden configuratieobjecten)
  core/
    domein.py      Afdeling, Tier, statussen, levelsysteem
    tiers.py       De escalatiemotor: tier 1/2/3
    events.py      Gestructureerde message queue tussen agents
    activity.py    Het activiteitenlog (audit-trail)
  agents/
    base.py        BaseAgent — het enige pad waarlangs een agent iets kan doen
    llm.py         Anthropic-koppeling (function calling)
    matching.py    Matching-agent (Fase 1)
    support.py     Support-agent, voorlopig alleen de no-show-waarschuwing
    directie.py    Coordinator: dagrapport, tellers, beslissingen
  api/
    schemas.py     Het contract met wosz-app.html
    directie.py    /api/directie/*
    matching.py    /api/matching/*
  payouts/         Uitbetalingen — lees de README in die map
  db/              ORM-model, sessies, seed
```

De lagen zijn bewust gescheiden: `db` weet niets van agents, `agents` weet niets
van HTTP, en `api` bevat geen bedrijfslogica. Fase 2 voegt naast
`agents/matching.py` gewoon `agents/financieel.py` toe zonder dat er iets aan de
bestaande lagen hoeft te veranderen.

---

## De vier harde eisen, en waar ze afgedwongen worden

### 1. Geld gaat nooit automatisch de deur uit

Er zit **geen betaalintegratie in dit systeem** — geen Mollie, geen bank-client,
geen betaalcredential. Uitbetalen kan technisch alleen doordat Sebas het zelf
doet, na goedkeuring in het dashboard.

Drie lagen houden dat overeind:

| Laag | Wat het doet |
|---|---|
| Geen client | Er is geen functie die geld verplaatst. Ook een agent met volledige codetoegang kan niets initiëren. |
| `AgentSettings` | Agents krijgen een configuratieobject dat structureel geen betaalvelden bevat. Er valt niets te lekken. |
| Import-guard | `tests/test_betaalscheiding.py` loopt de volledige import-graaf van `app/agents/` na en faalt bij elk pad naar `app.payouts`. |

Details in [`app/payouts/README.md`](app/payouts/README.md).

### 2. Alles wordt gelogd

Elke agentactie loopt via `BaseAgent.voer_uit()` → tier-engine → activiteitenlog.
Loggen is geen losse aanroep die vergeten kan worden: iedere tak van
`behandel_voorstel()` schrijft een regel weg. De logregel bevat tijdstip, tekst,
afdeling en — waar van toepassing — de tier-classificatie.

### 3. Escalatie in drie tiers

| Tier | Gedrag | Mechanisme |
|---|---|---|
| 1 | Agent handelt zelfstandig af | Actie wordt direct uitgevoerd en gelogd |
| 2 | Agent voert uit tenzij Sebas binnen X uur ingrijpt | Beslissing met `deadline_at`; een sweep voert de standaardoptie alsnog uit |
| 3 | Agent wacht altijd op een expliciete keuze | Beslissing zonder deadline; niets gebeurt tot Sebas kiest |

X is instelbaar via `WOSZ_TIER2_DEADLINE_UREN` (standaard 24).

Twee dingen maken dit betrouwbaar. Ten eerste staat *wat* er moet gebeuren als
data in `Beslissing.actie` (een uitvoerder-naam plus parameters), niet als vrije
tekst — uitvoeren hangt dus niet af van hoe een model een zin leest. Ten tweede
filtert de sweep hard op `tier == 2`: een tier 3-beslissing kan langs dat pad
nooit vanzelf doorgaan, zelfs niet als er per ongeluk een deadline op staat. Daar
is een test voor.

### 4. Agents praten alleen via gestructureerde events

De enige weg van agent naar agent is `app/core/events.py`. Die bus accepteert
uitsluitend Pydantic-envelopes met vastgelegde velden en `extra="forbid"`. Een
agent kan dus geen zin naar een collega sturen; er is geen veld om hem in te
zetten. Transport is een Postgres-tabel met polling, zoals hoofdstuk 2
voorschrijft voor de MVP.

Huidige eventtypes:

| Event | Van → naar |
|---|---|
| `uren.gewerkt` | Matching → Financieel |
| `medewerker.no_show` | Matching → Support |
| `medewerker.level_bereikt` | Matching → Financieel |
| `werving.tekort` | Matching → Marketing |

---

## De Matching-agent

Matcht op functie, beschikbaarheid en levelprioriteit, en weigert dubbele
boekingen en geschorste medewerkers.

Claude komt er alleen aan te pas als de regels geen duidelijke winnaar
aanwijzen — twee kandidaten op hetzelfde level met evenveel no-shows. Dan krijgt
het model de shift-eisen en de kandidatenlijst, en kiest het via function calling
één kandidaat met onderbouwing. Die onderbouwing komt letterlijk in het
activiteitenlog terecht.

De keuze van het model wordt gecontroleerd voordat hij wordt uitgevoerd: kiest
het een kandidaat die niet is aangeboden, of levert het geen onderbouwing, dan
valt de agent terug op zijn eigen regels. Zonder `ANTHROPIC_API_KEY` draait de
agent volledig op regels — daardoor draaien de tests zonder netwerk, en legt een
API-storing het matchen niet stil.

Escalatie: standaardmatches en levelupdates zijn tier 1; herhaalde no-shows
(vanaf drie) worden een tier 2-schorsingsvoorstel; urengeschillen zijn tier 3.

---

## Endpoints

### Directie — voedt het dashboard

| Endpoint | Vervangt in `wosz-app.html` |
|---|---|
| `GET /api/directie/activiteiten` | `activityLog` |
| `GET /api/directie/activiteiten/{afdeling}` | de per-afdeling feeds |
| `GET /api/directie/beslissingen` | `decisions` + `decisionsResolved` |
| `POST /api/directie/beslissingen/{id}/kies` | `resolveDecision()` |
| `GET /api/directie/dagrapport` | `dailyReport` |
| `GET /api/directie/dashboard` | de vier tellers |
| `GET /api/directie/uitbetalingen` | — (nieuw) |
| `POST /api/directie/uitbetalingen/export` | — (nieuw) |
| `POST /api/directie/uitbetalingen/{id}/voldaan` | — (nieuw) |

### Matching

| Endpoint | Doet |
|---|---|
| `POST /api/matching/run` | Match alle openstaande shifts |
| `POST /api/matching/matches/{id}/uren` | Boek uren, werk level bij |
| `POST /api/matching/matches/{id}/no-show` | Signaleer no-show (logt bij Matching én Support) |
| `POST /api/matching/matches/{id}/urengeschil` | Leg een geschil voor (tier 3) |

### Waarom de veldnamen zijn zoals ze zijn

De API is op de bestaande frontend gebouwd, niet andersom. Twee details die
makkelijk misgaan en daarom in `tests/test_api_contract.py` vastliggen:

- **`isEuro` en `gekozenOptie` zijn camelCase.** `fmtVal(v.waarde, v.isEuro)` en
  `d.gekozenOptie` lezen die namen letterlijk.
- **`afdeling` mag `null` zijn.** `renderLog()` doet
  `a.afdeling ? ' · ' + DEPT_LABEL[a.afdeling] : ''`, en `DEPT_LABEL` kent alleen
  de vier afdelingen. Een directieregel zou daar letterlijk "undefined" tonen,
  dus die krijgt `null` — precies zoals `resolveDecision()` voorheen een regel
  zonder afdeling toevoegde.

---

## Wat er nog niet is

Eerlijk overzicht, zodat niemand verrast wordt:

- **Support-agent**: alleen de no-show-waarschuwing (tier 1 volgens §3.3). De
  chatbot, de kennisbank en de tier 3-escalatie van klachten komen in Fase 2.
- **Financieel-agent**: bestaat nog niet. `app/agents/ontvangst_fase1.py` bevat
  minimale ontvangers die uren- en level-events vastleggen in het log, zodat de
  bus nu al compleet is. Ze berekenen niets en zetten geen bedragen klaar.
- **Marketing-agent**: idem — het wervingstekort wordt gelogd, meer niet.
- **Directie-agent**: stelt het dagrapport samen uit echte data en beheert
  beslissingen. Notificaties (push/e-mail/WhatsApp) bij tier 3 komen in Fase 3.
- **Authenticatie**: de API is nog open. Vóór livegang hoort hier minimaal
  tokenauthenticatie op de directie-endpoints.
- **Migraties**: tabellen worden met `create_all` aangemaakt. Bij echte data hoort
  Alembic erbij.
- **Externe koppelingen**: Meta Ads en WhatsApp/e-mail zijn nog niet aangesloten.

Zie ook randvoorwaarde 6.1 uit de bouwopdracht: de arbeidsrechtelijke toets
(Waadi) hoort afgerond te zijn vóórdat hier echte medewerkersdata of transacties
doorheen gaan. Dat is geen technisch punt, maar het staat wel tussen dit systeem
en livegang.

---

## Configuratie

Alle instellingen komen uit environment variables; zie `.env.example`. Er staan
geen secrets in de code, en `.env` hoort niet in git.

| Variabele | Doel |
|---|---|
| `WOSZ_DATABASE_URL` | PostgreSQL-connectiestring |
| `ANTHROPIC_API_KEY` | Agent-beslissingen; leeg = regelmodus |
| `WOSZ_ANTHROPIC_MODEL` | Standaard `claude-opus-5` |
| `WOSZ_ANTHROPIC_EFFORT` | `low`/`medium`/`high`/`xhigh`/`max` |
| `WOSZ_TIER2_DEADLINE_UREN` | Termijn voor tier 2 (standaard 24) |
| `WOSZ_EVENT_POLL_SECONDEN` | Pollinterval van de event-worker |
| `WOSZ_CORS_ORIGINS` | Origins die het dashboard mogen serveren |
| `WOSZ_UITBETALING_EXPORT_MAP` | Waar de uitbetalingsexport landt |
