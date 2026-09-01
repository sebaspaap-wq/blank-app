# Meta-advertentie — "Negentig"

<!-- gate:ignore-start -->
**Agents:** strateeg → art direction → copywriter → compliance
**Kanaal:** social_paid · **Taal:** nl · **Publieksreclame:** nee — merkcommunicatie, geen productaanprijzing
**Fase:** pre-launch (geen handelsvergunning)
<!-- gate:ignore-end -->

---

## 1 · Het idee

Eén beeld dat de hele propositie draagt, zonder één woord uitleg: **negentig, met een eind eraan.**

Negentig identieke tegels in een strak raster. De laatste is donker. Dat is het.

Waarom dit werkt in een tijdlijn vol beweging: het is stil. Alles om deze advertentie heen
schreeuwt, beweegt en snijdt. Dit is een rustig, strak uitgelicht raster dat je scroll even
laat haperen omdat het eruitziet als iets dat met opzet gemaakt is. En op het moment dat je
langer dan een halve seconde kijkt, zie je die ene donkere tegel rechtsonder — en snap je dat
het over een eindpunt gaat.

Geen mensen, geen sigaretten, geen product. Dat is geen beperking maar de kracht: iedereen die
dit ziet, projecteert er zijn eigen negentig dagen op.

---

## 2 · Wat er te zien is

**Onderwerp** · 90 vierkante tegels van bleke kalksteen, 9 rijen van 10, met gelijke
voegen. Tegel 90 — rechtsonder — is van gepolijst houtskoolgrijs steen, iets dieper in het
oppervlak gedrukt dan de rest.

**Ondergrond** · Een warm wit, licht korrelig pleisteroppervlak. Geen tafel, geen context, geen
horizon. Het raster ligt in het vlak.

**Licht** · Strijklicht van linksboven, laag in de hoek, alsof de zon net over een muur komt.
Elke tegel werpt een korte, scherpe schaduw naar rechtsonder. Die negentig schaduwen samen maken
het ritme van het beeld. De donkere tegel werpt dezelfde schaduw als de rest — hij is het eind,
geen uitzondering.

**Camera** · Recht van boven, exact loodrecht. Medium format, 100 mm, f/8. Geen perspectief, geen
kanteling. Het raster vult ongeveer vier vijfde van het kader; de rest is lege pleister.

