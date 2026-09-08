"""De rem op het systeem.

QUITTER verkoopt (straks) een geneesmiddel. Dat betekent dat niet elke tekst
mag wat een gewone webshop mag. Dit bestand bevat de regels als code, zodat
elke AI-agent er langs moet voordat er iets naar buiten gaat — en zodat een
overtreding een foutmelding is en geen boete.

Belangrijk: dit is een werkinstrument, geen juridisch advies. De definitieve
toets ligt bij de Keuringsraad (KOAG/KAG) voor publieksreclame en bij de
fabrikant/IGJ voor alles rond de handelsvergunning. Zie docs/04-compliance.md.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class Ernst(str, Enum):
    BLOKKEREND = "blokkerend"   # zo niet naar buiten
    WAARSCHUWING = "waarschuwing"  # mens moet er even naar kijken


@dataclass(frozen=True)
class Regel:
    code: str
    patroon: str
    ernst: Ernst
    waarom: str
    beter: str


# --------------------------------------------------------------------------
# Verboden en riskante claims
# --------------------------------------------------------------------------

REGELS: list[Regel] = [
    Regel(
        "C01", r"\b(gegarandeerd|garantie op succes|100% ?(succes|rookvrij)|verzekerd van)\b",
        Ernst.BLOKKEREND,
        "Een absolute werkingsclaim mag niet bij een geneesmiddel en is bovendien niet waar.",
        "Zeg wat het programma doet ('je bouwt af volgens schema'), niet wat het garandeert.",
    ),
    Regel(
        "C02", r"\b(geneest|genezing|medicijn tegen kanker|voorkomt kanker|kankervrij)\b",
        Ernst.BLOKKEREND,
        "Claims over ernstige ziekten zijn verboden in publieksreclame.",
        "Laat ziektebeelden helemaal weg. Praat over roken, niet over de gevolgen.",
    ),
    Regel(
        "C03", r"\b(bijwerkingsvrij|geen bijwerkingen|volkomen veilig|zonder risico)\b",
        Ernst.BLOKKEREND,
        "Veiligheidsclaims over een geneesmiddel mogen niet zo absoluut zijn.",
        "Verwijs naar de bijsluiter: 'Lees voor gebruik de bijsluiter.'",
    ),
    Regel(
        "C04", r"\b(dokter|arts|huisarts|apotheker)(s|en)? (raadt|raden|beveelt|bevelen|adviseert|adviseren)\b",
        Ernst.BLOKKEREND,
        "Aanbeveling door beroepsbeoefenaren in publieksreclame voor geneesmiddelen is verboden.",
        "Gebruik gewone klantervaringen of laat het weg.",
    ),
    Regel(
        "C05", r"\b(gratis \w*(proef|monster|sample|pakket)\w*|(proef|monster)\w* gratis|weggeef\w*|win een|kans op een|maak kans)\b",
        Ernst.BLOKKEREND,
        "Gratis monsters en prijsvragen zijn niet toegestaan bij geneesmiddelenreclame.",
        "Werk met korting op de eerste bestelling in plaats van weggeefacties.",
    ),
    Regel(
        "C06", r"\b(kinderen|tieners|jongeren|onder de 18|16-jarige)\b",
        Ernst.BLOKKEREND,
        "Nooit richten op of afbeelden van minderjarigen. Het product is 18+.",
        "Haal de doelgroep weg of maak expliciet dat het product 18+ is.",
    ),
    Regel(
        "C07", r"(\bafvallen\b|\bdieet\b|kilo's kwijt|\bslanker\b|\bval\w*( \w+){0,2} af\b|\bkom(t|en)? niet aan\b)",
        Ernst.BLOKKEREND,
        "Nicotine als afslankmiddel positioneren is verboden en schadelijk.",
        "Behandel gewichtstoename hooguit feitelijk in de coaching, nooit als verkoopargument.",
    ),
    Regel(
        "C08", r"\b(zonder (enige )?(trek|ontwenning)|je merkt er niets van|moeiteloos stoppen)\b",
        Ernst.WAARSCHUWING,
        "Belooft een ervaring die het product niet kan waarmaken. Levert teleurstelling en retouren op.",
        "Wees eerlijk: 'de trek wordt kleiner, hij verdwijnt niet meteen'.",
    ),
    Regel(
        "C09", r"\b(\d{2,3}\s?%\s?(slaagkans|succes|van de gebruikers))\b",
        Ernst.WAARSCHUWING,
        "Elk percentage over effectiviteit moet herleidbaar zijn tot een bron en door de Keuringsraad.",
        "Alleen gebruiken met bronvermelding en na goedkeuring. Anders weglaten.",
    ),
    Regel(
        "C10", r"\b(veiliger dan roken|gezonder alternatief|onschadelijk)\b",
        Ernst.WAARSCHUWING,
        "Vergelijkende gezondheidsclaims zijn gevoelig en moeten letterlijk uit de SmPC komen.",
        "Beschrijf de functie ('vervangt de nicotine uit sigaretten'), niet de gezondheidswinst.",
    ),
    Regel(
        "C11", r"\b(bestel nu en stop morgen|vandaag nog rookvrij|in \d+ dagen rookvrij gegarandeerd)\b",
        Ernst.WAARSCHUWING,
        "Suggereert een uitkomst op een termijn die je niet kunt beloven.",
        "Beloof het schema, niet de uitkomst: 'in 90 dagen bouw je af naar nul'.",
    ),
]

# Wat er verplicht bij moet zodra er een geneesmiddel in de doos zit.
VERPLICHTE_ELEMENTEN = [
    "Lees voor gebruik de bijsluiter.",
    "Uitsluitend voor personen van 18 jaar en ouder.",
]

# Vragen die een AI nooit zelf beantwoordt. Deze gaan naar een mens (of naar
# de apotheker/arts van de klant).
ESCALATIE_ONDERWERPEN = [
    "zwanger", "zwangerschap", "borstvoeding", "hartinfarct", "hartaanval",
    "beroerte", "hartklachten", "hartritme", "bloeddrukmedicatie", "diabetes",
    "insuline", "epilepsie", "nierfunctie", "leverfunctie", "maagzweer",
    "allergisch", "allergie", "overdosis", "te veel gekauwd", "misselijk en duizelig",
    "kind heeft", "hond heeft", "ingeslikt", "spoedeisende", "112",
    "antidepressiva", "bupropion", "varenicline", "champix", "zyban",
]


@dataclass(frozen=True)
class Bevinding:
    regel: Regel
    fragment: str
    positie: int


def controleer(tekst: str) -> list[Bevinding]:
    """Loop een tekst na langs alle regels."""
    bevindingen: list[Bevinding] = []
    for regel in REGELS:
        for match in re.finditer(regel.patroon, tekst, flags=re.IGNORECASE):
            bevindingen.append(Bevinding(regel, match.group(0), match.start()))
    return bevindingen


def is_publiceerbaar(tekst: str) -> bool:
    return not any(b.regel.ernst is Ernst.BLOKKEREND for b in controleer(tekst))


def moet_escaleren(bericht: str) -> list[str]:
    """Welke onderwerpen in een klantbericht om een mens vragen."""
    lager = bericht.lower()
    return [o for o in ESCALATIE_ONDERWERPEN if o in lager]


def rapporteer(tekst: str) -> str:
    bevindingen = controleer(tekst)
    if not bevindingen:
        return "Geen bevindingen. Deze tekst mag door de merktoets heen."
    regels = []
    for b in bevindingen:
        regels.append(
            f"[{b.regel.ernst.value.upper()}] {b.regel.code} — \"{b.fragment}\"\n"
            f"    waarom: {b.regel.waarom}\n"
            f"    beter : {b.regel.beter}"
        )
    return "\n".join(regels)


def instructie_voor_agents() -> str:
    """De compliance-briefing die elke schrijvende agent meekrijgt."""
    verboden = "\n".join(f"- {r.code}: {r.waarom} → {r.beter}" for r in REGELS)
    verplicht = "\n".join(f"- {e}" for e in VERPLICHTE_ELEMENTEN)
    return f"""# Wat je niet mag schrijven

QUITTER verkoopt een geneesmiddel. Voor publieksreclame gelden strengere regels
dan voor een gewone webshop. Houd je hieraan, ook als het de tekst zwakker maakt:

{verboden}

## Verplicht bij elke uiting waarin de kauwgom voorkomt
{verplicht}

## Bij twijfel
Schrijf de zin zo dat je alleen beschrijft wat het programma DOET (een schema,
aflopende sterkte, dagelijkse begeleiding) en nooit wat het GARANDEERT.
"""
