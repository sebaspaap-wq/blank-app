# Uitgaande kanalen

Hier staat het enige stuk code dat iets de deur uit doet: berichten versturen en
content publiceren.

## Waarom dit geen onderdeel van een agent is

Dezelfde scheiding als bij uitbetalingen, om dezelfde reden.

Een agent schrijft een bericht in de outbox — een rij in `berichten` met de
inhoud van een goedgekeurd sjabloon. Daarmee houdt zijn rol op. Het versturen
gebeurt hier, in de applicatielaag, door een worker die de outbox leegt.

Dat is geen stijlkeuze. `AgentSettings` bevat geen enkel veld met
SMTP-gegevens, API-tokens of accountnamen — die staan in `Settings`, en dat
object krijgen agents niet. Een agent die zelf iets zou willen versturen, heeft
dus geen adres, geen wachtwoord en geen client. Er is niets om te misbruiken en
niets om te vergeten.

De volgorde van afhankelijkheden is:

```
app/agents/     schrijft naar de outbox
      |
      v
app/kanalen/    leest de outbox en verstuurt
```

Nooit andersom. Een test controleert dat: `tests/test_kanalen.py` loopt de
imports van `app/agents/` na en faalt als er een pad naar `app.kanalen` in zit.

## Welke driver er draait

Per kanaal is er één driver, gekozen via een environment variable.

| Kanaal | Variabele | Waarden | Standaard |
|---|---|---|---|
| Berichten (WhatsApp/e-mail) | `WOSZ_BERICHT_DRIVER` | `console`, `email` | `console` |
| Social posts | `WOSZ_SOCIAL_DRIVER` | `console` | `console` |

`console` is de standaard en verstuurt niets: hij schrijft de tekst naar het
serverlog en markeert het bericht als verstuurd. Zo kun je het hele systeem
draaien — inclusief de automatische opvolging — zonder dat er ooit iets naar een
echte medewerker gaat. Dat is de veilige stand om in te ontwikkelen.

`email` verstuurt echt, via SMTP. Hij weigert te starten zonder complete
configuratie: liever een duidelijke fout bij het opstarten dan berichten die
stilletjes nergens aankomen.

## Een kanaal aansluiten

1. Schrijf een klasse met een `verstuur`-methode (zie `basis.py`).
2. Registreer hem in `KIES_DRIVER` in `__init__.py`.
3. Zet de bijbehorende gegevens in `Settings`, nooit in `AgentSettings`.

Wat je daarbij niet hoeft te doen: iets aan de agents veranderen. Die weten niet
langs welke weg hun bericht vertrekt, en dat hoort zo.

## Publiceren gaat automatisch — maar pas nadat je een kanaal aanzet

De Marketing-agent plant content op de hoeken die Sebas heeft goedgekeurd
(paragraaf 3.1: tier 1). Zodra de geplande datum is aangebroken, publiceert de
scheduler die post zelf. Er zit geen extra goedkeuring per post tussen: de hoek
goedkeuren *is* de beslissing, en per post opnieuw akkoord geven zou het hele
punt van automatisering wegnemen.

De rem zit ergens anders, en die is architecturaal: zolang `WOSZ_SOCIAL_DRIVER`
op `console` staat — de standaard — bestaat er geen verbinding met een social
platform. Publiceren kan dan niet misgaan, want er is niets om naartoe te
publiceren. Het aanzetten van een echt kanaal is een handeling van Sebas, met
zijn eigen accountgegevens, en daarmee zijn expliciete akkoord op alles wat er
daarna langs die weg naar buiten gaat.

## Wat er bewust ontbreekt

Er is geen driver voor Instagram, TikTok of Meta Ads. Die koppelingen vragen om
een zakelijk account, OAuth en een goedkeuringstraject bij Meta; dat is een
beslissing van Sebas en geen implementatiedetail. De `console`-driver voor
social laat zien wat er gepubliceerd zou worden, zodat de rest van de keten —
plannen, tekst schrijven, publiceren — nu al compleet werkt en er straks alleen
een driver bijkomt.

Er is ook geen driver die advertentiebudgetten aanpast. Dat is dezelfde grens
als bij uitbetalingen: het systeem stelt een verschuiving voor en Sebas voert
hem uit in Meta Ads Manager. Zie `app/agents/marketing.py`.
