# QUITTER — eenpersoons-marketingteam

Eén supervisor-agent die specialisten aanstuurt, met één verschil ten opzichte van elk ander
"AI marketing team": **QUITTER verkoopt een geneesmiddel**, dus er zit een poort tussen het
maken en het publiceren waar niets omheen kan.

```
        jij
         │  "maak een zoekadvertentie voor nicotinekauwgom, NL"
         ▼
┌─────────────────────┐
│  hoofd marketing    │  orchestrator — verdeelt, bewaakt, levert af
└─────────┬───────────┘
          │ roept aan als tools
          ├── research        feiten met bron
          ├── strategist      campagnebrief van één A4
          ├── copywriter      advertenties, koppen, pagina's
          ├── seo_content     artikelen
          ├── social          posts en scripts
          ├── email           de reeks dag 0 → dag 100
          ├── art_director    beeldbriefings en prompts
          └── analyst         wekelijks één beslissing
          │
          ▼
┌─────────────────────┐
│  compliance-poort   │  1. check.mjs   — deterministisch, geen AI
│                     │  2. compliance  — context, toon, impliciete claims
└─────────┬───────────┘
          │  BLOCK → terug naar de maker, met de regel erbij
          ▼
       jij keurt goed  →  Keuringsraad KOAG/KAG  →  publiceren
```

De volgorde is niet onderhandelbaar. Een taalmodel dat zijn eigen tekst beoordeelt, keurt zijn
eigen tekst goed — daarom staat er een domme, deterministische controle vóór de slimme.

## Wat er in deze map zit

| Pad | Wat het is |
| --- | --- |
| `agents/_preamble.md` | Het blok dat aan het begin van élke systeemprompt staat |
| `agents/00-orchestrator.md` … `09-analyst.md` | De teamleden, met hun volledige systeemprompt |
| `compliance/rules.md` | Alle juridische regels, met bron en status |
| `compliance/rules.json` | Dezelfde regels, machineleesbaar |
| `compliance/check.mjs` | De poort. Draait offline, zonder AI, zonder dependencies |
| `compliance/test.mjs` | 12 tests op de poort |
| `brand/voice.md` | De merkstem |
| `workflows/quitter-marketing-team.n8n.json` | Het team als n8n-workflow |
| `playbooks/` | De week, de campagnebrief, de publiceer-checklist |

## Vandaag aan het werk zetten

Zonder n8n, zonder opbouw. Eén commando, en de tekst gaat automatisch door de poort:

```bash
export ANTHROPIC_API_KEY=...        # of: ant auth login
npm run marketing -- copywriter --brief "3 zoekadvertenties, 30 tekens kop" --channel search_ads
npm run marketing -- email --brief "de mail voor dag 3" --lang nl
npm run marketing -- social --brief "LinkedIn over waarom we programma's verkopen" --channel social_organic
```

Wat er gebeurt: de runner bouwt de systeemprompt uit `agents/`, `brand/voice.md` en de volledige
regelset, vraagt het model om het werk, en haalt het antwoord door `check.mjs`. Blokkeert de poort,
dan krijgt de agent de overtreden regels terug en herschrijft hij één keer. Het resultaat komt in
`output/` te staan met het oordeel erboven — niet gepubliceerd, wachtend op jou.

`--dry-run` laat de volledige systeemprompt zien zonder de API aan te roepen. Handig om te zien
wat een agent precies meekrijgt.

In `output/` staat al een complete eerste campagne: wachtlijstpagina, vijf zoekadvertenties, een
LinkedIn-post, vijf artikelen en drie wachtlijstmails. Alle vijf door de poort.

## Zonder API-sleutel

Drie van de vier onderdelen werken vandaag al, zonder sleutel en zonder installatie.

**De poort.** Draait op Node zelf — geen dependencies, geen netwerk, geen kosten.

```bash
node marketing-team/compliance/check.mjs --file concept.md --channel own_site
```

**De agents als plakklare prompt.** `--dry-run` roept de API niet aan; het drukt precies af wat
een agent meekrijgt. Kopieer dat naar Claude.ai, ChatGPT of welke chat je al betaalt, plak je
briefing eronder, en haal het antwoord daarna door de poort.

```bash
npm run marketing -- copywriter --brief "5 varianten voor de wachtlijstkop" --dry-run
```

Werk je vaker met één agent, zet die prompt dan één keer vast als Project-instructie of Custom
GPT. Dan is het voortaan alleen nog je briefing typen.

**De subagents in deze repo.** Werk je in Claude Code, dan staan `quitter-copywriter` en
`quitter-compliance` klaar in `.claude/agents/`. Geen aparte sleutel nodig — ze draaien op de
sessie die je al hebt.

De runner (`npm run marketing`) is het enige dat een sleutel vraagt. Die automatiseert de lus
schrijven → poort → herschrijven; met de hand doe je precies hetzelfde, alleen zelf.

## De poort gebruiken

```bash
# losse tekst
node marketing-team/compliance/check.mjs "90 dagen. Eén beslissing."

# een bestand, als publieksreclame, op een specifiek kanaal
node marketing-team/compliance/check.mjs --file concept.md --channel search_ads --public

# machineleesbaar, voor gebruik in een script of workflow
echo "tekst" | node marketing-team/compliance/check.mjs --json

# na elke wijziging in rules.json
node marketing-team/compliance/test.mjs
```

Exitcode 0 = door, 1 = geblokkeerd. Daarmee kun je het in elke pipeline hangen.

## Het team in n8n zetten

1. Importeer `workflows/quitter-marketing-team.n8n.json` (Workflows → Import from File).
2. Koppel een model-credential aan de node **Model**.
3. Maak per specialist een sub-workflow met een *Execute Workflow Trigger* en een AI Agent
   erin, met de systeemprompt uit `agents/`. Zet de workflow-ID in de bijbehorende
   **Specialist:**-node — daar staat nu `VUL_HIER_DE_WORKFLOW_ID_IN`.
4. De **Compliance-poort** werkt meteen: die draait de regels als code, zonder credential.
5. Test met: *"Schrijf drie zoekadvertenties voor 'nicotinekauwgom kopen', Nederlands."*

De poort krijgt JSON binnen:
```json
{ "text": "<de volledige tekst>", "channel": "search_ads", "isPublicAd": true }
```

## Het team in Claude Code gebruiken

Er staan twee subagents klaar in `.claude/agents/`:

- `quitter-copywriter` — schrijft en draait zichzelf door de poort
- `quitter-compliance` — beoordeelt en blokkeert

## Voordat je hier ook maar iets mee publiceert

Drie dingen moeten eerst kloppen, en geen daarvan kan een AI voor je oplossen:

1. **De verplichte waarschuwingszin.** Staat nu als placeholder in `rules.json`. De poort
   blokkeert daarom alle publieksreclame. Haal de exacte Nederlandse formulering bij de
   Keuringsraad KOAG/KAG, vul hem in, zet de status op `BEVESTIGD`.
2. **De KOAG/KAG-keuring.** Publieksreclame voor zelfzorggeneesmiddelen wordt vooraf getoetst.
   Plan die doorlooptijd in je kalender, niet erna.
3. **De ZERO-constructie.** Een cadeau bij de aankoop van een geneesmiddel raakt de regels rond
   premies. Laat dit toetsen. De poort geeft er nu een waarschuwing op.

Deze map vervangt geen jurist en geen Keuringsraad. Hij zorgt ervoor dat je er niet per ongeluk
langs loopt.
