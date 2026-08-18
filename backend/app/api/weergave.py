"""Weergavehelpers voor de app-schermen.

De medewerker- en horecaschermen tonen datums als "Za 16 aug" en uurlonen als
"€13,00 – €14,50". Dat zijn presentatievormen, geen opslagvormen: in de database
staat een echte datum en een tekstveld. Deze module doet de vertaling, op één
plek, zodat alle endpoints hetzelfde tonen.
"""

from __future__ import annotations

import re
from datetime import date

DAG_KORT = ("Ma", "Di", "Wo", "Do", "Vr", "Za", "Zo")
MAAND_KORT = (
    "jan",
    "feb",
    "mrt",
    "apr",
    "mei",
    "jun",
    "jul",
    "aug",
    "sep",
    "okt",
    "nov",
    "dec",
)


def korte_datum(dag: date) -> str:
    """Bijvoorbeeld 'Za 16 aug' — zoals de shiftkaarten het tonen."""
    return f"{DAG_KORT[dag.weekday()]} {dag.day} {MAAND_KORT[dag.month - 1]}"


class DatumFout(ValueError):
    """De ingevoerde datum is niet te lezen."""


#: "Za 23 aug", "23 aug", "23 augustus" — met of zonder jaartal.
_TEKST_DATUM = re.compile(
    r"^(?:[a-z]{2,10}\.?\s+)?(\d{1,2})\s+([a-z]{3,9})\.?(?:\s+(\d{4}))?$"
)
#: "23-08-2026", "23/8", "23-8-26"
_CIJFER_DATUM = re.compile(r"^(\d{1,2})[-/](\d{1,2})(?:[-/](\d{2,4}))?$")

MAAND_NAMEN = (
    "januari",
    "februari",
    "maart",
    "april",
    "mei",
    "juni",
    "juli",
    "augustus",
    "september",
    "oktober",
    "november",
    "december",
)


def _jaar_erbij(maand: int, dag: int, *, vandaag: date) -> date:
    """Vul het jaartal aan als de invoer er geen had.

    Een shift die je vandaag plaatst ligt in de toekomst. Staat de datum dit
    jaar al achter ons, dan bedoelt de invoerder volgend jaar — anders zou een
    aanvraag in december voor 3 januari stilletjes elf maanden in het verleden
    landen en nooit gematcht worden.
    """
    try:
        gekozen = date(vandaag.year, maand, dag)
    except ValueError as fout:  # 31 februari en dergelijke
        raise DatumFout(f"{dag}-{maand} bestaat niet") from fout
    if gekozen < vandaag:
        try:
            gekozen = date(vandaag.year + 1, maand, dag)
        except ValueError as fout:  # 29 februari in een niet-schrikkeljaar
            raise DatumFout(f"{dag}-{maand} bestaat niet in het volgende jaar") from fout
    return gekozen


def lees_datum(tekst: str, *, vandaag: date | None = None) -> date:
    """Lees de datum die iemand in het aanvraagformulier heeft getypt.

    Het veld is vrije tekst met als voorbeeld "bv. Za 23 aug", dus we accepteren
    zowel dat als een gewone datumnotatie. Wat we niet doen is terugvallen op
    vandaag: een onleesbare datum is een invoerfout, en die hoort de invoerder
    te zien in plaats van als verkeerd geplande shift in het systeem te belanden.
    """
    vandaag = vandaag or date.today()
    schoon = tekst.strip().lower().replace("–", "-").replace("—", "-")
    if not schoon:
        raise DatumFout("Geen datum ingevuld")

    # ISO eerst — dat is wat een datumveld in de browser oplevert.
    try:
        return date.fromisoformat(schoon)
    except ValueError:
        pass

    treffer = _TEKST_DATUM.match(schoon)
    if treffer:
        dag, maandtekst, jaar = treffer.groups()
        maand = _maandnummer(maandtekst)
        if maand is None:
            raise DatumFout(f"Onbekende maand: {maandtekst}")
        if jaar:
            try:
                return date(int(jaar), maand, int(dag))
            except ValueError as fout:
                raise DatumFout(str(fout)) from fout
        return _jaar_erbij(maand, int(dag), vandaag=vandaag)

    treffer = _CIJFER_DATUM.match(schoon)
    if treffer:
        dag, maand, jaar = treffer.groups()
        if jaar:
            jaartal = int(jaar)
            if jaartal < 100:
                jaartal += 2000
            try:
                return date(jaartal, int(maand), int(dag))
            except ValueError as fout:
                raise DatumFout(str(fout)) from fout
        return _jaar_erbij(int(maand), int(dag), vandaag=vandaag)

    raise DatumFout(
        f"'{tekst}' is geen datum die ik kan lezen. Probeer bijvoorbeeld "
        f"'{korte_datum(vandaag)}' of '{vandaag.isoformat()}'."
    )


def _maandnummer(tekst: str) -> int | None:
    for index, kort in enumerate(MAAND_KORT, start=1):
        if tekst.startswith(kort):
            return index
    for index, lang in enumerate(MAAND_NAMEN, start=1):
        if lang.startswith(tekst):
            return index
    return None


def periode_tekst(periode: str) -> str:
    """Zet "2026-08" om in "augustus 2026".

    Facturen worden per maand opgebouwd en de periode staat als sorteerbare
    tekst in de database. Voor een factuuroverzicht is dat onleesbaar.
    """
    delen = periode.split("-")
    if len(delen) == 2 and delen[0].isdigit() and delen[1].isdigit():
        maand = int(delen[1])
        if 1 <= maand <= 12:
            return f"{MAAND_NAMEN[maand - 1]} {delen[0]}"
    return periode


def uurloon_tekst(waarde: str | None) -> str:
    """Wat er onder een shift staat als het uurloon niet is ingevuld."""
    return waarde or "Nog niet opgegeven"


def kandidaat_info(
    *, ervaring_jaren: float, functies: list[str], level_naam: str
) -> str:
    """De regel onder de naam van een kandidaat.

    Bijvoorbeeld: "2 jaar ervaring · Bediening, Bar". Zonder opgegeven ervaring
    valt hij terug op het level, want dat zegt binnen WOSZ net zoveel.
    """
    delen: list[str] = []
    if ervaring_jaren >= 1:
        jaren = int(ervaring_jaren)
        delen.append(f"{jaren} jaar ervaring")
    else:
        delen.append(level_naam)

    if functies:
        delen.append(", ".join(f.capitalize() for f in functies))
    return " · ".join(delen)
