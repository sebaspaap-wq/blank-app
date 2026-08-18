"""Demodata om de backend lokaal te kunnen draaien.

De namen, strandtenten en functies komen overeen met wat wosz-app.html laat
zien, zodat het dashboard er met echte data herkenbaar uitziet.

Draai met:  python -m app.db.seed
"""

from __future__ import annotations

import asyncio
from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.domein import MatchStatus, ShiftStatus, nu
from app.db.models import (
    Bedrijf,
    Campagne,
    CampagneResultaat,
    Doelstelling,
    Hoek,
    Kennisbankitem,
    Level,
    Match,
    Referral,
    Shift,
    User,
)
from app.db.session import maak_tabellen, sessie

# (naam, e-mail, functies, beschikbare dagen, seizoensuren, ervaringsjaren, uurloonwens)
MEDEWERKERS = [
    ("Sanne de Vries", "sanne@voorbeeld.nl", ["bediening", "bar"], ["do", "vr", "za", "zo"], 74.0, 2.0, "€13,50"),
    ("Milan Bakker", "milan@voorbeeld.nl", ["bar", "bediening"], ["vr", "za", "zo"], 61.0, 1.0, "€14,00"),
    ("Tom Hendriks", "tom@voorbeeld.nl", ["bediening"], ["za", "zo"], 32.0, 0.5, "€13,00"),
    ("Lisa Mulder", "lisa@voorbeeld.nl", ["keuken"], ["ma", "di", "wo", "do", "vr"], 50.0, 3.0, "€14,50"),
    ("Noor Jansen", "noor@voorbeeld.nl", ["bediening", "host / runner"], ["za", "zo", "ma"], 18.0, 0.0, "€12,50"),
    ("Daan Visser", "daan@voorbeeld.nl", ["keuken", "bediening"], ["wo", "do", "vr", "za"], 61.0, 4.0, "€15,00"),
]

BEDRIJVEN = [
    ("Strandtent Zuid", "Zandvoort"),
    ("Beachclub Noord", "Zandvoort"),
    ("Café De Kust", "Zandvoort"),
    ("Strandtent Boulevard", "Zandvoort"),
]

#: Contactpersoon per bedrijf, in dezelfde volgorde als ``BEDRIJVEN``.
HORECA_CONTACTEN = [
    ("Ruben Postma", "ruben@strandtentzuid.nl"),
    ("Iris de Groot", "iris@beachclubnoord.nl"),
    ("Joost Meijer", "joost@cafedekust.nl"),
    ("Femke Smit", "femke@strandtentboulevard.nl"),
]

DOELEN = [
    ("Aanmeldingen deze week", 128, 200, False, 1),
    ("Actieve strandtenten", 6, 15, False, 2),
    ("Omzet deze maand", 1240, 2500, True, 3),
]

