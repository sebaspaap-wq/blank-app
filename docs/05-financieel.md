# 5. Het geld

Alle getallen hieronder komen uit `quitter/finance.py` en `quitter/catalog.py`. Ze zijn
geen illustratie: pas een aanname aan en dit document klopt niet meer, maar de cockpit wel.
Draai `uv run quitter marge` voor de actuele versie.

> **Elke aanname is gemarkeerd.** De inkoopprijzen zijn schattingen tot MAE Pharma met
> echte cijfers komt. Vervang ze in `quitter/catalog.py` en alles rekent opnieuw.

---

## Wat een order oplevert

```
PROGRAMMA'S
--------------------------------------------------------------------------------------------------------
Q90-L    QUITTER 90 Licht         €149.00  kostprijs € 79.28  marge € 57.42 (42.0%)  max CAC € 32.42
Q90-S    QUITTER 90 Standaard     €199.00  kostprijs €100.83  marge € 81.74 (44.8%)  max CAC € 56.74
Q90-Z    QUITTER 90 Zwaar         €249.00  kostprijs €122.69  marge €105.75 (46.3%)  max CAC € 80.75

EXTRA'S
--------------------------------------------------------------------------------------------------------
X-TIN2     Tweede blikje                      € 14.00  marge €  9.37  (bump)
X-PARTNER  Partnerkorting: tweede programma   €129.00  marge € 11.61  (bump)
X-RESET    QUITTER Reset                      € 59.00  marge € 20.76  (upsell)
X-COACH    QUITTER Coach+                     €  9.00  marge €  6.84  (abonnement)
```

**De gemiddelde order** (25% licht, 50% standaard, 25% zwaar, plus de extra's die een deel
van de klanten meeneemt):

| | |
|---|---|
| Orderwaarde inclusief btw | **€217.06** |
| Marge na alle kosten behalve advertenties | **€86.65** |
| Wat een klant maximaal mag kosten (bij €25 winst per order) | **€61.65** |

---

## Waar het geld heen gaat

Bij het standaardprogramma van €199:

| Post | Bedrag | Opmerking |
|---|---|---|
| Kauwgom (270× 4 mg + 300× 2 mg) | €85.20 | AANNAME €0,16 / €0,14 per stuk — **de post die alles bepaalt** |
| Metalen blikje | €2.20 | AANNAME, vanaf 1.000 stuks |
| Verzenddoos en vulling | €0.90 | |
| Drukwerk (afbouwkaart, welkomstkaart, bijsluiter) | €1.10 | |
| Verzending | €4.95 | PostNL pakket NL |
| Betaalkosten | €5.27 | Mollie: vast bedrag plus percentage |
| Retour- en verliesvoorziening | ± €0.27 | 3% ongeopend retour, 1% verlies |
| **Totale kostprijs** | **€100.83** | |
| Omzet exclusief btw (9%) | €182.57 | Geregistreerd geneesmiddel valt onder het lage tarief — **verifiëren** zodra de vergunning rond is |
| **Marge** | **€81.74** | 45% |

Meer dan tachtig procent van je kostprijs is kauwgom. Al het andere — het blikje, het
drukwerk, de verzending — is samen minder dan een kwart van wat de kauwgom kost. Daarom
gaat elke onderhandeling over die ene prijs per stuk.

---

## Het rekenmodel

```
GEMIDDELDE ORDER
  Orderwaarde incl. btw   €  217.06
  Marge na alle kosten    €   86.65   (voor advertenties)
  Plafond advertentiebod  €   61.65   (bij €25 winst per order)

SCENARIO'S PER MAAND
  scenario                                     orders      omzet       ads      winst   uren
  Voorzichtig — 30 orders/maand, dure klanten      30      6,512     1,800        579      4
  Realistisch — 100 orders/maand                  100     21,706     4,500      3,945     12
  Het werkt — 300 orders/maand                    300     65,118    12,000     13,774     36
  Vervang je baan — 750 orders/maand              750    162,795    28,500     36,264     90

ALS DE INKOOPPRIJS VAN KAUWGOM VERANDERT (per stuk 4 mg)
    inkoop  marge/order   marge %   max CAC   break-even orders
  €   0.22        54.35     27.3%     29.35                  51
  €   0.18        75.88     38.1%     50.88                   9
  €   0.16        86.65     43.5%     61.65                   6
  €   0.12       108.18     54.3%     83.18                   4
  €   0.09       124.31     62.4%     99.31                   3
  €   0.06       140.48     70.5%    115.48                   2
```

### Hoe je die laatste tabel leest

Bij **€0,22 per stuk** houd je €54 per order over. Trek daar €50 advertentiekosten van af
en je verdient €4 per bestelling: dan werk je gratis en betaal je Facebook.

Bij **€0,09 per stuk** houd je €124 over. Datzelfde advertentiebudget levert dan €74 per
bestelling op — bijna twintig keer zoveel winst bij exact dezelfde verkoop.

**Dat is het verschil tussen een hobby en een bedrijf, en het wordt beslist in één gesprek
met je leverancier.** Ga dat gesprek in met een concreet volume, een concrete prijs en de
bereidheid om weg te lopen.

