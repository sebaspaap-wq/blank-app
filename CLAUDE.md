# Werken aan QUITTER

QUITTER verkoopt een afbouwprogramma van 90 dagen met nicotinekauwgom in aflopende sterkte.
De rode draad van het bedrijf:

> QUITTER haalt de nicotine er in 90 dagen uit — volgens schema, niet op wilskracht.

Alles wat je maakt moet op die zin terug te voeren zijn.

## Regels die niet onderhandelbaar zijn

1. **Verzin nooit een getal.** Aantallen stuks, sterktes, prijzen, marges en dagplannen
   komen uit `quitter/taper.py`, `quitter/catalog.py` en `quitter/finance.py`. Een verkeerd
   aantal stuks in een coachmail is een gebruiksfout bij een geneesmiddel.
2. **Nicotinekauwgom is een geneesmiddel.** Reclameregels staan in `quitter/compliance.py`.
   Draai `controleer_tekst` over alles wat naar buiten gaat. Beloof nooit een uitkomst,
   alleen het schema.
3. **Het afbouwschema loopt alleen omlaag.** Dat wordt afgedwongen in `Schema.__post_init__`
   en getest. Pas je een schema aan, draai dan de tests.
4. **Eén bron van waarheid.** Prijs veranderen? Alleen in `quitter/catalog.py`, daarna
   `python -m quitter.site_build` om de website bij te werken.
5. **Nederlands.** Code, documentatie, commentaar en alles wat de klant leest.
6. **Medische vragen gaan naar een mens.** Nooit door een agent laten beantwoorden;
   de escalatielijst staat in `quitter/compliance.py`.

## De opzet

| Map | Wat |
|---|---|
| `quitter/` | Merk, catalogus, schema's, rekenmodel, regels, agents en gereedschap |
| `site/` | Statische website; `assets/data.js` wordt gegenereerd, niet met de hand aangepast |
| `docs/` | Het bedrijfsplan |
| `content/` | Wat de agents produceren |
| `data/` | Voorraad, orders, agent-logboek |

Agents mogen alleen schrijven in `content/`, `site/` en `data/` (`quitter/paths.py`).

## Controleren

```bash
uv run python -m pytest tests -q      # 36 tests
uv run python -m quitter.site_build   # website bijwerken na een prijs- of schemawijziging
uv run quitter marge                  # klopt het rekenmodel nog
```
