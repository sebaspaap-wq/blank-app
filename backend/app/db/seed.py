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
from app.db.models import Bedrijf, Doelstelling, Level, Shift, User
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

    await s.commit()
    print(
        f"Seed klaar: {len(MEDEWERKERS)} medewerkers, {len(BEDRIJVEN)} bedrijven, "
        f"{len(shifts)} open shifts."
    )


async def main() -> None:
    await maak_tabellen()
    async with sessie() as s:
        await seed(s)


if __name__ == "__main__":
    asyncio.run(main())
