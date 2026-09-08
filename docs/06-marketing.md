# 6. Marketing

## Het uitgangspunt

Je klant hoeft niet overtuigd te worden dat stoppen goed is. Hij moet overtuigd worden dat
het déze keer anders gaat. Alle marketing gaat daarover, en over niets anders.

Twee getallen bepalen of het werkt:

- **Je mag ongeveer €62 per klant uitgeven** (bij de huidige inkoopaanname en €25 winst per
  order). Zie `docs/05-financieel.md` — dit getal verandert zodra je echte inkoopprijzen hebt.
- **Bij een conversie van 2% op de bestelpagina** betekent dat: een klik mag maximaal
  €1,24 kosten. Dat is haalbaar op Facebook in Nederland, maar niet ruim. Elke procent
  extra conversie is meer waard dan elke euro extra budget.

---

## De trechter

```
Facebook / Instagram advertentie
        ↓  (haak: "je bent niet te zwak, je schema was verkeerd")
Landingspagina of direct de zelftest
        ↓  (vier vragen — dit is het beste stuk van de site)
Uitslag: dit is jouw programma, dit zit erin, dit kost het
        ↓
Bestellen  →  afrekenscherm met tweede blikje en partnerprogramma
        ↓
Bevestigingsmail → welkomstmail → 90 dagelijkse mails
        ↓
Dag 30: Reset aanbieden · Dag 60: partner · Dag 85: review vragen
```

**De zelftest is je belangrijkste pagina.** Niet de landingspagina. Vier vragen beantwoorden
is makkelijk, en aan het eind heeft iemand niet "een product bekeken" maar "zijn eigen
programma gekregen". Stuur advertentieverkeer daarom direct naar `quiz.html`, niet naar de
homepage — en meet het verschil.

---

## Facebook en Instagram

### Vijf invalshoeken

Een invalshoek is een reden waarom iemand klikt. Test invalshoeken tegen elkaar, niet
losse advertenties. Pas als één invalshoek wint, maak je daar vijf varianten van.

**1. Het lag niet aan jou** — de sterkste, begin hiermee.
> Je bent niet drie keer gefaald omdat je te zwak bent.
> Je bent drie keer gefaald omdat je van twintig sigaretten naar nul sprong.
> Dat is geen wilskracht, dat is een verkeerd plan.
> QUITTER is een schema van 90 dagen: 4 mg, dan 2 mg, dan niets.
> → Doe de test, 4 vragen, dan weet je welk schema bij je hoort.

**2. Dag 3** — heel specifiek, en daarom geloofwaardig.
> Dag 1 is niet de zwaarste dag. Dag 3 is dat.
> Bijna iedereen die stopt, gaat om dag drie onderuit — en meestal staat er dan niemand naast je.
> Bij QUITTER staat er iets klaar voor dag 3. Voor alle 90 dagen, eigenlijk.
> → Bekijk het schema.

**3. De rekensom** — voor de nuchtere klikker.
> Een pakje per dag is ruim €300 per maand.
> QUITTER kost €199. Eén keer.
> Negentig dagen kauwgom in aflopende sterkte, een blikje voor in je broekzak,
> en elke ochtend één mail die vertelt wat je die dag doet.
> → Bereken welk programma je nodig hebt.

**4. Het blikje** — beeld doet hier het werk.
> Het past in je broekzak. Precies waar je pakje zat.
> Je pakt het net zo vaak, met dezelfde hand, op dezelfde momenten.
> Alleen zit er geen sigaret in maar een schema.
> → Kijk wat erin zit.

**5. Niemand hoeft het te weten** — voor wie het stiekem wil doen.
> Geen huisarts. Geen wachtlijst. Geen groepsgesprek waar je je naam moet zeggen.
> Een doos op je deurmat en negentig dagen die je zelf regelt.
> → Doe de test.

### Wat je niet mag zeggen

Adverteer op **het programma en het schema**, niet op de kauwgom. Zodra je in een Meta-
advertentie een geneesmiddel aanbiedt, loop je tegen hun eigen beleid aan én tegen de
Nederlandse reclameregels. Zeg "een schema van negentig dagen", niet "koop nicotinekauwgom".

Draai elke advertentietekst door de merktoets voordat je hem inplant:

```bash
uv run quitter check "je advertentietekst hier"
```

En laat wat overblijft toetsen door de Keuringsraad — zie `docs/04-compliance.md`.

### Beeld

