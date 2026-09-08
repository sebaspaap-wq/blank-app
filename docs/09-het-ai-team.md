# 9. Het AI-team

Je hebt geen personeel. Je hebt acht agents die elk één ding goed doen en die elkaar
werk kunnen geven. Ze delen dezelfde merkbriefing en dezelfde reclameregels, zodat alles
wat het bedrijf uitstuurt uit één mond lijkt te komen.

Er zit geen magie in. Elke agent gebruikt hetzelfde gereedschap dat jij ook met de hand
kunt aanroepen, en wat ze maken komt als bestand in het project terecht. Niets verdwijnt
in een chatvenster.

```bash
uv run quitter team                                    # wie er werkt
uv run quitter vraag REGIE "..."                       # geef een opdracht
uv run streamlit run streamlit_app.py                  # of via de cockpit, tabblad Team
```

Zet eerst je sleutel: `export ANTHROPIC_API_KEY=...`

---

## Wie doet wat

| Agent | Rol | Waarvoor je hem aanroept |
|---|---|---|
| **REGIE** | dagelijkse leiding | Alles wat uit meer dan één stuk bestaat. REGIE knipt het op en verdeelt het. |
| **PEN** | tekstschrijver | Webpagina's, advertentieteksten, verkoopmails, artikelen. |
| **COACH** | programmabegeleider | De negentig dagelijkse mails. Haalt per dag het schema op zodat de aantallen kloppen. |
| **MARKT** | marketeer | Campagnes, invalshoeken, budgetverdeling. Rekent altijd voor wat een klant mag kosten. |
| **BALIE** | klantenservice | Antwoorden op klantvragen. Escaleert alles wat medisch is. |
| **TOETS** | toezichthouder | Keurt elke tekst op de reclameregels. Sluit af met AKKOORD, AANPASSEN of AFGEKEURD. |
| **MAGAZIJN** | operatie en inkoop | Voorraad, inpaklijsten, inkoopadvies, en of je het inpakken nog aankunt. |
| **CIJFERS** | analist | Marges, scenario's, en de enige die mag zeggen dat iets niet uit kan. |

## De vaste volgorde

```
maker (PEN / COACH / MARKT)  →  TOETS  →  pas dan publiceren
```

REGIE bewaakt dat. Zegt TOETS "AANPASSEN", dan gaat het terug naar de maker met de
opmerkingen erbij — maximaal twee rondes, daarna komt het bij jou.

Alleen REGIE mag anderen aansturen. Dat is bewust: acht modellen die door elkaar praten
leveren geen bedrijf op, maar een vergadering.

---

## Wat ze kunnen (het gereedschap)

Achttien functies, allemaal in `quitter/tools/`. De belangrijkste:

| Gereedschap | Wat het doet |
|---|---|
| `merkbriefing` | De rode draad, de toon, de zinnen die van ons zijn. |
| `reclameregels` | Wat je niet mag beweren over een geneesmiddel. |
| `controleer_tekst` | Draait een tekst langs alle regels en geeft per bevinding een betere formulering. |
| `dagplan` | Wat een klant op dag X doet: sterkte, aantal stuks, blok, dagen te gaan. |
| `afbouwschema` | Het volledige schema van een programma. |
| `adviseer_programma` | Welk programma bij een roker past, op basis van zijn rookgedrag. |
| `financieel_rapport` | Marges, scenario's, break-even. |
| `doorrekenen` | Wat een maand oplevert bij X orders en Y advertentiekosten. |
| `inkoop_gevoeligheid` | Wat de inkoopprijs met de marge doet. |
| `voorraad`, `inpaklijst`, `orders` | De winkel. |
| `schrijf_bestand`, `lees_bestand`, `toon_map` | Werk opslaan en teruglezen. |

**Wat ze niet kunnen:** buiten `content/`, `site/` en `data/` schrijven. Een agent mag de
website vullen, niet zijn eigen broncode herschrijven. Dat wordt afgedwongen in
`quitter/paths.py` en getest in `tests/test_quitter.py`.

**Wat ze nooit verzinnen:** getallen. Aantallen stuks, prijzen, marges en dagplannen komen
altijd uit het gereedschap. Dat staat in elke systeemprompt en het is de belangrijkste
regel van het hele team — een verzonnen aantal stuks in een coachmail is een gebruiksfout
bij een geneesmiddel.

---

## Opdrachten die werken

```bash
# Een campagne, van bedenken tot goedgekeurd
uv run quitter vraag REGIE "Maak een Facebook-campagne voor mensen die al twee keer \
  gefaald zijn. Vijf invalshoeken, per invalshoek drie advertentieteksten en een \
  beeldbriefing. Laat alles langs TOETS en zet het in content/ads/."

# De eerste twee weken coachmails
uv run quitter dagmails standaard 1 14

# Een klantvraag beantwoorden
uv run quitter vraag BALIE "Klant mailt: 'Ik zit op dag 34 en heb ineens veel meer trek \
  dan vorige week. Doe ik iets fout?' Schrijf het antwoord."

# Nagaan of een korting kan
uv run quitter vraag CIJFERS "Kan ik in januari een actie doen van 25% korting op het \
  standaardprogramma? Reken voor wat dat met de marge en de break-even doet."

# Een tekst laten keuren
uv run quitter vraag TOETS "Keur deze advertentie: 'In 90 dagen gegarandeerd van je \
  verslaving af, zonder trek en zonder bijwerkingen.'"
```

---

## Wat het kost

Alles draait standaard op het beste model. Dat is een bewuste keuze: het duurste onderdeel
van QUITTER is niet een API-factuur, het is een verkeerde advertentie of een verkeerd
antwoord aan een klant.

In de praktijk: een opdracht van REGIE die drie collega's aanstuurt kost een paar tientjes
aan tokens per maand bij normaal gebruik. Elke actie wordt gelogd in `data/agent-log.jsonl`
met een kostenschatting erbij, en de cockpit laat het logboek zien.

---

## Wat je zelf blijft doen

De agents kunnen veel, maar niet alles. Bij jou blijft:

- **Geld uitgeven.** Advertentiebudget en inkoop gaan altijd langs jou.
- **Medische vragen.** Die gaan naar een huisarts of apotheker, nooit naar een model.
- **Het gesprek met MAE Pharma** en alles wat met de vergunning te maken heeft.
- **Inpakken en versturen** — tot je het uitbesteedt.
- **De eindbeslissing** over prijs, positionering en of iets naar buiten gaat.

En één ding dat je niet moet delegeren: **de eerste vijftig klanten zelf te woord staan.**
Daar leer je wat er echt misgaat in het programma. Zet BALIE er pas op als je weet welke
vragen er komen.
