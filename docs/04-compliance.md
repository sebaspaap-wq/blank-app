# 4. Regels: wat mag en wat niet

> **Dit is geen juridisch advies.** Het is een werkinstrument dat je vertelt waar de
> blokkades zitten en welke vragen je aan wie moet stellen. Laat het toetsen door iemand
> die gespecialiseerd is in geneesmiddelenrecht voordat je live gaat. Bij een geneesmiddel
> is dat geen luxe: hier zijn boetes en een verkoopverbod het risico, niet een boze klant.

De regels zitten ook als code in `quitter/compliance.py`. Elke AI-agent moet erlangs
voordat er iets naar buiten gaat, en de tests falen als een verboden claim erdoorheen glipt.

---

## Het ene feit waar alles om draait

**Nicotinekauwgom is in Nederland een geneesmiddel.** Niet een supplement, niet een
levensmiddel, niet een tabaksproduct. Dat betekent:

1. Er moet een **handelsvergunning** op het product zitten (CBG-MEB of Europees via EMA).
2. Wie het verkoopt, moet dat via het juiste kanaal doen — dat hangt af van de
   **afleverstatus** van dat specifieke product.
3. **Reclame** ervoor is aan strenge regels gebonden en wordt in Nederland vooraf getoetst.
4. Wie het **online** aanbiedt, moet zich melden en een verplicht Europees logo voeren.

Er is geen weg omheen. Er is alleen een weg erdoorheen.

---

## Vier dingen die geregeld moeten zijn

### 1. De handelsvergunning — jouw grootste blokkade

Je wilt onder eigen merk verkopen. Voor een geneesmiddel kan dat op een paar manieren:

| Route | Wat het inhoudt | Tempo |
|---|---|---|
| **Eigen handelsvergunning** | Je dient zelf een dossier in bij het CBG. Duur en traag. | Maanden tot jaren |
| **Duplicaat / informed consent** | De fabrikant geeft toestemming om zijn dossier te gebruiken; het product komt onder jouw naam in het register. | Maanden |
| **Private label onder hun vergunning** | De fabrikant blijft vergunninghouder, jij bent distributeur onder een eigen handelsnaam. | Weken tot maanden |
| **Gewoon inkopen en doorverkopen** | Je verkoopt hun merk in jouw doos. Snelst, maar het is dan niet jouw merk op de kauwgom. | Direct, mits kanaal klopt |

**Dit is precies de vraag die je aan MAE Pharma moet stellen.** De volledige vragenlijst
staat in `docs/08-mae-pharma.md`. Zonder een helder antwoord hierop weet je niet of je
over drie weken of over een jaar kunt verkopen — en dat bepaalt alles.

### 2. Waar je het mag verkopen (kanalisatie)

Elk geneesmiddel heeft een afleverstatus. Voor zelfzorgmiddelen zijn de relevante:

- **AV** — algemene verkoop. Mag in elke winkel en webshop.
- **UAD** — uitsluitend apotheek en drogist. Vereist een gediplomeerd drogist of
  apotheker die toezicht houdt en advies kan geven, ook bij online verkoop.
- **UA / UR** — alleen apotheek, of alleen op recept. Niet van toepassing hier.

> **Zoek op:** de afleverstatus van precies het product dat je gaat verkopen, in de
> geneesmiddeleninformatiebank van het CBG. Is het UAD, dan heb je een gediplomeerde
> drogist nodig — in dienst, of ingehuurd. Dat is een reële kostenpost en een reële
> vertraging, en je wilt er niet achter komen nadat je voorraad hebt ingekocht.

### 3. Online verkoop melden

Wie geneesmiddelen online aanbiedt aan het publiek in Nederland, moet dat melden en wordt
opgenomen in een openbaar register. De website moet het **gemeenschappelijke Europese logo**
voeren, met een link naar de vermelding in dat register. Zonder logo ben je herkenbaar illegaal.

> **Te doen:** meld de webshop bij de IGJ zodra de bv bestaat en het domein op jouw naam
> staat. Zet daarna het logo in de voettekst van elke pagina van `site/`.

### 4. Reclame — vooraf laten toetsen

Publieksreclame voor zelfzorggeneesmiddelen mag in Nederland, maar wordt vooraf getoetst
door de **Keuringsraad (KOAG/KAG)**. Reken op doorlooptijd en op aanpassingsrondes.

**Wat sowieso niet mag** (dit zit ook in `quitter/compliance.py` als blokkerende regels):

