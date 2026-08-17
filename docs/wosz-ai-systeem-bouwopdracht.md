# WOSZ AI-organisatie — bouwopdracht

## Doel
Bouw een systeem van vier gescheiden AI-agents (Marketing, Matching, Support, Financieel) die zelfstandig de dagelijkse operatie van WOSZ uitvoeren, gecoördineerd door een Directie-agent die rapporteert aan en beslissingen voorlegt aan de menselijke eigenaar (Sebas). Geen enkele agent voert een onomkeerbare actie (geld, contractwijziging, publieke communicatie namens WOSZ) uit zonder menselijke goedkeuring waar dat relevant is.

Zie `wosz-ai-architectuur.html` voor het visuele overzicht en `wosz-app.html` (directie-rol) voor hoe de front-end dit al simuleert — dat is de UI die dit systeem moet gaan voeden met echte data.

---

## 1. Architectuuroverzicht

```
Sebas (mens)
   ↑ dagrapport, beslissingen ter goedkeuring
Directie-agent (coördinator)
   ↑ statusupdates
┌───────────┬───────────┬───────────┬─────────────┐
│ Marketing │ Matching  │ Support   │ Financieel  │
└───────────┴───────────┴───────────┴─────────────┘
   ↓ acties & data
Externe koppelingen (Meta Ads, database, WhatsApp/e-mail, betaal-API)
```

Elke agent is een losstaande service/module met een eigen systeemprompt, eigen tools (function calling), en een eigen stuk van de database. Agents communiceren niet rechtstreeks met elkaar via vrije tekst, maar via gestructureerde events op een message queue — dat voorkomt dat afdelingen "buiten hun boekje" gaan en maakt het systeem controleerbaar en logbaar.

---

## 2. Aanbevolen techstack

- **Backend**: Python, FastAPI (async, geschikt voor agent-orchestratie)
- **Agent-orchestratie**: Anthropic API (Claude) met function calling per agent; een lichte orchestrator-laag (geen zware framework-afhankelijkheid nodig — begin met eigen eventloop, geen LangChain-vereiste)
- **Message queue tussen agents**: Redis (pub/sub) of simpele Postgres-tabel met polling voor de MVP — Redis pas nodig bij schaal
- **Database**: PostgreSQL — gebruikers, shifts, matches, uren, facturen, beslissingen, activiteitenlog
- **Scheduler**: cron-achtige taken (bijv. APScheduler of een simpele cronjob) voor terugkerende taken: dagrapport samenstellen, dagelijkse contentplanning
- **Frontend**: hergebruik de bestaande `wosz-app.html`-structuur; vervang de gesimuleerde `activityLog`/`decisions`-arrays door echte API-calls naar de backend (`GET /api/directie/activiteiten`, `GET /api/directie/beslissingen`, `POST /api/directie/beslissingen/{id}/kies`)
- **Hosting**: begin simpel (bijv. Render, Railway of een enkele VPS) — geen kubernetes-cluster nodig voor dit volume

---

## 3. Per-agent specificatie

### 3.1 Marketing-agent
**Verantwoordelijk voor**: social content plannen, advertentiebudget bijsturen binnen vooraf ingestelde grenzen, A/B-testresultaten interpreteren.

**Tools/permissies**:
- Lees/schrijf toegang tot content-kalender (database)
- Meta Ads API — mag budget verschuiven binnen een vooraf ingestelde bandbreedte (bijv. max 20% per dag zonder goedkeuring)
- Mag GEEN nieuwe advertenties publiceren zonder dat de content al is goedgekeurd in een contentkalender die Sebas periodiek bekijkt

**Escalatieregels**:
- Tier 1 (zelfstandig): contentplanning binnen bestaande huisstijl, kleine budgetschuiven binnen bandbreedte
- Tier 3 (wacht op Sebas): nieuw budget aanvragen, nieuwe hoek/campagne-richting, negatieve resultaten die > 25% afwijken van verwachting

### 3.2 Matching-agent
**Verantwoordelijk voor**: shifts koppelen aan medewerkers, no-shows signaleren, levelsysteem/uren bijhouden.