# Kennisbank: (vraag, antwoord, trefwoorden, categorie, vereist_mens)
#
# Antwoorden zijn de teksten die Support letterlijk verstuurt. Ze horen dus door
# Sebas geschreven of nagelezen te zijn — de agent formuleert nooit zelf.
#
# ``vereist_mens=True`` markeert onderwerpen waar Support nooit automatisch op
# antwoordt, ook al staat er een antwoord: geld, tarieven, contractvoorwaarden
# (paragraaf 3.3). De agent escaleert dan naar Sebas en meldt welk antwoord hij
# zou hebben gebruikt.
KENNISBANK = [
    (
        "Hoe meld ik me af voor een shift?",
        "Afmelden doe je in de app bij 'Mijn shifts'. Doe het zo snel mogelijk, "
        "dan kunnen we op tijd iemand anders zoeken. Lukt het binnen 24 uur voor "
        "de shift niet meer via de app, stuur dan even een bericht.",
        ["afmelden", "afzeggen", "annuleren", "afmelding", "ziek"],
        "shifts",
        False,
    ),
    (
        "Hoe werkt het levelsysteem?",
        "Elk uur dat je werkt telt mee voor je level dit seizoen. Hoe hoger je "
        "level, hoe eerder je mag reageren op nieuwe shifts. Je ziet je "
        "voortgang in de app onder 'Levels'.",
        ["level", "levels", "levelsysteem", "punten", "voortgang"],
        "levels",
        False,
    ),
    (
        "Wat moet ik aantrekken tijdens een shift?",
        "Meestal een zwart shirt en een zwarte broek, met dichte schoenen. "
        "Sommige strandtenten hebben eigen kleding — dat staat dan bij de shift "
        "vermeld. Twijfel je, vraag het even na bij het bedrijf.",
        ["kleding", "aantrekken", "dresscode", "uniform", "schoenen"],
        "praktisch",
        False,
    ),
    (
        "Hoe nodig ik een vriend uit?",
        "In de app vind je onder 'Vrienden' je persoonlijke uitnodigingslink. "
        "Deel die met wie je mee wilt krijgen; zodra hij of zij zich aanmeldt en "
        "gaat werken, zie je de voortgang in je overzicht.",
        ["vriend", "vrienden", "uitnodigen", "aanbrengen", "referral", "link"],
        "vrienden",
        False,
    ),
    (
        "Ik kan niet inloggen in de app",
        "Probeer eerst uit te loggen en opnieuw in te loggen met het e-mailadres "
        "waarmee je je hebt aangemeld. Werkt dat niet, stuur dan een bericht met "
        "het e-mailadres dat je gebruikt, dan kijken we mee.",
        ["inloggen", "wachtwoord", "account", "login"],
        "praktisch",
        False,
    ),
    (
        "Wanneer krijg ik uitbetaald?",
        "Uitbetalingen worden per periode klaargezet en door WOSZ handmatig "
        "gecontroleerd voordat ze de deur uitgaan.",
        ["uitbetaling", "uitbetaald", "betaling", "geld", "loon", "salaris"],
        "geld",
        True,
    ),
    (
        "Kan ik meer per uur verdienen?",
        "Het uurloon wordt per shift door het bedrijf bepaald en staat bij de "
        "shift vermeld.",
        ["uurloon", "tarief", "verdienen", "loonsverhoging"],
        "geld",
        True,
    ),
    (
        "Wat staat er in mijn overeenkomst?",
        "De voorwaarden van je inzet staan in de overeenkomst die je bij "
        "aanmelding hebt gekregen.",
        ["contract", "overeenkomst", "voorwaarden", "opzeggen", "juridisch"],
        "contract",
        True,
    ),
]


# Huisstijl-hoeken: (naam, omschrijving, toon, voorbeelden)
#
# Dit is de huisstijl waarbinnen de Marketing-agent zelfstandig mag plannen.
# Een hoek die hier niet staat, is een nieuwe campagne-richting en dus tier 3.
HOEKEN = [
    (
        "Geen zzp-gedoe",
        "Werken aan het strand zonder inschrijving bij de KvK, zonder facturen "
        "en zonder administratie achteraf.",
        "Nuchter en direct. Spreek de frustratie aan die mensen kennen van "
        "andere klusplatforms. Geen uitroeptekens.",
        [
            "Geen KvK, geen facturen, geen gedoe.",
            "Werken op het strand zonder papierwinkel.",
        ],
    ),
    (
        "Vrienden-bonus",
        "Samen met je vrienden werken op het strand, en er iets extra's aan "
        "overhouden als je ze meeneemt.",
        "Speels en sociaal. Richt je op groepjes die samen willen werken.",
        [
            "Neem je vrienden mee naar het strand.",
            "Samen werken is minder werk.",
        ],
    ),
    (
        "Strandzomer",
        "De sfeer van een zomer werken aan zee: zonsondergangen, vaste crew, "
        "het strand als werkplek.",
        "Warm en beeldend. Laat de zomer het werk verkopen.",
        [
            "Je kantoor heeft dit uitzicht niet.",
            "Zonsondergang als einde van je dienst.",
        ],
    ),
]