**Kleur** · Uitsluitend warm wit (#F7F6F2), houtskool (#191919) en taupe (#A69B8D) in de
schaduwen. Geen enkele andere kleur in beeld.

**Sfeer** · Architectonisch, stil, duur. Denk aan een museumvloer, niet aan een apotheek.

---

## 3 · De prompt

Plak dit in Higgsfield Soul, of geef het door aan `node marketing-team/image.mjs --prompt "…"`,
dan wordt de merkbeeldtaal er automatisch aan geplakt.

```
Top-down flat lay of exactly ninety small square tiles of pale limestone arranged in a precise
grid of nine rows by ten columns with equal narrow grouting, resting on a warm off-white
lime-plaster surface with fine grain. The final tile in the bottom-right corner is polished
charcoal-grey stone, set very slightly deeper into the surface than the others. Low raking
morning light from the upper left casts short crisp parallel shadows from every tile. Exactly
perpendicular overhead camera, no perspective distortion, grid fills about four fifths
of the frame, generous empty plaster around it. Medium format, 100mm lens, f/8, natural depth of
field, true soft shadows, matte materials, architectural stillness, museum-floor calm, editorial
still life. Colour limited strictly to warm white #F7F6F2, charcoal #191919 and taupe #A69B8D.
```

**Strictly avoid** · `no cigarettes, no ashtrays, no smoke, no lungs, no medical equipment, no lab
coats, no doctors, no people, no hands, no packaging, no product, no pills, no text overlay, no
logos, no children, no before-and-after, no green health symbolism, no gradients, no cartoons, no
tilted camera, no props, no wood grain, no marble veining.`

**Formaten** · Feed 4:5 en Stories/Reels 9:16 vragen een ander raster, niet een uitsnede:

| Plaatsing | Higgsfield-formaat | Aanpassing in de prompt |
| --- | --- | --- |
| Feed 4:5 | `MIXED_1152x1536` (3:4, snijd naar 4:5) | grid of nine rows by ten columns |
| Stories / Reels 9:16 | `PORTRAIT_1152x2048` | grid of **fifteen rows by six columns** |
| Vierkant 1:1 | `SQUARE_1536x1536` | grid of **ten rows by nine columns** |

Genereer per plaatsing opnieuw. Een 9:16-uitsnede uit een liggend raster snijdt tegels doormidden
en dan valt het idee uit elkaar.

---

## 4 · De teksten

**Primaire tekst — variant A (aanbevolen)**

Stoppen met roken duurt maanden. Hulp bij stoppen wordt verkocht per week.

Daar bouwen we iets aan: één plan van negentig dagen, met een datum waarop het klaar is.

QUITTER is in ontwikkeling en nog niet verkrijgbaar. Zet je op de lijst en je hoort het als eerste.

**Primaire tekst — variant B (korter, voor Reels)**

Negentig dagen. Eén plan. Eén datum waarop het klaar is.

QUITTER is in ontwikkeling. Zet je op de lijst.

**Primaire tekst — variant C (de observatie voorop)**

De meeste stoppogingen stranden niet op wilskracht. Ze stranden op voorraad.

Wij bouwen een plan van negentig dagen dat in één keer binnenkomt. Nog niet verkrijgbaar — wel al
te volgen.

**Kop** · Negentig dagen, één plan

**Beschrijving** · QUITTER — in ontwikkeling

**Knop** · Meer informatie → de wachtlijstpagina

**Alt-tekst** · Negentig kalkstenen tegels in een raster van negen bij tien op warm wit pleister,
de laatste tegel rechtsonder is donkergrijs.

---

<!-- gate:ignore-start -->

## 5 · Instellingen in Meta

- **Doelstelling** · Leads of verkeer naar de wachtlijstpagina. Niet conversies: er is nog niets
  te kopen.
- **Leeftijd** · 18+. Verplicht, en het staat los van wat je verder instelt.
- **Targeting** · Geen interesse- of gedragstargeting op roken, gezondheid of stoppen. Dat is een
  bijzondere categorie persoonsgegevens, en Meta beperkt die targeting bovendien zelf. Werk op
  brede targeting en laat het algoritme het doen.
- **Geen klantlijsten, geen lookalikes.** Zie regel C1: wie dit koopt of hierop klikt, zegt iets
  over zijn gezondheid.
- **Plaatsingen** · Feed, Reels, Stories. Geen Audience Network.
- **Frequentiecap** · Laag houden. Dit beeld werkt door rust; drie keer per week is genoeg.

---

## 6 · De twee regels die deze advertentie hebben gevormd

**Geen handelsvergunning, dus geen productadvertentie.** Reclame voor een geneesmiddel zonder
handelsvergunning is verboden — en Meta staat advertenties voor nicotinevervangers alleen toe
voor goedgekeurde producten. Twee onafhankelijke redenen waarom deze advertentie over het merk
gaat en niet over het middel. Daarom geen verpakking in beeld, geen sterkte, geen prijs, geen
"bestellen".

**Meta's regel over persoonlijke kenmerken.** Advertenties mogen niet impliceren dat je iets weet
over iemands gezondheid. "Rook jij nog?", "Stop jij ook?", "Jouw stoppoging" — allemaal
afgekeurd, want de tweede persoon in combinatie met een gezondheidskenmerk suggereert dat Meta
weet dat de kijker rookt. Elke zin hierboven is daarom in de derde persoon of algemeen
geformuleerd: *stoppen duurt maanden*, niet *jouw stoppoging duurt maanden*.

Dat is geen omweg. Het maakt de advertentie beter: hij gaat over een verschijnsel in plaats van
over een verwijt.

---

## 7 · Wat er bewust niet in zit

- Geen mens, geen gezicht, geen handen. Zodra er iemand in beeld staat, wordt het een verhaal
  over die persoon in plaats van over de kijker.
- Geen cijfer over succeskansen, geen "bewezen", geen vergelijking.
- Geen urgentie, geen aftellers, geen "op=op".
- Geen sigaret, geen rook, geen asbak. Ook niet doorgestreept: het beeld ervan blijft hangen.
- Geen groen, geen longen, geen dokters.

---

## 8 · De versie voor ná de handelsvergunning

Zelfde beeld, één wijziging: **de donkere tegel rechtsonder wordt de QUITTER-verpakking**, in
hetzelfde vlak, met dezelfde schaduw. Negentig dagen, en aan het eind staat het product.

Die versie mag pas als het RVG-nummer er is, en gaat dan eerst langs de Keuringsraad KOAG/KAG.
De tekst krijgt er dan de verplichte vermeldingen bij: werkzame stof, de aansporing om de
bijsluiter te lezen, de waarschuwingszin en 18+.

<!-- gate:ignore-end -->
