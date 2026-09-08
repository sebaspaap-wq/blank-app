# Facebook en Instagram — vijf invalshoeken om mee te beginnen

Test **invalshoeken** tegen elkaar, niet losse advertenties. Eén beeld per invalshoek,
€20 per dag, twee weken. Pas als er één wint, maak je daar vijf tekstvarianten van.

Alles hieronder is door de merktoets (`uv run quitter check`) en bevat geen verboden claim.
**Voordat je publiceert:** laat de definitieve set toetsen door de Keuringsraad — zie
`docs/04-compliance.md`.

Bestemming van alle advertenties: **`quiz.html`**, niet de homepage. Vier vragen beantwoorden
is een lagere drempel dan een product bekijken, en aan het eind heeft iemand zijn eigen
programma in handen.

---

## Invalshoek 1 — "Het lag niet aan jou"

*De sterkste. Begin hiermee.*

**A**
> Je bent niet drie keer gefaald omdat je te zwak bent.
> Je bent drie keer gefaald omdat je van twintig sigaretten naar nul sprong.
>
> Dat is geen wilskracht. Dat is een verkeerd plan.
>
> QUITTER is een schema van 90 dagen. Je bouwt af van 4 mg naar 2 mg naar nul, en elke
> ochtend krijg je één mail die vertelt wat je die dag doet.
>
> Vier vragen en je weet welk schema bij je hoort. →

**B**
> "Deze keer lukt het wel." Dat zei je vorige keer ook.
>
> Niet omdat je het niet meende. Omdat je een datum had en geen schema.
>
> 90 dagen. Zes stappen omlaag. Elke dag staat van tevoren vast. →

**C**
> Wilskracht is geen plan.
>
> QUITTER: 90 dagen nicotinekauwgom in aflopende sterkte, in een blikje dat in je broekzak
> past. Plus elke ochtend één mail met wat je die dag doet. →

**Beeld:** het blikje in een broekzak, van dichtbij, daglicht.

---

## Invalshoek 2 — "Dag 3"

*Heel specifiek, en daarom geloofwaardig.*

**A**
> Dag 1 is niet de zwaarste dag. Dag 3 is dat.
>
> Bijna iedereen die stopt, gaat rond dag drie onderuit. En meestal staat er dan niemand
> naast je.
>
> Bij QUITTER staat er iets klaar voor dag 3. Voor alle 90 dagen, eigenlijk. →

**B**
> Weet je nog waar je vorige keer strandde?
> Grote kans dat het dag twee of drie was.
>
> Daarom begint ons schema niet met minderen maar met vervangen: tien stuks van 4 mg per
> dag, precies op de momenten waarop je normaal rookte. →

**Beeld:** de afbouwkaart op een keukentafel, koffie ernaast. Dag 3 aangekruist.

---

## Invalshoek 3 — De rekensom

*Voor de nuchtere klikker.*

**A**
> Een pakje per dag is ruim €300 per maand.
> QUITTER kost €199. Eén keer.
>
> Negentig dagen kauwgom in aflopende sterkte, een blikje voor in je broekzak,
> en elke ochtend één mail die vertelt wat je die dag doet. →

**B**
> 570 stuks kauwgom. Zes blisters. Negentig dagen.
> Van 4 mg naar 2 mg naar nul.
>
> Reken zelf uit wat je nu per maand aan roken uitgeeft. →

**Beeld:** zes blisters naast elkaar, van vol naar bijna leeg.
*(Controleer de actuele pakjesprijs voordat je hem noemt.)*

---

## Invalshoek 4 — Het blikje

*Beeld doet hier het werk. Kortste tekst wint.*

**A**
> Het past in je broekzak. Precies waar je pakje zat.
>
> Je pakt het net zo vaak, met dezelfde hand, op dezelfde momenten.
> Alleen zit er geen sigaret in maar een schema. →

**B**
> 90 dagen in een blikje. →

**Beeld:** vijftien seconden video. Handen in beeld, blikje gaat open, blister eruit,
tekst in beeld voor wie zonder geluid kijkt.

---

## Invalshoek 5 — "Niemand hoeft het te weten"

*Voor wie het stiekem wil doen. Onderschat deze groep niet.*

**A**
> Geen huisarts. Geen wachtlijst. Geen groepsgesprek waar je je naam moet zeggen.
>
> Een doos op je deurmat en negentig dagen die je zelf regelt. →

**B**
> Je hoeft het aan niemand te vertellen tot het gelukt is. →

**Beeld:** een neutrale doos op een deurmat.

---

## Wat je niet schrijft

- Niets over "koop nicotinekauwgom" — adverteer op het programma en het schema.
- Geen percentages over slaagkans zonder bron én goedkeuring.
- Geen "gegarandeerd", "zonder trek", "volkomen veilig", "artsen raden aan".
- Geen longfoto's, asbakken of hoestende mensen.
- Geen gratis proefpakketten of winacties — dat mag niet bij een geneesmiddel.

*(De merktoets slaat aan op de opsomming hierboven: die staat er als voorbeeld van wat níét mag. Dat is de bedoeling — de toets kijkt naar woorden, niet naar context. De advertentieteksten zelf zijn schoon.)*

Draai elke tekst door de merktoets voordat je hem inplant:

```bash
uv run quitter check "je tekst hier"
```
