# WOSZ — AI-organisatie

Systeem van vier gescheiden AI-agents (Marketing, Matching, Support, Financieel)
die de dagelijkse operatie van WOSZ uitvoeren, gecoordineerd door een
Directie-agent die rapporteert aan Sebas.

**Status:** alle vier de agents draaien — Matching, Support, Financieel en Marketing.

```
backend/    FastAPI-backend met de agents, de escalatiemotor en de event-bus
frontend/   wosz-app.html — het bestaande dashboard, gekoppeld aan de backend
docs/       De bouwopdracht en het architectuuroverzicht
```

## Aan de slag

**Dubbelklik op het startbestand.** Meer is het niet.

| Jouw computer | Bestand |
|---|---|
| Mac | `start.command` |
| Windows | `start-windows.bat` |
| Linux | `start.command` |

Er opent een zwart venster met tekst. Dat hoort zo — laat het openstaan. De
eerste keer duurt het een paar minuten (er wordt van alles geïnstalleerd);
daarna is het een paar seconden. Als het klaar is, opent je browser vanzelf
met het dashboard. Klik daar op **Demo: directie**.

**Stoppen:** sluit dat zwarte venster.

Op een Mac kan de eerste keer een waarschuwing komen dat het bestand van een
onbekende maker is. Klik dan met de rechtermuisknop op `start.command`, kies
*Openen*, en daarna nog een keer *Openen*.

Je hebt geen API-key nodig en je betaalt niets. Zonder key beslissen de agents
op vaste regels in plaats van met Claude; verder werkt alles hetzelfde.

Werkt het niet, of wil je liever zelf de commando's typen? Dan staat de
uitgebreide uitleg in [`backend/README.md`](backend/README.md).

## Twee dingen om te weten voordat je verder bouwt

**Geld gaat nooit automatisch de deur uit.** Er zit geen betaalintegratie in dit
systeem. Uitbetalen kan alleen doordat Sebas het zelf doet, na goedkeuring in het
dashboard. Dat is architecturaal afgedwongen, niet als regel voor een AI —
zie [`backend/app/payouts/README.md`](backend/app/payouts/README.md).

**De arbeidsrechtelijke toets komt eerst.** Randvoorwaarde 6.1 van de
bouwopdracht: laat een arbeidsjurist beoordelen of het model onder de Waadi valt
vóórdat hier echte medewerkersdata of transacties doorheen gaan.
