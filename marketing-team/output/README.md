# Output — de eerste campagne

Vijf teksten, gemaakt met dit team en door de poort gehaald. Ze zijn **niet gepubliceerd**:
lees ze, beslis zelf, en pas ze aan waar je het beter weet.

| Bestand | Kanaal | Poort |
| --- | --- | --- |
| `01-wachtlijst-pagina.md` | own_site | PASS |
| `02-zoekadvertenties.md` | search_ads | PASS |
| `03-linkedin-post.md` | social_organic | PASS |
| `04-artikel-outline.md` | own_site | PASS |
| `05-email-wachtlijst.md` | email | PASS |

Zelf opnieuw controleren:

```bash
node marketing-team/compliance/check.mjs --file marketing-team/output/01-wachtlijst-pagina.md --channel own_site
```

## Waarom dit een wachtlijstcampagne is en geen productcampagne

Reclame maken voor een geneesmiddel zonder handelsvergunning is verboden. QUITTER heeft die
vergunning nog niet, dus mag er in deze fase **niets** worden aangeprezen: geen sterktes, geen
prijs, geen bestelknop, geen belofte over werking. Het merk, het idee en het probleem mogen wel.

Dat is precies wat het bedrijfsplan als eerste stap voorschrijft — vraag bewijzen vóór je
registreert — en het is toevallig ook het enige wat nu juridisch kan. Deze vijf teksten doen
samen één ding: meten wat een aanmelding kost.

Zodra de handelsvergunning er is, zet je in `compliance/rules.json` het veld
`product.marketingAuthorisation` op `"granted"`. Dan vervalt deze blokkade, en gelden vanaf dat
moment de verplichte vermeldingen en de voorafgaande keuring voor alles wat je publiceert.

## Wat de poort onderweg tegenhield

- Twee bestanden werden eerst geblokkeerd omdat de controle ook mijn eigen briefings las. Sindsdien
  slaat de poort HTML-commentaar over en alles tussen `<!-- gate:ignore-start -->` en
  `<!-- gate:ignore-end -->`.
- Het woord "koop" in gewone zinnen ("nog niet te koop") gaf vals alarm. De patronen kijken nu
  naar een échte oproep tot aankoop: "bestel nu", een knop op een eigen regel, een prijs.
- In twee teksten stond "de beste route" over de vergoede zorg. Terecht een waarschuwing —
  herschreven naar "de aangewezen route".