**Tools/permissies**:
- Lees/schrijf toegang tot shifts, medewerkersprofielen, matches
- Mag automatisch matchen op basis van vooraf gedefinieerde regels (beschikbaarheid, functie, level-prioriteit)
- Stuurt events naar Support-agent (no-show) en Financieel-agent (uren)

**Escalatieregels**:
- Tier 1: standaardmatches, levelupdates
- Tier 2: bij herhaaldelijke no-shows van dezelfde medewerker → voorstel tot schorsing, tenzij Sebas binnen 24 uur ingrijpt
- Tier 3: geschillen tussen medewerker en bedrijf over gewerkte uren

### 3.3 Support-agent
**Verantwoordelijk voor**: vragen beantwoorden (chatbot), onboarding-berichten, waarschuwingen versturen namens Matching-agent.

**Tools/permissies**:
- Lees toegang tot FAQ/kennisbank, medewerkers- en bedrijfsprofielen
- Mag zelfstandig standaardberichten versturen (WhatsApp/e-mail template-based)
- Mag GEEN inhoudelijke toezeggingen doen over geld, tarieven, of contractvoorwaarden

**Escalatieregels**:
- Tier 1: standaardvragen, onboarding, no-show-waarschuwingen
- Tier 3: klachten, conflicten, elke vraag die buiten de kennisbank valt — direct escaleren naar Sebas, niet laten "gokken"

### 3.4 Financieel-agent
**Verantwoordelijk voor**: uren berekenen, facturen opstellen, bonussen (vrienden + levels) berekenen en klaarzetten.

**Tools/permissies**:
- Lees toegang tot uren-data van Matching-agent
- Schrijf toegang tot facturen/bonus-conceptrecords (status: "klaar ter goedkeuring")
- **Mag nooit** een daadwerkelijke uitbetaling of banktransactie initiëren — dat vereist altijd een expliciete klik van Sebas in het directiedashboard

**Escalatieregels**:
- Tier 1: uren berekenen, factuurconcepten opstellen
- Tier 3: élke uitbetaling, zonder uitzondering

### 3.5 Directie-agent (coördinator)
**Verantwoordelijk voor**: verzamelen van rapportages van alle agents, dagrapport samenstellen, bepalen welke acties tier 2/3 zijn en dus naar Sebas moeten, activiteitenlog bijhouden.

**Tools/permissies**:
- Leestoegang tot alle afdelingsdata
- Schrijftoegang tot de `beslissingen`-tabel (aanmaken van beslissingsverzoeken)
- Stuurt notificaties (push/e-mail/WhatsApp) naar Sebas bij tier 3-items

---

## 4. Datamodel (kernentiteiten)

```
users            (id, naam, rol: medewerker/horeca/directie, contactgegevens)
shifts           (id, bedrijf_id, datum, tijd, functie, aantal_gevraagd, status)
matches          (id, shift_id, medewerker_id, status, uren_gewerkt)
levels           (medewerker_id, huidig_level, seizoen_uren)
referrals        (id, medewerker_id, vriend_id, uren_vriend, bonus_status)
facturen         (id, bedrijf_id, periode, uren, bedrag, status)
beslissingen     (id, titel, situatie, opties[json], urgentie, status, gekozen_optie, afdeling_bron)
activiteitenlog  (id, tijd, tekst, afdeling)
```

---

## 5. Externe koppelingen die nodig zijn

| Koppeling | Doel | Opmerking |
|---|---|---|
| Meta Ads API | Marketing-agent stuurt campagnes bij | Vereist Meta Business-verificatie |
| WhatsApp Business API of e-mail (bijv. Postmark) | Support-agent communicatie | WhatsApp vereist goedkeuringsproces bij Meta |
| Betaal-API (bijv. Mollie) | Uitbetalingen — **alleen na goedkeuring door Sebas** | Nooit automatisch triggeren vanuit de Financieel-agent zelf |
| Bestaande WOSZ-database | Alle agents lezen/schrijven hierop | Zie datamodel hierboven |

