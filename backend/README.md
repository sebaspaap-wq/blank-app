# WOSZ AI-organisatie — backend

Backend voor de vier gescheiden afdelingsagents (Marketing, Matching, Support,
Financieel) en de coordinerende Directie-agent, zoals beschreven in
[`docs/wosz-ai-systeem-bouwopdracht.md`](../docs/wosz-ai-systeem-bouwopdracht.md).

**Status: alle vier de agents draaien.** Matching, Support, Financieel en
Marketing werken op echte data en voeden het bestaande directiedashboard. Wat er
nog niet is, staat verderop expliciet benoemd.

---

## Snel starten — gratis, lokaal, zonder API-key

**De makkelijkste manier is dubbelklikken op `start.command` (Mac/Linux) of
`start-windows.bat` (Windows) in de hoofdmap.** Dat script doet alles hieronder
voor je. De rest van deze sectie is voor wie het liever zelf typt.

Het systeem draait volledig zonder Anthropic-key en zonder database-installatie.
Je betaalt dus niets en er gaat geen enkele aanvraag het internet op.

Je hebt alleen [`uv`](https://docs.astral.sh/uv/) nodig:

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Dan, in de map van dit project:

```bash
cd backend
uv venv --python 3.11 .venv
uv pip install --python .venv/bin/python -e .

cp .env.example .env          # standaard al goed: SQLite, geen API-key
.venv/bin/python -m app.db.seed    # voorbeeldgegevens
.venv/bin/python -m app.db.demo    # laat de agents één ronde draaien
.venv/bin/python -m uvicorn app.main:app --reload
```

Op Windows is het `.venv\Scripts\python` in plaats van `.venv/bin/python`.

De API draait nu op <http://localhost:8000> (documentatie op `/docs`). Start in
een **tweede terminal** het dashboard:

```bash
cd frontend
python3 -m http.server 8090
```

Open <http://localhost:8090/wosz-app.html> en klik op **Demo: directie**.

### Iets doen, en het zien gebeuren

`app.db.demo` heeft de agents al één ronde laten draaien, dus het dashboard is
gevuld. Wil je ze nog iets laten doen:

```bash
curl -X POST localhost:8000/api/matching/run
curl -X POST "localhost:8000/api/marketing/kalender/weekplanning?aantal=3"
curl -X POST localhost:8000/api/support/vragen \
  -H 'content-type: application/json' \
  -d '{"vraag":"Hoe kan ik me afmelden voor mijn shift?","medewerker_id":2}'
```

Ververs het dashboard: het activiteitenlog, de afdelingsfeeds en het dagrapport
vullen zich. Wil je liever klikken dan curl'en, gebruik dan <http://localhost:8000/docs>
— daar staan alle endpoints met een "Try it out"-knop.

Opnieuw beginnen: stop de server, verwijder `backend/wosz.db`, en draai de seed
opnieuw.

### Wat je mist zonder API-key

Alles werkt, maar op vaste regels in plaats van met Claude:

| Agent | Zonder key | Met key |
|---|---|---|
| Matching | Kiest op levelprioriteit, no-shows en spreiding | Claude kiest tussen kandidaten die op die punten gelijk staan, met onderbouwing |
| Support | Zoekt op trefwoorden; geen duidelijke treffer = escaleren naar jou | Claude bepaalt welk kennisbankantwoord bij de vraag hoort |
| Marketing | Gebruikt de voorbeeldteksten bij de hoek | Claude schrijft een nieuwe post binnen die hoek |

De tier-escalatie, de event-bus, het activiteitenlog, de facturen, de
uitbetalingen en de content-kalender werken in beide gevallen identiek. Wil je
Claude er later bij, zet dan `ANTHROPIC_API_KEY` in je `.env` — verder verandert
er niets.

### Tests

```bash
uv pip install --python .venv/bin/python -e ".[dev]"
.venv/bin/python -m pytest
```

Draaien zonder netwerk en zonder PostgreSQL.

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
    sjablonen.py   Berichtsjablonen — alles wat Support kan versturen
    matching.py    Matching-agent
    support.py     Support-agent: kennisbank, onboarding, escalatie
    financieel.py  Financieel-agent: uren, facturen, bonussen
    marketing.py   Marketing-agent: content-kalender, budget, resultaten
    directie.py    Coordinator: dagrapport, tellers, beslissingen
  api/
    schemas.py     Het contract met wosz-app.html
    directie.py    /api/directie/*
    matching.py    /api/matching/*
    support.py     /api/support/*
    financieel.py  /api/financieel/*
    marketing.py   /api/marketing/*
  payouts/         Uitbetalingen — lees de README in die map
  db/              ORM-model, sessies, seed
```

De lagen zijn bewust gescheiden: `db` weet niets van agents, `agents` weet niets
van HTTP, en `api` bevat geen bedrijfslogica. Elke fase voegde een agent toe
zonder dat er iets aan de bestaande lagen veranderde — dat was de opzet en het
heeft standgehouden.

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

## De Support-agent

Beantwoordt vragen, verstuurt onboarding, en waarschuwt namens Matching bij
no-shows.

Paragraaf 3.3 eist dat Support **geen inhoudelijke toezeggingen doet over geld,
tarieven of contractvoorwaarden**. Net als bij de uitbetalingen is dat hier geen
instructie maar een constructie:

| Grens | Hoe die vaststaat |
|---|---|
| De agent schrijft nooit de tekst die een medewerker leest | Versturen kan alleen via een geregistreerd sjabloon in `app/agents/sjablonen.py`. Er is geen parameter waarin vrije tekst mee kan liften. |
| Sjablonen kunnen geen geld beloven | Bij registratie wordt elk sjabloon gecontroleerd op bedragen, tarieven en contractvoorwaarden. Een sjabloon dat dat bevat, laat de applicatie niet starten. |
| Inhoudelijke antwoorden zijn door een mens geschreven | Antwoorden komen uit de kennisbank. Claude kiest wélk antwoord past; het formuleert er nooit een. Routeren, niet schrijven. |
| Twijfel gaat naar Sebas | Klacht of conflict, vraag buiten de kennisbank, of een onderwerp met `vereist_mens`: allemaal tier 3. De agent gokt niet. |

`GET /api/support/sjablonen` geeft de volledige verzameling teksten die ooit
namens WOSZ verstuurd kan worden. Handig om periodiek door te lezen.

**De `vereist_mens`-vlag is jouw knop.** Kennisbankitems over geld, tarieven en
contracten staan standaard op `vereist_mens=True`: die worden nooit automatisch
beantwoord, ook al staat er een goedgekeurd antwoord. De agent escaleert dan en
vermeldt welk antwoord hij zou hebben gebruikt, zodat jij het met één klik kunt
bevestigen. Vind je dat te streng voor een specifiek item, zet de vlag dan uit —
dat is een datawijziging, geen codewijziging.

Er gaat nog niets echt de deur uit: berichten worden gerenderd en als `klaar` in
de outbox gezet (`GET /api/support/berichten`), zodat je de teksten kunt nalezen
voordat er ooit een WhatsApp- of e-mailkoppeling op wordt aangesloten.

---

## De Financieel-agent

Verwerkt gewerkte uren tot factuurconcepten per bedrijf per periode, en berekent
level- en vriendenbonussen.

Escalatie volgt paragraaf 3.4 letterlijk: uren verwerken en factuurconcepten
opstellen is tier 1, en **élke uitbetaling is tier 3, zonder uitzondering**. Een
factuur naar een bedrijf sturen valt daar niet onder — daar komt geld binnen, er
gaat niets uit.

Deze agent kan geen geld verplaatsen, en dat is geen kwestie van terughoudend
zijn: hij kan `app.payouts` niet importeren. Hij verwijst naar de
goedkeuringsuitvoerder alleen bij naam, als string in de beslissing. Een test
bewaakt dat.

---

## De Marketing-agent

Plant social content op de kalender, stuurt advertentiebudget bij, en beoordeelt
campagneresultaten.

Paragraaf 3.1 geeft deze agent tier 1 voor "contentplanning binnen bestaande
huisstijl" en "kleine budgetschuiven binnen bandbreedte". Dat is hier zo
gebouwd dat de grenzen niet van goed gedrag afhangen:

| Grens | Hoe die vaststaat |
|---|---|
| Er wordt niets gepubliceerd | Er is geen Meta Ads-koppeling en geen social-koppeling. De kalender is een werklijst; Sebas plaatst de posts. |
| Een budgetschuif kan geen nieuw geld maken | `verschuif_budget` is een overboeking: hetzelfde bedrag gaat er bij de ene campagne af als er bij de andere bij komt. Het totaal is behouden per constructie, niet per afspraak. |
| Grote schuiven kunnen niet zelfstandig | Boven de bandbreedte gooit de tier 1-functie een `BandbreedteOverschredenError`. De agent kan hem niet forceren; er is geen tweede pad. |
| De agent verzint geen nieuwe hoek | Content plannen kan alleen op een goedgekeurde hoek uit `huisstijl_hoeken`. Een nieuwe richting is tier 3. |
| Posts noemen nooit een bedrag | Wat het model schrijft wordt gecontroleerd op bedragen en tarieven voordat het op de kalender komt. Wat iemand verdient verschilt per shift; dat hoort niet in een advertentie. |

**Nieuw budget is altijd tier 3.** "Meer geld" en "geld anders verdelen" zijn
twee verschillende methodes, en alleen de tweede is zelfstandig. Ook een
afwijking van meer dan 25% ten opzichte van de verwachte kosten per aanmelding
gaat naar Sebas — de agent pauzeert geen campagne op eigen houtje.

**De lus met Matching is nu dicht.** Een `werving.tekort`-event leidt tot echte
actie: de agent plant extra content voor de functie die openstaat, ruim vóór de
shiftdatum, en verschuift bij twee of meer open plekken ook budget naar de
campagne die op dat moment de goedkoopste aanmeldingen levert. In Fase 1 werd
dat event alleen gelogd.

Budgetwijzigingen komen op een werklijst (`GET /api/marketing/budgetmutaties`)
die Sebas zelf doorvoert in Ads Manager — hetzelfde patroon als bij de
uitbetalingen.

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

### Support

| Endpoint | Doet |
|---|---|
| `POST /api/support/vragen` | Handel een binnengekomen vraag af (tier 1 of tier 3) |
| `POST /api/support/onboarding` | Stuur het welkomstbericht (tier 1) |
| `GET /api/support/berichten` | De outbox, met de volledige tekst |
| `POST /api/support/berichten/{id}/verstuurd` | Leg vast dat een bericht is verstuurd |
| `GET /api/support/sjablonen` | Alles wat Support kan versturen |

### Financieel

| Endpoint | Doet |
|---|---|
| `GET /api/financieel/facturen` | Factuurconcepten, eventueel per periode |
| `POST /api/financieel/periodes/{periode}/afsluiten` | Rond de concepten van een periode af (tier 1) |

### Marketing

| Endpoint | Doet |
|---|---|
| `GET /api/marketing/kalender` | De content-kalender |
| `POST /api/marketing/kalender` | Plan één item in (tier 1) |
| `POST /api/marketing/kalender/weekplanning` | Vul de komende week (tier 1) |
| `POST /api/marketing/kalender/{id}/gepubliceerd` | Vink af dat je hem hebt geplaatst |
| `POST /api/marketing/kalender/{id}/afwijzen` | Haal een item van de kalender |
| `GET /api/marketing/campagnes` | Campagnes met budget en bandbreedte |
| `POST /api/marketing/campagnes/budget/verschuiven` | Verschuif budget (tier 1 binnen de bandbreedte) |
| `POST /api/marketing/campagnes/budget/verhogen` | Vraag nieuw budget (tier 3) |
| `GET /api/marketing/budgetmutaties` | Werklijst voor Ads Manager |
| `POST /api/marketing/budgetmutaties/{id}/doorgevoerd` | Vink af dat je hem hebt doorgevoerd |
| `POST /api/marketing/hoeken/voorstellen` | Stel een nieuwe hoek voor (tier 3) |
| `POST /api/marketing/resultaten` | Voer dagcijfers in |
| `POST /api/marketing/resultaten/beoordelen` | Vergelijk met de verwachting |

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

- **Niets gaat echt naar buiten.** Support rendert berichten in een outbox,
  Marketing plant posts op een kalender, en budgetwijzigingen komen op een
  werklijst. Er is geen WhatsApp-, e-mail-, social- of Meta Ads-koppeling. Dat
  is een bewuste keuze: eerst beoordelen, dan pas aansluiten. De
  Meta Business-verificatie en het WhatsApp Business-traject lopen sowieso.
- **Directie-agent**: stelt het dagrapport samen uit echte data en beheert
  beslissingen. Notificaties (push/e-mail/WhatsApp) bij tier 3-items staan nog
  open — die vragen om een kanaal, en dat is er nog niet.
- **A/B-testen**: campagneresultaten worden vergeleken met een verwachting per
  campagne. Een echte A/B-opzet met varianten binnen één campagne zit er nog
  niet in.
- **Authenticatie**: de API is nog open. Vóór livegang hoort hier minimaal
  tokenauthenticatie op de directie-endpoints.
- **Migraties**: tabellen worden met `create_all` aangemaakt. Bij echte data
  hoort Alembic erbij.
- **Beheerschermen**: kennisbank, huisstijl-hoeken en campagnes komen uit de
  seed. Zodra Sebas ze echt gaat vullen, horen daar schermen bij.

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