# Campagnes: (naam, hoek-index, dagbudget_eur, verwachte kosten per aanmelding)
CAMPAGNES = [
    ("Geen zzp-gedoe", 0, 25.00, 4.50),
    ("Vrienden-bonus", 1, 15.00, 6.00),
]


async def seed(s: AsyncSession) -> None:
    bestaat = await s.scalar(select(func.count()).select_from(User))
    if bestaat:
        print("Database bevat al gegevens — seed overgeslagen.")
        return

    s.add(User(naam="Sebas", rol="directie", email="sebas@wosz.nl"))

    medewerkers: list[User] = []
    for naam, mail, functies, dagen, _uren, ervaring, wens in MEDEWERKERS:
        gebruiker = User(
            naam=naam,
            rol="medewerker",
            email=mail,
            woonplaats="Zandvoort",
            functies=functies,
            beschikbare_dagen=dagen,
            ervaring_jaren=ervaring,
            gewenst_uurloon=wens,
        )
        s.add(gebruiker)
        medewerkers.append(gebruiker)
    await s.flush()

    for gebruiker, (_, _, _, _, uren, _e, _w) in zip(medewerkers, MEDEWERKERS, strict=True):
        from app.core.domein import level_voor_uren

        s.add(
            Level(
                medewerker_id=gebruiker.id,
                seizoen_uren=uren,
                huidig_level=level_voor_uren(uren)["level"],
            )
        )

    bedrijven: list[Bedrijf] = []
    for naam, plaats in BEDRIJVEN:
        bedrijf = Bedrijf(naam=naam, plaats=plaats)
        s.add(bedrijf)
        bedrijven.append(bedrijf)
    await s.flush()

    # Elk bedrijf krijgt een contactpersoon met een horeca-account, zodat het
    # horecascherm meteen bij een echt bedrijf hoort in plaats van bij een id
    # dat je zelf moet raden.
    for bedrijf, (contact, mail) in zip(bedrijven, HORECA_CONTACTEN, strict=True):
        gebruiker = User(naam=contact, rol="horeca", email=mail, bedrijf_id=bedrijf.id)
        s.add(gebruiker)
        await s.flush()
        bedrijf.contact_user_id = gebruiker.id
    await s.flush()

    # Anker de shifts op het eerstvolgende weekend: dan sluiten ze aan op de
    # beschikbaarheid van de demomedewerkers, zodat een 'match run' meteen iets
    # zichtbaars oplevert.
    vandaag = nu().date()
    vrijdag = vandaag + timedelta(days=(4 - vandaag.weekday()) % 7 or 7)
    zaterdag = vrijdag + timedelta(days=1)
    zondag = vrijdag + timedelta(days=2)

    shifts = [
        (bedrijven[0], zaterdag, "17:00-01:00", "bediening", 2, 8.0, "€13,00 – €14,50"),
        (bedrijven[1], zondag, "12:00-18:00", "keuken", 1, 6.0, "€13,50"),
        (bedrijven[2], vrijdag, "18:00-00:00", "bar", 1, 6.0, "€12,50 – €13,50"),
        (bedrijven[3], zondag, "10:00-16:00", "host / runner", 2, 6.0, "€12,50"),
    ]
    for bedrijf, datum, tijd, functie, aantal, duur, uurloon in shifts:
        s.add(
            Shift(
                bedrijf_id=bedrijf.id,
                datum=datum,
                tijd=tijd,
                functie=functie,
                aantal_gevraagd=aantal,
                duur_uren=duur,
                uurloon=uurloon,
                status=str(ShiftStatus.OPEN),
            )
        )

    # Een gewerkte shift van vorige week, zodat het medewerkerscherm
    # geschiedenis heeft en het horecascherm gewerkte uren kan tonen.
    #
    # De match staat bewust op 'bevestigd' en niet op 'gewerkt': ``app.db.demo``
    # boekt de uren daarna via de Matching-agent. Zo doorloopt de demodata
    # dezelfde weg als echte data — inclusief het event naar Financieel, dat het
    # factuurconcept voor dit bedrijf aanmaakt.
    vorige_zaterdag = zaterdag - timedelta(days=7)
    afgerond = Shift(
        bedrijf_id=bedrijven[0].id,
        datum=vorige_zaterdag,
        tijd="16:00-22:00",
        functie="bediening",
        aantal_gevraagd=1,
        duur_uren=6.0,
        uurloon="€13,25",
        status=str(ShiftStatus.GEMATCHT),
    )
    s.add(afgerond)
    await s.flush()
    s.add(
        Match(
            shift_id=afgerond.id,
            medewerker_id=medewerkers[0].id,
            status=str(MatchStatus.BEVESTIGD),
            onderbouwing="Hoogste levelprioriteit en ervaring met bediening.",
        )
    )

    for label, waarde, doel, is_euro, volgorde in DOELEN:
        s.add(
            Doelstelling(
                label=label,
                waarde=waarde,
                doel=doel,
                is_euro=is_euro,
                volgorde=volgorde,
            )
        )

    for vraag, antwoord, trefwoorden, categorie, vereist_mens in KENNISBANK:
        s.add(
            Kennisbankitem(
                vraag=vraag,
                antwoord=antwoord,
                trefwoorden=trefwoorden,
                categorie=categorie,
                vereist_mens=vereist_mens,
            )
        )

    # Sanne heeft Tom aangebracht; Tom zit op 32 uur en heeft de 50-uursgrens
    # dus nog niet gehaald. Werkt hij nog een shift, dan zet de Financieel-agent
    # de vriendenbonus klaar ter goedkeuring (tier 3).
    sanne = next(m for m in medewerkers if m.naam == "Sanne de Vries")
    tom = next(m for m in medewerkers if m.naam == "Tom Hendriks")
    s.add(
        Referral(
            medewerker_id=sanne.id,
            vriend_id=tom.id,
            uren_vriend=32.0,
            bonus_status="bezig",
            bonus_bedrag_cent=2000,
        )
    )

    hoeken: list[Hoek] = []
    for naam, omschrijving, toon, voorbeelden in HOEKEN:
        hoek = Hoek(
            naam=naam,
            omschrijving=omschrijving,
            toon=toon,
            voorbeelden=voorbeelden,
            goedgekeurd=True,
        )
        s.add(hoek)
        hoeken.append(hoek)
    await s.flush()

    campagnes: list[Campagne] = []
    for naam, hoek_index, dagbudget, verwacht in CAMPAGNES:
        campagne = Campagne(
            naam=naam,
            hoek_id=hoeken[hoek_index].id,
            dagbudget_cent=round(dagbudget * 100),
            verwachte_kosten_per_aanmelding_cent=round(verwacht * 100),
        )
        s.add(campagne)
        campagnes.append(campagne)
    await s.flush()

    # Zeven dagen resultaten, zodat de agent iets te vergelijken heeft.
    # "Geen zzp-gedoe" presteert duidelijk beter dan "Vrienden-bonus" —
    # net als in de demo van het dashboard.
    for dag in range(1, 8):
        datum = vandaag - timedelta(days=dag)
        s.add(
            CampagneResultaat(
                campagne_id=campagnes[0].id,
                datum=datum,
                uitgaven_cent=2500,
                vertoningen=4200,
                klikken=190,
                aanmeldingen=6,
            )
        )
        s.add(
            CampagneResultaat(
                campagne_id=campagnes[1].id,
                datum=datum,
                uitgaven_cent=1500,
                vertoningen=2600,
                klikken=80,
                aanmeldingen=2,
            )
        )

    await s.commit()
    print(
        f"Seed klaar: {len(MEDEWERKERS)} medewerkers, {len(BEDRIJVEN)} bedrijven, "
        f"{len(shifts)} open shifts, {len(KENNISBANK)} kennisbankitems, "
        f"{len(HOEKEN)} hoeken, {len(CAMPAGNES)} campagnes."
    )


async def main() -> None:
    await maak_tabellen()
    async with sessie() as s:
        await seed(s)


if __name__ == "__main__":
    asyncio.run(main())
