# Juridische regels voor QUITTER-marketing

QUITTER is nicotinevervangende therapie: **een geneesmiddel**. Reclame daarvoor is in
Nederland gebonden aan de Geneesmiddelenwet, het Reclamebesluit Geneesmiddelen en de Code
voor de Publieksreclame voor Geneesmiddelen (CPG), met voorafgaande keuring door de
Keuringsraad KOAG/KAG en toezicht door de IGJ.

Dit bestand is de bron voor het hele marketingteam. `rules.json` is de machineleesbare
versie; `check.mjs` handhaaft wat automatisch te handhaven is. Elke agent krijgt deze regels
mee, en geen enkele uiting gaat naar buiten zonder de poort.

## Statuslegenda

| Status | Betekenis |
| --- | --- |
| `BEVESTIGD` | Geverifieerd bij een officiële bron; bron staat erbij. |
| `TE BEVESTIGEN` | Klopt naar alle waarschijnlijkheid, maar niet in deze vorm geverifieerd. Laat toetsen door de Keuringsraad of een advocaat gezondheidsrecht vóór publicatie. |

---

## A. De harde verboden — hier komt niets langs

### A1 · Geen claim buiten de goedgekeurde productinformatie · `BEVESTIGD`
Alles wat je over werking, indicatie, dosering of veiligheid zegt, moet herleidbaar zijn tot
de goedgekeurde SmPC en bijsluiter. Niet "helpt je stoppen" als de goedgekeurde tekst dat zo
niet zegt. Marketing mag herformuleren in gewone taal, maar niet uitbreiden.
> Bron: Geneesmiddelenwet; toezicht IGJ — https://www.igj.nl/zorgsectoren/geneesmiddelen/geneesmiddelenreclame

### A2 · Geen misleiding, geen overdrijving · `BEVESTIGD`
Geen superlatieven ("de beste", "nummer 1"), geen absolute beloftes ("gegarandeerd stoppen",
"100%"), geen suggestie dat het middel op zichzelf tot stoppen leidt.

### A3 · Geen verzonnen bewijs · `BEVESTIGD`
Geen percentages, slagingskansen, onderzoeken of "klinisch bewezen" zonder dossier dat het
draagt. Eén verzonnen cijfer in één advertentie is genoeg voor een handhavingszaak.

### A4 · Geen vergelijkende reclame met andere merken · `TE BEVESTIGEN`
Geen "beter dan Nicorette", ook niet impliciet ("eindelijk een merk dat wél…").

### A5 · Geen aanbeveling door artsen, apothekers of bekende personen · `TE BEVESTIGEN`
Publieksreclame voor geneesmiddelen mag niet aanbevolen worden door beroepsbeoefenaren of
personen die door hun bekendheid het gebruik kunnen aanmoedigen. Dit raakt direct
influencer-marketing en "aanbevolen door dokters"-formuleringen.

### A6 · Geen veiligheidsclaims · `BEVESTIGD`
Niet "veilig", niet "zonder bijwerkingen", niet "geschikt voor iedereen". Een geneesmiddel
heeft contra-indicaties en bijwerkingen; die staan in de bijsluiter.

### A7 · Niet richten op minderjarigen · `BEVESTIGD`
Geen beeld, taal, kanaal of tone-of-voice gericht op jongeren. Het product is voor 18+.

### A8 · Geen cadeaus of premies om aankoop te bevorderen · `TE BEVESTIGEN`
Dit raakt **QUITTER ZERO** rechtstreeks: een gratis product dat je krijgt als je een
geneesmiddel koopt en opmaakt, is precies de constructie die de CPG beperkt. Laat de
ZERO-constructie toetsen vóór lancering. Alternatieven staan in het bedrijfsplan, hoofdstuk 05.

### A9 · Geen onbetrouwbare urgentie of dark patterns · `BEVESTIGD` (eigen norm)
Geen "op=op", geen afteltimers, geen vooraf aangevinkte abonnementen. Dit is deels wet en
deels merkbelofte — voor QUITTER geldt het als hard verbod.

---

## B. Wat verplicht wél in de uiting moet

