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

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.core.domein import AFDELINGSAGENTS, Afdeling, als_aware
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


class UitbetalingUit(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    soort: str
    begunstigde: str
    bedrag_eur: float = Field(serialization_alias="bedragEur")
    omschrijving: str
    status: str


def afdeling_of_none(waarde: str) -> str | None:
    """Geef ``None`` terug voor afdelingen die de frontend niet kent."""
    return waarde if waarde in {str(a) for a in AFDELINGSAGENTS} else None


__all__ = [
    "ActiviteitUit",
    "BeslissingUit",
    "BeslissingenUit",
    "DagrapportUit",
    "DashboardUit",
    "KeuzeIn",
    "OptieUit",
    "UitbetalingUit",
    "UrenIn",
    "UrengeschilIn",
    "VoortgangUit",
    "afdeling_of_none",
    "Afdeling",
]