---

## Twaalf maanden vooruit

Uitgangspunt: je begint met 40 orders in maand 1, groeit 20% per maand, en een klant kost
€45 aan advertenties. Inkoopprijs op de huidige aanname van €0,16.

| Maand | Orders | Omzet | Advertenties | Winst | Cumulatief |
|---|---|---|---|---|---|
| 1 | 40 | €8,682 | €1,800 | €1,446 | €1,446 |
| 2 | 48 | €10,419 | €2,160 | €1,779 | €3,225 |
| 3 | 58 | €12,589 | €2,610 | €2,195 | €5,420 |
| 4 | 69 | €14,977 | €3,105 | €2,654 | €8,074 |
| 5 | 83 | €18,016 | €3,735 | €3,237 | €11,310 |
| 6 | 100 | €21,706 | €4,500 | €3,945 | €15,255 |
| 7 | 119 | €25,830 | €5,355 | €4,736 | €19,991 |
| 8 | 143 | €31,040 | €6,435 | €5,735 | €25,726 |
| 9 | 172 | €37,334 | €7,740 | €6,943 | €32,669 |
| 10 | 206 | €44,714 | €9,270 | €8,359 | €41,028 |
| 11 | 248 | €53,831 | €11,160 | €10,108 | €51,136 |
| 12 | 297 | €64,467 | €13,365 | €12,149 | €63,285 |

Twee dingen vallen op:

1. **De eerste maanden verdien je bijna niets.** Dat hoort. De vaste kosten zijn laag, dus
   je verliest ook bijna niets — maar reken jezelf niet rijk op maand 2.
2. **De uren lopen op.** In maand 12 zit je op ruim 36 uur inpakken per maand.
   Dat is een dag per week. Zie `docs/07-operatie.md`: rond de 250 orders per maand moet
   het inpakken de deur uit.

Met een lagere inkoopprijs verschuift deze hele tabel omhoog. Reken hem opnieuw in de
cockpit zodra je echte cijfers hebt.

---

## Wanneer kun je stoppen met je baan

Je werkt nu 40-60 uur per week. De vraag is niet wanneer QUITTER winst maakt, maar wanneer
QUITTER meer oplevert dan je huidige inkomen — bij een werkweek die je aankunt.

| | Orders/maand | Winst/maand | Inpakuren/maand |
|---|---|---|---|
| Bijverdienste | 50 | ± €1.500 | 6 |
| Serieus tweede inkomen | 150 | ± €5.500 | 18 |
| **Vervangt een salaris** | **300** | **± €13.500** | **36** |
| Je hebt personeel of een fulfilmentpartner nodig | 750 | ± €36.000 | 90 |

*(Bij CAC €40-45 en de huidige inkoopaanname. Bij €0,09 inkoop haal je hetzelfde inkomen
bij ongeveer de helft van het aantal orders.)*

Het omslagpunt ligt rond **300 orders per maand**: tien per dag. Dat is een uur inpakken
per dag naast je werk, en het is haalbaar met één goed werkende advertentie.

---

## De vier knoppen, op volgorde van effect

1. **Inkoopprijs per stuk kauwgom.** Van €0,16 naar €0,09 is €38 meer marge per order.
   Niets anders komt in de buurt. Onderhandel op volume, op vooruitbetaling, op een
   jaarcontract — alles wat de prijs per stuk omlaag krijgt.
2. **Gemiddelde orderwaarde.** Elke euro extra AOV is een euro die je meer mag bieden op
   Facebook. Het tweede blikje (€14, kost €2,20) is de makkelijkste. Het partnerprogramma
   is de grootste.
3. **Advertentiekosten per klant.** Het verschil tussen €60 en €40 per klant is bij 300
   orders €6.000 per maand. Dat is een kwestie van testen, niet van budget.
4. **Prijs.** €199 → €219 is 10% meer marge zonder één cent extra kosten. Test het pas als
   de verkoop loopt, en test het echt (twee prijzen naast elkaar), niet op gevoel.

---

## Wat je nodig hebt om te beginnen

| Post | Bedrag | Wanneer |
|---|---|---|
| Domeinen (4×) | ± €40/jaar | Nu |
| Bv oprichten (notaris) | ± €500-800 | Voor de eerste verkoop |
| Eerste inkoop kauwgom (100 dozen) | ± €9.000 | AANNAME — dit is de grote post |
| Blikjes, dozen, drukwerk (100×) | ± €420 | Bij de eerste inkoop |
| Mollie | Geen vaste kosten, per transactie | Voor de eerste verkoop |
| Hosting en mailtool | ± €30/maand | Nu |
| AI-team (API) | ± €40-80/maand | Nu |
| Juridische toets voorwaarden | ± €500-1.500 | Voor de eerste verkoop |
| Eerste advertentiebudget | €1.000 om te testen | Na de eerste 25 handmatige orders |

De inkoop is verreweg de grootste post en ook de enige die je kunt uitstellen: begin met
de kleinste afname die de fabrikant accepteert, ook als de prijs per stuk dan hoger is.
Een dure eerste partij die verkoopt is beter dan een goedkope partij die in de gang staat.