### B1 · De verplichte waarschuwingszin · `TE BEVESTIGEN — LETTERLIJK OVERNEMEN`
Elke publieksreclame voor een geneesmiddel bevat verplichte vermeldingen, waaronder de
aansporing de bijsluiter te lezen.

> **Belangrijk:** de exact voorgeschreven Nederlandse formulering is in dit project nog
> **niet** bij een officiële bron geverifieerd. De zin die je online vaak tegenkomt
> ("dit is een geneesmiddel, geen langdurig gebruik zonder medisch advies") is de **Belgische**
> verplichte zin en mag niet zonder controle voor Nederland worden overgenomen.
>
> Haal de exacte Nederlandse zin bij de Keuringsraad KOAG/KAG en zet hem één keer in
> `rules.json` onder `mandatoryNotice`. **Laat geen enkel AI-model deze zin zelf formuleren** —
> de agent controleert alleen of de vastgelegde string letterlijk aanwezig is.

### B2 · Naam van het werkzame bestanddeel · `TE BEVESTIGEN`
Nicotine, in combinatie met de merknaam en de sterkte.

### B3 · Aansporing de bijsluiter te lezen · `BEVESTIGD`

### B4 · KOAG/KAG-toelatingsnummer · `BEVESTIGD`
Publieksreclame voor zelfzorggeneesmiddelen wordt vooraf getoetst door de Keuringsraad; veel
media nemen een uiting zonder toelatingsnummer niet af.
> Bron: https://keuringsraad.nl/regels-wetgeving/geneesmiddelen/

### B5 · EU-logo voor online verkoop · `BEVESTIGD`
Wie online geneesmiddelen verkoopt vanuit Nederland moet zich registreren als online
aanbieder en het verplichte EU-logo tonen, met link naar het register.
> Bron: https://ondernemersplein.overheid.nl/wetten-en-regels/zelfzorggeneesmiddelen-verkopen/

### B6 · 18+ · `BEVESTIGD`

---

## C. Privacy: gezondheidsgegevens

### C1 · Kopen van een stoppen-met-rokenmiddel is een gezondheidsgegeven · `BEVESTIGD`
Dat maakt klantdata een bijzondere categorie persoonsgegevens onder de AVG. Gevolgen voor
marketing:
- **Geen** klantlijsten uploaden naar advertentieplatforms voor targeting of lookalikes.
- **Geen** retargeting op productpagina's zonder expliciete, aparte toestemming.
- **Geen** e-mailsegmentatie die iemands rookgedrag afleidbaar maakt naar derden.
- Analytics pas na toestemming — zo is de site al gebouwd.

---

## D. Kanaalregels

| Kanaal | Wat mag | Let op |
| --- | --- | --- |
| Eigen site & e-mail | Productinformatie, prijs, programma-uitleg | Waarschuwingszin, EU-logo, geen claims buiten dossier |
| Zoekadvertenties | Merk- en categorietermen | Vooraf keuren; platformbeleid rond gezondheid |
| Social organisch | Merkverhaal, proces, ontwerp | Zodra het product genoemd wordt, is het geneesmiddelenreclame |
| Social betaald | Beperkt | Platformbeleid + KOAG-keuring |
| Influencers / affiliates | **Vermijden** | Raakt A5; bovendien reclamecode voor influencers |
| PR & pers | Feitelijke informatie | Journalistiek is geen reclame, maar een gesponsord artikel wel |
| Werkgevers / B2B | Zakelijke propositie | Richting eindgebruiker gelden alsnog alle publieksregels |

---

## E. De werkwijze die dit afdwingt

1. Elke uiting wordt geschreven door een agent die deze regels in zijn systeemprompt heeft.
2. Elke uiting gaat daarna verplicht door `check.mjs` (deterministisch) en door de
   compliance-agent (context en toon).
3. Bij `BLOCK` gaat het terug naar de schrijver met de regel erbij. Nooit "toch maar plaatsen".
4. Wat door de poort komt, gaat naar **jou**. Een mens keurt goed, altijd.
5. Alles wat publieksreclame is, gaat vóór publicatie naar de Keuringsraad.

> Geen enkele stap in deze keten mag door een AI-agent worden overgeslagen, ook niet als de
> agent overtuigd is dat het wel goed zit.