| Code | Wat | Waarom |
|---|---|---|
| C01 | "Gegarandeerd rookvrij", "100% succes" | Absolute werkingsclaim |
| C02 | Ziektebeelden noemen (kanker, hart- en vaatziekten) | Claims over ernstige ziekten in publieksreclame |
| C03 | "Geen bijwerkingen", "volkomen veilig" | Absolute veiligheidsclaim |
| C04 | "Artsen raden het aan" | Aanbeveling door beroepsbeoefenaren |
| C05 | Gratis monsters, weggeefacties, prijsvragen | Niet toegestaan bij geneesmiddelen |
| C06 | Richten op of afbeelden van minderjarigen | Verboden |
| C07 | Nicotine als afslankmiddel | Verboden en schadelijk |

**Wat er verplicht bij moet** zodra de kauwgom in beeld is:
- "Lees voor gebruik de bijsluiter."
- De naam van het geneesmiddel en waar het voor is.
- Bij ons ook: "Uitsluitend voor personen van 18 jaar en ouder."

**En let op Meta zelf.** Los van de Nederlandse wet heeft Facebook eigen regels voor
advertenties met medicijnen. Adverteer daarom op **het programma en het schema**, niet op
de kauwgom: "een schema van negentig dagen dat je van roken af helpt" komt door waar
"koop nicotinekauwgom" strandt.

---

## Twee routes naar omzet

Omdat route B op papieren wacht, is er een route A die vandaag al kan.

### Route A — het programma zonder kauwgom (kan nu)

Verkoop het blikje, de afbouwkaart, de dagelijkse begeleiding en het schema. De klant koopt
de kauwgom zelf bij de drogist; jij zegt precies welke sterkte en hoeveel doosjes.

- **Prijs:** €69-89.
- **Juridisch:** je verkoopt geen geneesmiddel, dus geen vergunning en geen kanalisatie.
  Wel blijf je weg van medische claims — de reclameregels voor geneesmiddelen gelden
  strikt genomen niet, maar misleidende claims zijn nog steeds verboden (ACM).
- **Waarom het slim is:** je test vandaag of mensen hiervoor betalen, je bouwt je klantenlijst
  op, en je leert welke advertentie werkt — allemaal terwijl je op MAE Pharma wacht.
- **Waarom het niet genoeg is:** lagere marge, minder waarde, en je verliest het beste stuk
  van het idee — dat alles in één doos zit.

### Route B — het echte product (waar je naartoe werkt)

Kauwgom in de doos, €149/€199/€249. Dit is het bedrijf. Route A is de aanloop.

**Ga niet ondertussen kauwgom verkopen zonder dat de papieren rond zijn.** Dat is precies
het soort besluit waar een bedrijf aan doodgaat: de IGJ kan de verkoop stilleggen, en één
handhavingsdossier volgt je jaren.

---

## Nog vier dingen die je moet regelen

**Bijwerkingen melden.** Je moet meldingen kunnen ontvangen en doorgeven. Dat staat al op
`site/contact.html`, met een verwijzing naar Lareb. Spreek met de vergunninghouder af hoe
jij meldingen aan hen doorgeeft — dat hoort in het contract.

**Bewaren en vervoeren.** Geneesmiddelen hebben eisen aan opslag: temperatuur, droog,
afgesloten, met houdbaarheidsdata en partijnummers die je kunt terugvinden. Pak je thuis
in, dan is je huis je magazijn en gelden die eisen daar. Leg partijnummers per order vast —
zonder dat kun je bij een terugroepactie niet vertellen wie wat heeft gekregen.

**Leeftijd.** Wij leveren 18+. Dat is bedrijfsbeleid, niet per se een wettelijke eis, maar
het is het enige verdedigbare beleid en het houdt Meta rustig.

**Privacy.** Dat iemand stopt met roken zegt iets over zijn gezondheid. Behandel de gegevens
strenger dan een gewone webshop dat zou doen: geen doorverkoop, geen koppeling aan
advertentieprofielen bij derden, en een korte bewaartermijn voor de mailbegeleiding.
Zie `site/privacy.html`.

---

## Checklist voor de lancering

- [ ] Duidelijk welke route (eigen vergunning, duplicaat, private label, doorverkoop)
- [ ] Afleverstatus van het product bekend — en zo nodig een gediplomeerd drogist geregeld
- [ ] Contract met de vergunninghouder, inclusief afspraken over bijwerkingen
- [ ] Webshop gemeld bij de IGJ, EU-logo op elke pagina
- [ ] Advertenties en landingspagina's voorgelegd aan de Keuringsraad
- [ ] Bijsluiter in elke doos, partijnummer en houdbaarheid vastgelegd per order
- [ ] Voorwaarden, privacyverklaring en retourbeleid nagekeken door een jurist
- [ ] Retourbeleid klopt: geopend geneesmiddel gaat niet terug (uitzondering herroepingsrecht)
- [ ] `quitter/compliance.py` bijgewerkt met wat er uit de toetsing komt