- **Het blikje in een broekzak.** Één foto, van dichtbij, in daglicht. Dit is je beste beeld.
- **De afbouwkaart op een keukentafel**, met koffie ernaast. Herkenbaar, niet gestileerd.
- **Zes blisters naast elkaar**, van vol naar bijna leeg. Het schema in één beeld.
- **Geen** longen, asbakken vol peuken, of mensen die hoesten. Dat scrolt weg en het mag niet.
- **Geen** stockfoto's van lachende modellen met een duim omhoog.

Video werkt beter dan foto: vijftien seconden, handen in beeld, het blikje dat opengaat,
de blister die je ziet, tekst in beeld voor wie zonder geluid kijkt.

### Zo begin je, stap voor stap

| Fase | Budget | Wat je doet | Waar je op let |
|---|---|---|---|
| Week 1-2 | €20/dag | Vijf invalshoeken, één beeld per invalshoek, naar de zelftest | Welke invalshoek de goedkoopste klik geeft |
| Week 3-4 | €40/dag | De winnende invalshoek, vijf varianten in tekst | Kosten per voltooide zelftest |
| Week 5-8 | €75/dag | Winnende combinatie opschalen, tweede beeld testen | Kosten per klant, moet onder €62 |
| Daarna | Zoveel als winstgevend blijft | Nieuwe invalshoeken blijven testen | Zodra de kosten per klant boven €62 komen: stoppen met opschalen |

**Zet nooit meer geld in een advertentie dan hij oplevert.** Dat klinkt vanzelfsprekend en
gaat toch bij bijna iedereen mis, omdat het een week duurt voordat je het ziet. Kijk elke
maandag naar kosten per klant, niet naar het aantal kliks.

---

## Wat je meet

Vijf getallen. Meer niet — de rest is afleiding.

| Getal | Waar | Doel |
|---|---|---|
| Kosten per klant (CAC) | Facebook + je orderoverzicht | onder €62, streven naar €40 |
| Conversie zelftest → bestelling | Site | boven 8% |
| Conversie bezoeker → zelftest gestart | Site | boven 25% |
| Gemiddelde orderwaarde | Orderoverzicht | boven €217 |
| Openpercentage dagmail | Mailtool | boven 45% na dertig dagen |

Die laatste is je beste voorspeller. Wie de mail van dag 30 nog opent, maakt het programma
af, laat een goede review achter, koopt de app en vertelt het door. Wie hem niet meer opent,
is teruggevallen. Bel die groep — letterlijk, of stuur een persoonlijke mail. Daar zit je
Reset-omzet én je beste productverbetering.

---

## Wat er nog meer moet gebeuren

### Zoekverkeer (voor over zes maanden)

Advertenties stoppen zodra je stopt met betalen. Zoekverkeer niet. Schrijf artikelen die
antwoord geven op wat je klant intikt:

- "hoe lang duurt afkicken van nicotine"
- "nicotinekauwgom 2 mg of 4 mg"
- "waarom mislukt stoppen met roken"
- "wat gebeurt er in je lichaam als je stopt met roken"
- "stoppen met roken zonder aankomen"
- "afbouwschema nicotinekauwgom"

Elk artikel eindigt bij de zelftest. Laat PEN ze schrijven, laat TOETS ze goedkeuren, en
publiceer er twee per week. Na een half jaar heb je een stroom bezoekers die je niets kost.

### Social zonder advertentiebudget

Eén formaat, elke dag, negentig dagen lang: **"Dag X"**. Het blikje, de blister van die dag,
één zin over wat er die dag gebeurt. Het is het programma zelf als content — mensen gaan
meekijken alsof het een serie is, en het is eindeloos te herhalen met elke nieuwe klant die
zijn eigen dag X post.

### Klanten die klanten opleveren

- **Review vragen op dag 85**, niet eerder. Iemand die het bijna heeft gehaald, schrijft
  het mooiste verhaal.
- **Partnerprogramma**: het tweede programma met korting op het afrekenscherm. Samen stoppen
  werkt beter dan alleen, en het verdubbelt je orderwaarde zonder extra advertentiekosten.
- **Doorverwijzen**: klant krijgt €20 terug als een vriend bestelt, vriend krijgt €20 korting.
  Kost je €40 en dat is nog altijd goedkoper dan Facebook.

### Wat je later moet oppakken

Werkgevers en verzekeraars. Een bedrijf met 200 rokende medewerkers heeft een reden om dit
te kopen, en betaalt per medewerker zonder te onderhandelen over €20. Dat is een heel andere
verkoop — trager, met contracten — maar de ordergrootte is tien keer die van een consument.
Niet nu. Wel opschrijven.