---

## 6. Belangrijke randvoorwaarden (niet overslaan)

1. **Arbeidsrechtelijke check eerst.** Zoals eerder vastgesteld: laat een arbeidsjurist beoordelen of het model onder de Waadi valt vóórdat dit systeem live gaat met echte transacties. Dit is geen technisch punt, maar moet wel vóór livegang geregeld zijn.
2. **Geld gaat nooit automatisch de deur uit.** Bouw dit letterlijk af als een harde technische beperking (geen API-key voor de betaal-integratie beschikbaar voor de Financieel-agent), niet alleen als een "regel" die de AI zou moeten volgen.
3. **AVG/privacy**: persoonsgegevens van medewerkers en bedrijven moeten volgens de AVG verwerkt worden — dataminimalisatie, bewaartermijnen, en een verwerkersovereenkomst met elke externe API-partij (Meta, WhatsApp, betaal-provider).
4. **Log alles.** Elke actie van elke agent moet in `activiteitenlog` terechtkomen — dit is niet optioneel, dit is je audit-trail als er ooit iets misgaat.

---

## 7. Gefaseerd bouwplan

**Fase 1 — MVP (1 agent + dashboard)**
Bouw eerst alleen de Matching-agent met echte data, gekoppeld aan het bestaande directiedashboard. Doel: bewijzen dat automatisch matchen + rapportage werkt voordat je uitbreidt.

**Fase 2 — Support + Financieel**
Voeg de Support-agent (chatbot) en Financieel-agent (urenberekening, factuurconcepten) toe. Uitbetalingen blijven volledig handmatig via het dashboard.

**Fase 3 — Marketing + volledige coördinatie**
Voeg de Marketing-agent toe en bouw de Directie-agent uit tot volledige coördinator met de escalatielogica zoals hierboven beschreven.

**Fase 4 — schaal**
Pas bij meerdere strandtenten en honderden medewerkers: overweeg Redis voor de message queue, en meer geautomatiseerde monitoring/alerting.

---

## 8. Kant-en-klare prompt voor Claude Code

Kopieer onderstaande tekst als startpunt in Claude Code om Fase 1 te laten bouwen:

```
Bouw een FastAPI-backend voor WOSZ, een horecapersoneelsplatform in Zandvoort.

Scope voor deze eerste fase: alleen de Matching-agent.

Vereisten:
- PostgreSQL database met tabellen: users, shifts, matches, levels, activiteitenlog
  (zie datamodel in wosz-ai-systeem-bouwopdracht.md)
- Een FastAPI-endpoint die automatisch shifts matcht aan beschikbare medewerkers
  op basis van functie, beschikbaarheid en levelprioriteit
- Elke matching-actie wordt weggeschreven naar de activiteitenlog-tabel met
  veld "afdeling" = "matching"
- Een endpoint GET /api/directie/activiteiten die de laatste 40 activiteiten
  teruggeeft, zodat de bestaande frontend (wosz-app.html, directie-rol) deze
  kan tonen in plaats van de huidige gesimuleerde data
- Signaleer no-shows: als een medewerker een geaccepteerde shift niet checkt,
  maak een record aan in de activiteitenlog met afdeling "matching" EN een
  tweede record met afdeling "support" (waarschuwing)
- Gebruik de Anthropic API (Claude) voor de daadwerkelijke matching-beslissing
  wanneer de situatie niet triviaal is (bijv. meerdere geschikte kandidaten) —
  geef het model de shift-vereisten en kandidatenlijst, laat het de beste
  match kiezen met onderbouwing die in de activiteitenlog komt

Bouw dit met duidelijke scheiding tussen database-laag, agent-logica en
API-laag, zodat de volgende fases (Support-agent, Financieel-agent) er
gemakkelijk naast gebouwd kunnen worden.
```

---

*Dit document is het startpunt. Voordat er echt geld of echte medewerkersdata doorheen gaat: laat de arbeidsrechtelijke check (punt 6.1) eerst afronden.*
