# 7. De operatie

Je pakt zelf in. Dat is de goedkoopste manier om te beginnen en de beste manier om je
product te leren kennen — de eerste vijftig dozen leren je meer over je bedrijf dan
vijftig gesprekken. Maar het schaalt niet, en je moet van tevoren weten wanneer het klapt.

---

## Van bestelling tot brievenbus

1. **Bestelling komt binnen** — Mollie bevestigt de betaling, jij krijgt een mail.
2. **Bevestigingsmail** gaat automatisch naar de klant: wat hij besteld heeft, wanneer het
   komt, en dat hij zelf zijn startdag kiest.
3. **Inpakken** volgens de inpaklijst van dat programma:
   `uv run quitter inpaklijst Q90-S`, of het tabblad Inpakken in de cockpit.
4. **Partijnummer en houdbaarheidsdatum noteren** bij het ordernummer. Dit is geen
   administratie voor de vorm: bij een terugroepactie moet je binnen een dag kunnen zeggen
   wie welke partij heeft gekregen.
5. **Zegel op de doos.** Zonder zegel geen retourbeleid — de zegel is het bewijs of iets
   geopend is.
6. **Verzendlabel plakken en wegbrengen.** Bestellingen voor 16:00 gaan dezelfde dag mee.
7. **Verzendmail** met track-and-trace.
8. **Startmail** zodra de klant zijn startdag doorgeeft; vanaf dat moment loopt de dagelijkse
   mail negentig dagen door.

### Hoeveel tijd dat kost

Reken op zeven minuten per order: blisters tellen, blikje vullen, kaartjes erbij, doos dicht,
zegel, label, administratie.

| Orders per maand | Uren per maand | Wat dat betekent |
|---|---|---|
| 50 | 6 | Een avond per week. Prima naast je baan. |
| 150 | 18 | Twee avonden per week. Nog te doen. |
| 250 | 30 | Bijna een dag per week. Hier begint het te knellen. |
| 500 | 60 | Anderhalve dag per week. Niet vol te houden naast 40-60 uur werk. |
| 750 | 90 | Meer dan twee dagen per week. Dit moet de deur uit. |

**Het omslagpunt ligt rond 250 orders per maand.** Zorg dat je vóór dat punt een
fulfilmentpartner hebt gesproken — niet erna, want dan sta je 's avonds in te pakken terwijl
je advertenties doorlopen en de levertijd oploopt.

> **Let op bij uitbesteden:** een fulfilmentpartner die geneesmiddelen opslaat en verstuurt,
> moet daarvoor gekwalificeerd zijn. Dit is niet hetzelfde als een gewone e-commerce-3PL.
> Vraag er expliciet naar en laat het in het contract zetten. Zie `docs/04-compliance.md`.

---

## Opslag bij jou thuis

Zolang je zelf inpakt, is je huis je magazijn. Daarvoor gelden eisen:

- **Droog, donker, op kamertemperatuur.** Niet in de schuur, niet op zolder in de zomer.
- **Afgesloten en buiten bereik van kinderen en huisdieren.** Nicotine is voor een kind
  gevaarlijk in kleine hoeveelheden.
- **Op houdbaarheidsdatum sorteren.** Oudste partij eerst de deur uit.
- **Partijnummers bijhouden** per binnengekomen levering en per uitgaande order.
- **Voorraad tellen** wanneer een levering binnenkomt en aan het eind van elke maand.

---

## Inkoop

Kauwgom heeft levertijd, en die levertijd is jouw grootste operationele risico: als je
uitverkocht raakt terwijl je advertenties lopen, betaal je voor klanten die je niet kunt
leveren.

**De regel: bestel bij zes weken voorraad.** Bij 150 orders per maand is dat ongeveer
225 dozen aan materiaal. De cockpit rekent voor hoeveel stuks van elke sterkte je nodig hebt.

Wat je bij elke levering controleert:
- Klopt het aantal stuks per sterkte?
- Staat het partijnummer op de verpakking en heb je het genoteerd?
- Is de houdbaarheid ver genoeg weg? **Vraag minimaal twaalf maanden restlooptijd** —
  bij een programma van drie maanden wil je niet dat de kauwgom halverwege verloopt.
- Zit de bijsluiter erbij, in het Nederlands?

---

## Klantenservice

BALIE (het AI-teamlid) kan het meeste zelf. Wat er langs jou moet:

| Soort vraag | Wie |
|---|---|
| Waar is mijn pakket, welk programma heb ik nodig, hoe gebruik ik de kauwgom | BALIE |
| Retour, ruilen, verkeerd programma besteld | BALIE, jij keurt goed |
| **Gezondheid, zwangerschap, medicijnen, hartklachten, bijwerkingen** | **Nooit AI. Doorverwijzen naar huisarts of apotheek.** |
| Vermoeden van te veel nicotine, kind of huisdier heeft kauwgom binnengekregen | **Direct doorverwijzen. Bij spoed 112.** |
| Boze klant, klacht over het product | Jij |

Die escalatieregel zit in de code (`quitter/compliance.py`) en wordt getest. BALIE mag hem
niet omzeilen, ook niet als de vraag vriendelijk gesteld is.

**Bijwerkingen** meld je door aan de vergunninghouder en de klant wijs je op Lareb.
Leg vast wanneer je wat hebt gemeld.

---

## Retouren

- **Ongeopend, zegel intact, binnen veertien dagen** — geld terug, retourkosten voor de klant.
  Terug de voorraad in, mits de zegel echt ongeschonden is.
- **Geopend** — gaat niet terug. Een geneesmiddel dat het huis van een klant is geweest,
  mag niet terug in de handel. Dit is een wettelijke uitzondering op het herroepingsrecht
  en geen bedrijfsbeleid dat je uit coulance kunt oprekken.
- **Beschadigd of verkeerd geleverd** — nieuwe doos, kosteloos, geen discussie. Dit kost je
  een paar procent en levert je de reviews op waar je later van leeft.
- **Verkeerd programma, doos nog dicht** — omruilen tegen prijsverschil plus verzendkosten.

Zet de retourvoorziening in het rekenmodel op 3% en kijk na honderd orders of dat klopt.

---

## Wat je nog moet regelen

- [ ] **Mollie-account** — iDEAL, Bancontact, creditcard. Vraag aan zodra de bv er is; er
      gaat een controle overheen en dat kost dagen.
- [ ] **Zakelijke bankrekening** op naam van de bv.
- [ ] **PostNL zakelijk account** — scheelt per pakket en geeft je track-and-trace.
- [ ] **Mailtool** die 90 geplande mails per klant aankan, gestart op de dag die de klant
      zelf kiest. Let bij de keuze op: kun je een reeks starten op een variabele datum?
      Niet elke tool kan dat, en zonder die functie werkt het hele product niet.
- [ ] **Boekhouding** die 9% en 21% btw uit elkaar houdt — het programma en de extra's
      vallen mogelijk in verschillende tarieven.
- [ ] **Verzekering**: bedrijfsaansprakelijkheid, en vraag expliciet of verkoop van
      geneesmiddelen gedekt is. Vaak is dat een uitsluiting.
- [ ] **Zegels, dozen, tape met opdruk** — bestel ruim, ze zijn goedkoop en je wilt nooit
      zonder zitten.
