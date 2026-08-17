# Uitbetalingen — waarom hier geen betaal-API staat

Dit is de enige plek in het systeem waar uitbetalingen langskomen. Wat je hier
**niet** vindt is net zo belangrijk als wat er wel staat:

- geen Mollie-, Stripe- of bank-client;
- geen API-key, IBAN of ander betaalcredential;
- geen functie die geld verplaatst.

## Waarom niet "de agent mag het niet"

Randvoorwaarde 6.2 van de bouwopdracht vraagt om een harde technische
beperking, niet om een regel die een AI moet volgen. Een regel in een
systeemprompt is een verzoek: hij kan verkeerd begrepen worden, door een
prompt-injectie omzeild worden, of bij een refactor sneuvelen. Daarom is de
scheiding hier structureel opgelost, op drie niveaus:

1. **Er is niets om aan te roepen.** Het systeem heeft geen betaalintegratie.
   Ook een agent met volledige codetoegang kan geen betaling initiëren, want de
   functie bestaat niet. De laatste stap is en blijft een mens bij zijn bank.

2. **De agents zien de configuratie niet.** Agents krijgen `AgentSettings`
   (`app/config.py`), en dat object heeft structureel geen enkel veld dat met
   uitbetalen te maken heeft. Er valt niets te lekken, want er is niets ingeladen.

3. **Agents kunnen deze module niet importeren.** `tests/test_betaalscheiding.py`
   loopt de import-graaf van elke module onder `app/agents/` na en faalt zodra
   er ook maar een indirect pad naar `app.payouts` ontstaat. Wie die grens
   probeert te overschrijden, krijgt een rode build — geen productie-incident.

## Wat er wel gebeurt

De Financieel-agent berekent bedragen en zet concepten klaar. Meer niet. Het
pad naar geld loopt zo:

```
Financieel-agent           berekent bedrag, maakt conceptrecord (tier 3)
        ↓
Directie-agent             legt de beslissing voor in het dashboard
        ↓
Sebas klikt "Goedkeuren"   -> uitbetalingsopdracht krijgt status
                              "klaar-voor-export"
        ↓
Sebas downloadt de export  -> CSV met begunstigde, bedrag en omschrijving
        ↓
Sebas voert de betaling    <- buiten dit systeem om, bij zijn eigen bank
zelf uit
        ↓
Sebas vinkt af             -> status "handmatig-voldaan" (audit-trail)
```

De statussen in `UitbetalingStatus` weerspiegelen dit: er is bewust geen status
"betaald door het systeem", omdat het systeem dat niet kan.

## Voor later

Mocht er ooit toch een betaalprovider aangesloten worden, dan hoort die als een
apart proces te draaien met eigen credentials, dat deze exports leest — niet als
een module die vanuit dit codebestand aanroepbaar is. De import-guard-test moet
dan blijven staan.
