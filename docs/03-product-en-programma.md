# 3. Het product en het programma

## Wat de klant koopt

Eén doos, één keer betalen, negentig dagen.

| In de doos | Waarom het erin zit |
|---|---|
| **Metalen blikje met schuifhuls** | Neemt de plek van het pakje in, ook in gewicht. Aan de binnenkant van de huls staat het schema. |
| **Zes blisters kauwgom** | Eén blister per blok van vijftien dagen, in volgorde genummerd. Je hoeft nooit te rekenen: je pakt de blister van vandaag. |
| **Afbouwkaart, creditcardformaat** | Het hele schema op zakformaat. Past in je portemonnee. |
| **Welkomstkaart met startcode** | Daarmee zet de klant zijn startdag en begint de dagelijkse mail. |
| **Bijsluiter (SmPC/patiëntenbijsluiter)** | Wettelijk verplicht. Een doos zonder bijsluiter mag niet de deur uit. |

En daarnaast, negentig ochtenden lang: **één mail met wat je die dag doet.**

---

## De drie programma's

De zelftest (vier vragen, `quitter/taper.py`) bepaalt welk programma iemand nodig heeft.
De logica is een verkorte Fagerström-benadering: hoevéél iemand rookt en hoe snel na het
opstaan de eerste sigaret komt, voorspellen samen het beste hoe zwaar de verslaving is.

| | **Licht** | **Standaard** | **Zwaar** |
|---|---|---|---|
| SKU | Q90-L | Q90-S | Q90-Z |
| Prijs | €149 | €199 | €249 |
| Voor wie | tot 10 sigaretten/dag | 10-20 per dag | meer dan 20 per dag, of eerste sigaret binnen 5 minuten |
| Kauwgom | 465× 2 mg | 270× 4 mg + 300× 2 mg | 450× 4 mg + 240× 2 mg |
| Totaal stuks | 465 | 570 | 690 |

> **Twijfel je tussen twee programma's, kies het zwaarste.** Te licht beginnen is de meest
> gemaakte fout bij nicotinevervangers: mensen onderdoseren, voelen te veel trek, en concluderen
> dat het niet werkt. Zet die zin op de site, in de quiz en in de eerste mail.

---

## Het schema

Zes blokken van vijftien dagen. De dosis loopt alleen omlaag — dat wordt in de tests
afgedwongen, zodat een latere aanpassing nooit per ongeluk een stijging kan introduceren.

### Standaard (Q90-S)

| Blok | Dagen | Sterkte | Per dag | Wat er gebeurt |
|---|---|---|---|---|
| 1 | 1-15 | 4 mg | 10× | **Vervangen.** Je stopt met roken op dag 1. Elke sigaret wordt een stuk 4 mg. |
| 2 | 16-30 | 4 mg | 8× | **Stabiel.** De ergste dagen liggen achter je. Twee stuks minder, verder niets. |
| 3 | 31-45 | 2 mg | 8× | **Halve sterkte.** Zelfde aantal, halve dosis. De grootste stap van het programma. |
| 4 | 46-60 | 2 mg | 6× | **Minderen.** Op vaste momenten, niet meer bij elke prikkel. |
| 5 | 61-75 | 2 mg | 4× | **Uitdunnen.** Vier vaste momenten. De rest zit je uit. |
| 6 | 76-90 | 2 mg | 2× | **Naar nul.** Dag 90 gebruik je niets meer. |

De schema's voor licht en zwaar staan in `quitter/taper.py` en zijn op te vragen met
`uv run quitter schema licht` of in de cockpit.

### Waarom het zo loopt

- **Dag 1 is de stopdag, niet dag 14.** Minderen met roken werkt slecht; vervangen werkt beter.
- **Blok 1 en 2 gaan nauwelijks omlaag.** De eerste maand is voor het gedrag, niet voor de dosis.
  Wie in week twee al gaat afbouwen, valt in week drie terug.
- **De sprong zit in blok 3**, van 4 mg naar 2 mg bij hetzelfde aantal stuks. Dat is de dag
  waarop mensen afhaken, dus daar staat de mail van dag 31 op scherp.
- **De laatste dertig dagen zijn het echte werk.** Weinig nicotine, veel trek uitzitten,
  met de wetenschap dat de einddatum vaststaat.

### Veiligheidsgrenzen

Het model bewaakt de gangbare maxima voor nicotinekauwgom: maximaal 15 stuks per dag bij
4 mg en 24 bij 2 mg. Geen schema komt daarbij in de buurt.

> **Te doen:** leg het definitieve schema naast de SmPC van de fabrikant zodra je weet welk
> product je verkoopt. Wijkt de SmPC af — bijvoorbeeld een lager maximum of een voorgeschreven
> minimale gebruiksduur — dan wint de SmPC, altijd. Pas dan `quitter/taper.py` aan; de tests
> vangen het af als er per ongeluk iets omhoog gaat.

---

## De dagelijkse mail

Dit is het halve product. De kauwgom zit in de doos, jij zit in hun inbox.

**Vorm:** onderwerpregel van maximaal 45 tekens, dan wat je vandaag doet, dan één ding
dat helpt. Maximaal 120 woorden. Mensen lezen dit op hun telefoon, staand, met trek.

**De vijf mails die het meeste verschil maken:**

| Dag | Waarom | Wat erin moet |
|---|---|---|
| **1** | De start | Rustig. Wat je nu doet, wat je vandaag mag verwachten, en dat dag 3 zwaarder wordt. |
| **3** | De zwaarste dag | Dit staat er al vóórdat het misgaat. "Vandaag is de zwaarste dag. Morgen wordt het lichter." |
| **10** | Het eerste afhaakmoment | Het nieuwe is eraf, het einde is nog ver. Terugkijken: tien dagen niet gerookt. |
| **31** | De halvering | Van 4 mg naar 2 mg. Uitleggen dat je meer trek gaat voelen en dat dat klopt. |
| **76** | De laatste stap | Nog vijftien dagen. Bijna nul nicotine. Hier verdient iemand zijn negentig dagen. |

**Toon:** je bent geen coach die roept, je bent een schema dat praat.
Niet "je kunt het!" maar "vandaag acht stuks, en drink meer water dan je denkt nodig te hebben".

De mails worden geschreven door de agent COACH, die per dag het dagplan ophaalt zodat de
aantallen altijd kloppen:

```bash
uv run quitter dagmails standaard 1 14
```

---

## Waar het geld nog meer zit

Eén doos per klant is een eenmalige verkoop. Deze vier maken er meer van, zonder dat je
er extra klanten voor nodig hebt:

| | Wat | Prijs | Wanneer aanbieden |
|---|---|---|---|
| **Tweede blikje** | Eén in je jas, één in de auto | €14 | Op het afrekenscherm |
| **Partnerprogramma** | Tweede programma met korting | €129 | Op het afrekenscherm — samen stoppen werkt beter |
| **QUITTER Reset** | Vier weken 2 mg om terug op schema te komen | €59 | Bij terugval, en in de mail van dag 30 en dag 60 |
| **QUITTER Coach+** | De app: inchecken, trekmomenten loggen, hulp op je zwaarste uur | €9/maand | Vanaf dag 7, voor wie de mail elke dag opent |

Het tweede blikje is de makkelijkste: het kost je €2,20 en levert €9,37 op, en de klant
zegt ja omdat hij het argument meteen snapt.

**De app is voor later.** Bouw hem pas als de dozen lopen. Maar bouw de mail nu al zo dat
je weet wie hem elke dag opent — dat zijn precies de mensen die straks €9 per maand betalen.
