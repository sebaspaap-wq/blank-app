"""Response-schema's — het contract met wosz-app.html.

Deze schema's zijn niet vrij ontworpen. Ze geven exact de velden terug die de
bestaande renderfuncties in wosz-app.html al gebruiken, zodat de hardcoded
arrays 1-op-1 vervangen kunnen worden door API-calls zonder dat er iets aan de
structuur of styling van de frontend verandert.

Herkomst per veld:

``ActiviteitUit``   -> ``activityLog`` en ``renderLog()`` / ``renderDeptFeeds()``
``BeslissingUit``   -> ``decisions`` en ``decisionCardHtml()``
``DagrapportUit``   -> ``dailyReport`` en ``renderRapport()``
``DashboardUit``    -> de vier tellers in ``renderDirectie()``

Twee details die makkelijk misgaan en daarom expliciet zijn vastgelegd:

1. ``isEuro`` is camelCase, want ``fmtVal(v.waarde, v.isEuro)`` leest dat veld
   letterlijk. Hetzelfde geldt voor ``gekozenOptie`` in ``decisionCardHtml()``.
2. ``afdeling`` mag ``null`` zijn. ``renderLog()`` doet
   ``a.afdeling ? ' · ' + DEPT_LABEL[a.afdeling] : ''`` en ``DEPT_LABEL`` kent
   alleen de vier afdelingen. Een directieregel met afdeling ``"directie"``
   zou daar dus letterlijk "undefined" tonen; daarom sturen we voor die regels
   ``null``, net zoals ``resolveDecision()`` nu een regel zonder afdeling
   toevoegt.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.core.domein import AFDELINGSAGENTS, Afdeling, SocialKanaal, als_aware
from app.db.models import Activiteit, Beslissing


class ActiviteitUit(BaseModel):
    """Eén regel in het activiteitenlog, zoals de frontend hem verwacht."""

    tijd: str
    tekst: str
    afdeling: str | None = None

    # Extra veld: de frontend negeert het, maar het maakt de audit-trail in de
    # API zichtbaar zonder dat de bestaande weergave verandert.
    tier: int | None = None

    @classmethod
    def van_model(cls, activiteit: Activiteit) -> "ActiviteitUit":
        moment = als_aware(activiteit.tijd)
        afdeling = activiteit.afdeling
        zichtbaar = afdeling if afdeling in {str(a) for a in AFDELINGSAGENTS} else None
        return cls(
            tijd=moment.strftime("%H:%M") if moment else "",
            tekst=activiteit.tekst,
            afdeling=zichtbaar,
            tier=activiteit.tier,
        )


class OptieUit(BaseModel):
    """Eén keuzemogelijkheid op een beslissingskaart."""

    naam: str
    gevolg: str


class BeslissingUit(BaseModel):
    """Een beslissing zoals ``decisionCardHtml()`` hem rendert."""

    model_config = ConfigDict(populate_by_name=True)

    id: int
    urgentie: str
    titel: str
    situatie: str
    opties: list[OptieUit]
    aanbeveling: str = ""
    gekozen_optie: str | None = Field(default=None, serialization_alias="gekozenOptie")

    # Extra velden voor de escalatielogica. De bestaande frontend gebruikt ze
    # niet; ze zijn beschikbaar als je de kaart later wilt uitbreiden.
    tier: int
    afdeling_bron: str = Field(serialization_alias="afdelingBron")
    deadline: str | None = None

    @classmethod
    def van_model(cls, beslissing: Beslissing) -> "BeslissingUit":
        deadline = als_aware(beslissing.deadline_at)
        return cls(
            id=beslissing.id,
            urgentie=beslissing.urgentie,
            titel=beslissing.titel,
            situatie=beslissing.situatie,
            opties=[
                OptieUit(naam=o["naam"], gevolg=o["gevolg"]) for o in beslissing.opties
            ],
            aanbeveling=beslissing.aanbeveling or "",
            gekozen_optie=beslissing.gekozen_optie,
            tier=beslissing.tier,
            afdeling_bron=beslissing.afdeling_bron,
            deadline=deadline.isoformat() if deadline else None,
        )


class BeslissingenUit(BaseModel):
    """De twee lijsten die het beslissingenpaneel toont."""

    open: list[BeslissingUit]
    afgehandeld: list[BeslissingUit]


class RapportSectieUit(BaseModel):
    titel: str
    icon: str
    items: list[str]


class VoortgangUit(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    label: str
    waarde: float
    doel: float
    is_euro: bool = Field(default=False, serialization_alias="isEuro")


class DagrapportUit(BaseModel):
    datum: str
    secties: list[RapportSectieUit]
    voortgang: list[VoortgangUit]
    aandacht: list[str]

    @classmethod
    def van_dict(cls, rapport: dict[str, Any]) -> "DagrapportUit":
        return cls(
            datum=rapport["datum"],
            secties=[RapportSectieUit(**s) for s in rapport["secties"]],
            voortgang=[
                VoortgangUit(
                    label=v["label"],
                    waarde=v["waarde"],
                    doel=v["doel"],
                    is_euro=v["isEuro"],
                )
                for v in rapport["voortgang"]
            ],
            aandacht=rapport["aandacht"],
        )


class DashboardUit(BaseModel):
    """De vier tellers boven aan het dashboard."""

    model_config = ConfigDict(populate_by_name=True)

    acties_vandaag: int = Field(serialization_alias="actiesVandaag")
    nieuwe_matches: int = Field(serialization_alias="nieuweMatches")
    aanmeldingen_vandaag: int = Field(serialization_alias="aanmeldingenVandaag")
    open_beslissingen: int = Field(serialization_alias="openBeslissingen")


class KeuzeIn(BaseModel):
    """Body van ``POST /api/directie/beslissingen/{id}/kies``."""

    optie_index: int = Field(ge=0, description="Index van de gekozen optie in 'opties'.")


class UrenIn(BaseModel):
    uren: float = Field(gt=0, le=24)


class UrengeschilIn(BaseModel):
    uren_medewerker: float = Field(gt=0, le=24)
    uren_bedrijf: float = Field(gt=0, le=24)


class VraagIn(BaseModel):
    """Body van ``POST /api/support/vragen``."""

    vraag: str = Field(min_length=1, max_length=2000)
    medewerker_id: int


class OnboardingIn(BaseModel):
    medewerker_id: int


class BerichtUit(BaseModel):
    """Een bericht in de outbox, inclusief de volledige tekst."""

    model_config = ConfigDict(populate_by_name=True)

    id: int
    kanaal: str
    sjabloon: str
    ontvanger: str
    onderwerp: str
    inhoud: str
    status: str

    @classmethod
    def van_model(cls, bericht) -> "BerichtUit":
        return cls(
            id=bericht.id,
            kanaal=bericht.kanaal,
            sjabloon=bericht.sjabloon,
            ontvanger=bericht.ontvanger_naam,
            onderwerp=bericht.onderwerp,
            inhoud=bericht.inhoud,
            status=bericht.status,
        )


class SjabloonUit(BaseModel):
    naam: str
    kanaal: str
    onderwerp: str
    body: str
    variabelen: list[str]


class FactuurUit(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    bedrijf: str
    periode: str
    uren: float
    bedrag_eur: float = Field(serialization_alias="bedragEur")
    status: str


class ContentplanningIn(BaseModel):
    """Body van ``POST /api/marketing/kalender``."""

    hoek_id: int
    geplande_datum: date
    kanaal: SocialKanaal = SocialKanaal.INSTAGRAM
    aanleiding: str = ""


class ContentitemUit(BaseModel):
    """Eén item op de content-kalender."""

    model_config = ConfigDict(populate_by_name=True)

    id: int
    geplande_datum: str = Field(serialization_alias="geplandeDatum")
    kanaal: str
    hoek: str
    haak: str
    concepttekst: str
    aanleiding: str
    status: str
    door_llm: bool = Field(serialization_alias="doorLlm")

    @classmethod
    def van_model(cls, item, hoek_naam: str) -> "ContentitemUit":
        return cls(
            id=item.id,
            geplande_datum=item.geplande_datum.isoformat(),
            kanaal=item.kanaal,
            hoek=hoek_naam,
            haak=item.haak,
            concepttekst=item.concepttekst,
            aanleiding=item.aanleiding,
            status=item.status,
            door_llm=item.door_llm,
        )


class CampagneUit(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    naam: str
    kanaal: str
    status: str
    dagbudget_eur: float = Field(serialization_alias="dagbudgetEur")
    bandbreedte_pct: float = Field(serialization_alias="bandbreedtePct")
    max_verschuiving_eur: float = Field(serialization_alias="maxVerschuivingEur")
    verwachte_kosten_per_aanmelding_eur: float = Field(
        serialization_alias="verwachteKostenPerAanmeldingEur"
    )


class BudgetverschuivingIn(BaseModel):
    van_campagne_id: int
    naar_campagne_id: int
    bedrag_eur: float = Field(gt=0)
    reden: str = Field(min_length=1, max_length=500)


class BudgetverhogingIn(BaseModel):
    campagne_id: int
    extra_eur: float = Field(gt=0)
    reden: str = Field(min_length=1, max_length=500)


class BudgetmutatieUit(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    soort: str
    van_campagne: str | None = Field(default=None, serialization_alias="vanCampagne")
    naar_campagne: str | None = Field(default=None, serialization_alias="naarCampagne")
    bedrag_eur: float = Field(serialization_alias="bedragEur")
    reden: str
    status: str


class NieuweHoekIn(BaseModel):
    naam: str = Field(min_length=1, max_length=120)
    omschrijving: str = Field(min_length=1, max_length=1000)
    reden: str = Field(min_length=1, max_length=500)


class ResultaatIn(BaseModel):
    campagne_id: int
    datum: date
    uitgaven_eur: float = Field(ge=0)
    vertoningen: int = Field(ge=0, default=0)
    klikken: int = Field(ge=0, default=0)
    aanmeldingen: int = Field(ge=0, default=0)


class UitbetalingUit(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    soort: str
    begunstigde: str
    bedrag_eur: float = Field(serialization_alias="bedragEur")
    omschrijving: str
    status: str


# ---------------------------------------------------------------------------
# Medewerkerscherm
#
# De veldnamen hieronder zijn niet gekozen maar overgenomen: ``shiftCardHtml()``
# leest ``s.role``, ``s.datum``, ``s.tijd``, ``s.plek`` en ``s.uurloon``, en
# ``renderMijnShifts()`` leest daarnaast ``s.status`` en ``s.uren``. Vandaar
# ``role`` in het Engels tussen verder Nederlandse velden.
# ---------------------------------------------------------------------------


class ShiftUit(BaseModel):
    """Eén kaart in 'Beschikbare shifts' — ``shiftCardHtml(s, true)``."""

    id: int
    role: str
    datum: str
    tijd: str
    plek: str
    uurloon: str


class MijnShiftUit(BaseModel):
    """Een regel onder 'Mijn shifts' — aankomend of geschiedenis.

    ``match_id`` staat er los in omdat annuleren en uren doorgeven een match
    aanwijzen; de frontend gebruikt nu nog de lijstindex.
    """

    model_config = ConfigDict(populate_by_name=True)

    match_id: int = Field(serialization_alias="matchId")
    role: str
    datum: str
    tijd: str
    plek: str
    status: str
    uurloon: str | None = None
    uren: float | None = None


class MijnShiftsUit(BaseModel):
    aankomend: list[MijnShiftUit]
    geschiedenis: list[MijnShiftUit]


class VriendUit(BaseModel):
    """Een regel in 'Vrienden aangemeld' — ``renderVrienden()``."""

    naam: str
    uren: float
    status: str


class ProfielUit(BaseModel):
    """De velden op 'Mijn profiel'."""

    model_config = ConfigDict(populate_by_name=True)

    naam: str
    email: str | None = None
    telefoon: str | None = None
    woonplaats: str | None = None
    gewenst_uurloon: str | None = Field(default=None, serialization_alias="gewenstUurloon")
    functies: list[str] = Field(default_factory=list)
    beschikbare_dagen: list[str] = Field(
        default_factory=list, serialization_alias="beschikbareDagen"
    )


class ProfielIn(BaseModel):
    """Body van ``POST /api/medewerker/{id}/profiel``."""

    naam: str = Field(min_length=2, max_length=120)
    email: str | None = Field(default=None, max_length=200)
    telefoon: str | None = Field(default=None, max_length=40)
    woonplaats: str | None = Field(default=None, max_length=120)
    gewenst_uurloon: str | None = Field(default=None, max_length=40)
    functies: list[str] = Field(default_factory=list)
    beschikbare_dagen: list[str] = Field(default_factory=list)


class MedewerkerUit(BaseModel):
    """Alles wat het medewerkerscherm in één keer nodig heeft."""

    model_config = ConfigDict(populate_by_name=True)

    id: int
    naam: str
    seizoen_uren: float = Field(serialization_alias="seizoenUren")
    profiel: ProfielUit
    beschikbaar: list[ShiftUit]
    aankomend: list[MijnShiftUit]
    geschiedenis: list[MijnShiftUit]
    vrienden: list[VriendUit]


class AanmeldingIn(BaseModel):
    """Body van ``POST /api/medewerker/aanmelden``."""

    naam: str = Field(min_length=2, max_length=120)
    email: str | None = Field(default=None, max_length=200)
    telefoon: str | None = Field(default=None, max_length=40)
    functies: list[str] = Field(default_factory=list)
    beschikbare_dagen: list[str] = Field(default_factory=list)
    ervaring_jaren: float = Field(default=0.0, ge=0, le=60)
    gewenst_uurloon: str | None = Field(default=None, max_length=40)


class VriendIn(BaseModel):
    """Body van ``POST /api/medewerker/{id}/vrienden`` — ``submitInvite()``."""

    naam: str = Field(min_length=2, max_length=120)
    email: str | None = Field(default=None, max_length=200)


# ---------------------------------------------------------------------------
# Horecascherm
# ---------------------------------------------------------------------------


class KandidaatUit(BaseModel):
    """Een kandidaat onder een aanvraag — ``aanvraagCardHtml()``."""

    model_config = ConfigDict(populate_by_name=True)

    medewerker_id: int = Field(serialization_alias="medewerkerId")
    naam: str
    info: str
    wens: str


class AanvraagUit(BaseModel):
    """Eén personeelsvraag zoals het horecascherm hem toont."""

    id: int
    functie: str
    datum: str
    tijd: str
    gevraagd: int
    gematcht: int
    uurloon: str
    kandidaten: list[KandidaatUit]


class HorecaStatsUit(BaseModel):
    """De vier tellers bovenaan het horecascherm.

    De matchtijd staat in minuten, niet in uren. De agent matcht meestal binnen
    een minuut; in uren afgerond zou daar altijd "0u" staan, wat leest als
    "geen gegevens" terwijl het juist het beste denkbare cijfer is.
    """

    model_config = ConfigDict(populate_by_name=True)

    actieve_aanvragen: int = Field(serialization_alias="actieveAanvragen")
    gematcht_deze_week: int = Field(serialization_alias="gematchtDezeWeek")
    uren_deze_maand: int = Field(serialization_alias="urenDezeMaand")
    gemiddelde_matchtijd_minuten: int | None = Field(
        serialization_alias="gemiddeldeMatchtijdMinuten"
    )


class BedrijfsprofielUit(BaseModel):
    """De velden op 'Bedrijfsprofiel'."""

    model_config = ConfigDict(populate_by_name=True)

    naam: str
    plaats: str | None = None
    contactpersoon: str | None = None
    email: str | None = None
    #: Wat WOSZ per gewerkt uur rekent. Alleen ter informatie: het tarief
    #: wijzigen is geen actie die een bedrijf zelf uitvoert.
    tarief_per_uur: float = Field(serialization_alias="tariefPerUur")


class BedrijfsprofielIn(BaseModel):
    """Body van ``POST /api/horeca/{id}/profiel``.

    ``tarief_per_uur`` staat er bewust niet in: dat is een afspraak tussen WOSZ
    en het bedrijf, geen veld dat het bedrijf zelf kan wijzigen.
    """

    naam: str = Field(min_length=2, max_length=120)
    plaats: str | None = Field(default=None, max_length=120)
    contactpersoon: str | None = Field(default=None, max_length=120)
    email: str | None = Field(default=None, max_length=200)


class HorecamedewerkerUit(BaseModel):
    """Een regel in de medewerkerstabel van het horecascherm."""

    model_config = ConfigDict(populate_by_name=True)

    naam: str
    functie: str
    uren_totaal: float = Field(serialization_alias="urenTotaal")
    laatste_shift: str = Field(serialization_alias="laatsteShift")
    contact: str


class HorecafactuurUit(BaseModel):
    """Een regel in de facturentabel van het horecascherm."""

    model_config = ConfigDict(populate_by_name=True)

    id: int
    periode: str
    uren: float
    tarief_per_uur_eur: float = Field(serialization_alias="tariefPerUurEur")
    bedrag_eur: float = Field(serialization_alias="bedragEur")
    status: str


class HorecaUit(BaseModel):
    """Alles wat het horecascherm in één keer nodig heeft."""

    model_config = ConfigDict(populate_by_name=True)

    bedrijf_id: int = Field(serialization_alias="bedrijfId")
    bedrijf: str
    profiel: BedrijfsprofielUit
    stats: HorecaStatsUit
    aanvragen: list[AanvraagUit]
    medewerkers: list[HorecamedewerkerUit]
    facturen: list[HorecafactuurUit]


class AanvraagIn(BaseModel):
    """Body van ``POST /api/horeca/{bedrijf_id}/aanvragen`` — ``submitRequest()``.

    ``datum`` en ``tijd`` komen als vrije tekst uit de invulvelden. De datum
    wordt hier omgezet naar een echte datum; lukt dat niet, dan is dat een
    invoerfout en geen shift die stilletjes op vandaag belandt.
    """

    functie: str = Field(min_length=2, max_length=60)
    datum: str = Field(min_length=1, max_length=40)
    tijd: str = Field(min_length=1, max_length=40)
    aantal: int = Field(default=1, ge=1, le=50)
    uurloon: str | None = Field(default=None, max_length=40)


def afdeling_of_none(waarde: str) -> str | None:
    """Geef ``None`` terug voor afdelingen die de frontend niet kent."""
    return waarde if waarde in {str(a) for a in AFDELINGSAGENTS} else None


__all__ = [
    "AanmeldingIn",
    "AanvraagIn",
    "AanvraagUit",
    "ActiviteitUit",
    "BedrijfsprofielIn",
    "BedrijfsprofielUit",
    "BerichtUit",
    "BeslissingUit",
    "BudgetmutatieUit",
    "BudgetverhogingIn",
    "BudgetverschuivingIn",
    "CampagneUit",
    "ContentitemUit",
    "ContentplanningIn",
    "BeslissingenUit",
    "DagrapportUit",
    "DashboardUit",
    "FactuurUit",
    "HorecaStatsUit",
    "HorecaUit",
    "HorecafactuurUit",
    "HorecamedewerkerUit",
    "KandidaatUit",
    "KeuzeIn",
    "MedewerkerUit",
    "MijnShiftUit",
    "MijnShiftsUit",
    "NieuweHoekIn",
    "OnboardingIn",
    "OptieUit",
    "ProfielIn",
    "ProfielUit",
    "ResultaatIn",
    "ShiftUit",
    "SjabloonUit",
    "UitbetalingUit",
    "UrenIn",
    "UrengeschilIn",
    "VoortgangUit",
    "VraagIn",
    "VriendIn",
    "VriendUit",
    "afdeling_of_none",
    "Afdeling",
]
