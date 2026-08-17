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

from app.core.domein import ShiftStatus, nu
from app.db.models import (
    Bedrijf,
    Doelstelling,
    Kennisbankitem,
    Level,
    Referral,
    Shift,
    User,
)
from app.db.session import maak_tabellen, sessie

MEDEWERKERS = [
    ("Sanne de Vries", ["bediening", "bar"], ["do", "vr", "za", "zo"], 74.0),
    ("Milan Bakker", ["bar", "bediening"], ["vr", "za", "zo"], 61.0),
    ("Tom Hendriks", ["bediening"], ["za", "zo"], 32.0),
    ("Lisa Mulder", ["keuken"], ["ma", "di", "wo", "do", "vr"], 50.0),
    ("Noor Jansen", ["bediening", "host / runner"], ["za", "zo", "ma"], 18.0),
    ("Daan Visser", ["keuken", "bediening"], ["wo", "do", "vr", "za"], 61.0),
]

BEDRIJVEN = [
    ("Strandtent Zuid", "Zandvoort"),
    ("Beachclub Noord", "Zandvoort"),
    ("Café De Kust", "Zandvoort"),
    ("Strandtent Boulevard", "Zandvoort"),
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


async def seed(s: AsyncSession) -> None:
    bestaat = await s.scalar(select(func.count()).select_from(User))
    if bestaat:
        print("Database bevat al gegevens — seed overgeslagen.")
        return

    s.add(User(naam="Sebas", rol="directie", email="sebas@wosz.nl"))

    medewerkers: list[User] = []
    for naam, functies, dagen, uren in MEDEWERKERS:
        gebruiker = User(
            naam=naam,
            rol="medewerker",
            functies=functies,
            beschikbare_dagen=dagen,
        )
        s.add(gebruiker)
        medewerkers.append(gebruiker)
    await s.flush()

    for gebruiker, (_, _, _, uren) in zip(medewerkers, MEDEWERKERS, strict=True):
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

    # Anker de shifts op het eerstvolgende weekend: dan sluiten ze aan op de
    # beschikbaarheid van de demomedewerkers, zodat een 'match run' meteen iets
    # zichtbaars oplevert.
    vandaag = nu().date()
    vrijdag = vandaag + timedelta(days=(4 - vandaag.weekday()) % 7 or 7)
    zaterdag = vrijdag + timedelta(days=1)
    zondag = vrijdag + timedelta(days=2)

    shifts = [
        (bedrijven[0], zaterdag, "17:00-01:00", "bediening", 2, 8.0),
        (bedrijven[1], zondag, "12:00-18:00", "keuken", 1, 6.0),
        (bedrijven[2], vrijdag, "18:00-00:00", "bar", 1, 6.0),
        (bedrijven[3], zondag, "10:00-16:00", "host / runner", 2, 6.0),
    ]
    for bedrijf, datum, tijd, functie, aantal, duur in shifts:
        s.add(
            Shift(
                bedrijf_id=bedrijf.id,
                datum=datum,
                tijd=tijd,
                functie=functie,
                aantal_gevraagd=aantal,
                duur_uren=duur,
                status=str(ShiftStatus.OPEN),
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

    await s.commit()
    print(
        f"Seed klaar: {len(MEDEWERKERS)} medewerkers, {len(BEDRIJVEN)} bedrijven, "
        f"{len(shifts)} open shifts, {len(KENNISBANK)} kennisbankitems."
    )


async def main() -> None:
    await maak_tabellen()
    async with sessie() as s:
        await seed(s)


if __name__ == "__main__":
    asyncio.run(main())
