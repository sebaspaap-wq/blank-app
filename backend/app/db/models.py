"""ORM-model.

Basis is het datamodel uit hoofdstuk 4 van de bouwopdracht. Uitbreidingen zijn
per tabel toegelicht — ze zijn nodig om de escalatielogica, de event-bus en de
handmatige uitbetaling architecturaal te kunnen afdwingen.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.core.domein import (
    Afdeling,
    BerichtStatus,
    BeslissingStatus,
    BudgetmutatieStatus,
    CampagneStatus,
    ContentStatus,
    EventStatus,
    MatchStatus,
    ShiftStatus,
    SocialKanaal,
    Tier,
    UitbetalingStatus,
    Urgentie,
    nu,
)


class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# Kernentiteiten (hoofdstuk 4)
# ---------------------------------------------------------------------------


class User(Base):
    """users (id, naam, rol, contactgegevens) + velden voor matching."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    naam: Mapped[str] = mapped_column(String(120), nullable=False)
    rol: Mapped[str] = mapped_column(String(20), nullable=False)  # medewerker/horeca/directie
    email: Mapped[str | None] = mapped_column(String(200))
    telefoon: Mapped[str | None] = mapped_column(String(40))

    # Uitbreiding: nodig om regelgebaseerd te kunnen matchen.
    functies: Mapped[list[str]] = mapped_column(JSON, default=list)
    beschikbare_dagen: Mapped[list[str]] = mapped_column(JSON, default=list)
    actief: Mapped[bool] = mapped_column(Boolean, default=True)
    geschorst: Mapped[bool] = mapped_column(Boolean, default=False)

    aangemaakt_op: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=nu)

    level: Mapped["Level | None"] = relationship(
        back_populates="medewerker", uselist=False, cascade="all, delete-orphan"
    )


class Bedrijf(Base):
    """Uitbreiding: strandtenten/horecazaken als eigen entiteit.

    Hoofdstuk 4 hangt ``shifts.bedrijf_id`` op aan ``users``. Een bedrijf heeft
    echter eigen gegevens (locatie, tarief, facturatie) die niet in een
    persoonsrecord thuishoren, ook met het oog op AVG-dataminimalisatie.
    """

    __tablename__ = "bedrijven"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    naam: Mapped[str] = mapped_column(String(120), nullable=False)
    plaats: Mapped[str | None] = mapped_column(String(120))
    contact_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    tarief_per_uur: Mapped[float] = mapped_column(Float, default=2.0)  # WOSZ-marge
    actief: Mapped[bool] = mapped_column(Boolean, default=True)


class Shift(Base):
    """shifts (id, bedrijf_id, datum, tijd, functie, aantal_gevraagd, status)."""

    __tablename__ = "shifts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bedrijf_id: Mapped[int] = mapped_column(ForeignKey("bedrijven.id"), nullable=False)
    datum: Mapped[date] = mapped_column(Date, nullable=False)
    tijd: Mapped[str] = mapped_column(String(40), nullable=False)  # bijv. "17:00-01:00"
    functie: Mapped[str] = mapped_column(String(60), nullable=False)
    aantal_gevraagd: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(20), default=ShiftStatus.OPEN)

    # Uitbreiding: uurloonindicatie zoals de frontend die toont.
    uurloon: Mapped[str | None] = mapped_column(String(40))
    duur_uren: Mapped[float] = mapped_column(Float, default=6.0)

    bedrijf: Mapped[Bedrijf] = relationship()
    matches: Mapped[list["Match"]] = relationship(back_populates="shift")


class Match(Base):
    """matches (id, shift_id, medewerker_id, status, uren_gewerkt)."""

    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    shift_id: Mapped[int] = mapped_column(ForeignKey("shifts.id"), nullable=False)
    medewerker_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=MatchStatus.VOORGESTELD)
    uren_gewerkt: Mapped[float | None] = mapped_column(Float)

    # Uitbreiding: de onderbouwing van de agent, zodat elke match herleidbaar is.
    onderbouwing: Mapped[str | None] = mapped_column(Text)
    door_llm: Mapped[bool] = mapped_column(Boolean, default=False)
    aangemaakt_op: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=nu)

    shift: Mapped[Shift] = relationship(back_populates="matches")
    medewerker: Mapped[User] = relationship()


class Level(Base):
    """levels (medewerker_id, huidig_level, seizoen_uren)."""

    __tablename__ = "levels"

    medewerker_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    huidig_level: Mapped[int] = mapped_column(Integer, default=1)
    seizoen_uren: Mapped[float] = mapped_column(Float, default=0.0)

    medewerker: Mapped[User] = relationship(back_populates="level")


class Referral(Base):
    """referrals (id, medewerker_id, vriend_id, uren_vriend, bonus_status)."""

    __tablename__ = "referrals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    medewerker_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    vriend_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    uren_vriend: Mapped[float] = mapped_column(Float, default=0.0)
    bonus_status: Mapped[str] = mapped_column(String(30), default="bezig")
    bonus_bedrag_cent: Mapped[int] = mapped_column(Integer, default=2000)


class Factuur(Base):
    """facturen (id, bedrijf_id, periode, uren, bedrag, status)."""

    __tablename__ = "facturen"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bedrijf_id: Mapped[int] = mapped_column(ForeignKey("bedrijven.id"), nullable=False)
    periode: Mapped[str] = mapped_column(String(40), nullable=False)
    uren: Mapped[float] = mapped_column(Float, default=0.0)
    bedrag_cent: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(30), default="concept")
    aangemaakt_op: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=nu)


class Beslissing(Base):
    """beslissingen (+ tier en deadline voor de escalatielogica).

    De velden ``titel``, ``situatie``, ``opties``, ``urgentie``, ``status``,
    ``gekozen_optie`` en ``afdeling_bron`` komen uit hoofdstuk 4. Toegevoegd:

    ``tier``        bepaalt of de beslissing zelfstandig, met deadline, of
                    blokkerend is (hoofdstuk 3).
    ``deadline_at`` alleen gevuld bij tier 2: het moment waarop de agent alsnog
                    uitvoert als Sebas niet heeft ingegrepen.
    ``actie``       gestructureerde beschrijving van wat er moet gebeuren als
                    een optie gekozen wordt. Dit is bewust data en geen vrije
                    tekst, zodat uitvoeren niet van een LLM-interpretatie afhangt.
    """

    __tablename__ = "beslissingen"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    titel: Mapped[str] = mapped_column(String(200), nullable=False)
    situatie: Mapped[str] = mapped_column(Text, nullable=False)
    opties: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    urgentie: Mapped[str] = mapped_column(String(20), default=Urgentie.DEZE_WEEK)
    status: Mapped[str] = mapped_column(String(30), default=BeslissingStatus.OPEN)
    gekozen_optie: Mapped[str | None] = mapped_column(String(120))
    afdeling_bron: Mapped[str] = mapped_column(String(20), nullable=False)

    aanbeveling: Mapped[str | None] = mapped_column(Text)
    tier: Mapped[int] = mapped_column(Integer, default=Tier.WACHT)
    deadline_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    actie: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    aangemaakt_op: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=nu)
    afgehandeld_op: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Activiteit(Base):
    """activiteitenlog (id, tijd, tekst, afdeling) + tier.

    Dit is de audit-trail uit randvoorwaarde 6.4. Elke agentactie schrijft hier
    een regel weg; dat gebeurt in het uitvoerpad van ``BaseAgent``, niet als
    losse aanroep die vergeten kan worden.
    """

    __tablename__ = "activiteitenlog"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tijd: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=nu, index=True)
    tekst: Mapped[str] = mapped_column(Text, nullable=False)
    afdeling: Mapped[str] = mapped_column(String(20), nullable=False)
    tier: Mapped[int | None] = mapped_column(Integer)

    # Uitbreiding: koppeling naar de beslissing of het event dat de actie veroorzaakte.
    beslissing_id: Mapped[int | None] = mapped_column(ForeignKey("beslissingen.id"))
    event_id: Mapped[int | None] = mapped_column(ForeignKey("agent_events.id"))


class AgentEvent(Base):
    """Message queue tussen agents (hoofdstuk 2: Postgres-tabel met polling).

    Agents praten uitsluitend via deze tabel met elkaar, en uitsluitend met een
    gevalideerde payload — nooit met vrije tekst.
    """

    __tablename__ = "agent_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    bron_afdeling: Mapped[str] = mapped_column(String(20), nullable=False)
    doel_afdeling: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(20), default=EventStatus.PENDING, index=True)
    pogingen: Mapped[int] = mapped_column(Integer, default=0)
    laatste_fout: Mapped[str | None] = mapped_column(Text)

    aangemaakt_op: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=nu)
    verwerkt_op: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Uitbetalingsopdracht(Base):
    """Een door Sebas goedgekeurde uitbetaling die hij zelf uitvoert.

    Dit record is geen betaalopdracht aan een bank — die koppeling bestaat niet
    in dit systeem. Het is een werkinstructie voor Sebas plus de audit-trail
    eromheen. Zie app/payouts/README.md.
    """

    __tablename__ = "uitbetalingsopdrachten"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    soort: Mapped[str] = mapped_column(String(40), nullable=False)  # bonus/factuur/correctie
    begunstigde_naam: Mapped[str] = mapped_column(String(120), nullable=False)
    begunstigde_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    bedrag_cent: Mapped[int] = mapped_column(Integer, nullable=False)
    omschrijving: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(30), default=UitbetalingStatus.CONCEPT)

    beslissing_id: Mapped[int | None] = mapped_column(ForeignKey("beslissingen.id"))
    goedgekeurd_op: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    geexporteerd_op: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    handmatig_voldaan_op: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    aangemaakt_op: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=nu)


class Kennisbankitem(Base):
    """Een door Sebas beoordeeld vraag-antwoordpaar.

    Dit is de enige bron van inhoudelijke antwoorden die Support mag versturen.
    De agent kiest welk item van toepassing is; hij schrijft het antwoord niet
    zelf. Zo kan er nooit een toezegging naar buiten die geen mens heeft gezien.
    """

    __tablename__ = "kennisbank"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vraag: Mapped[str] = mapped_column(Text, nullable=False)
    antwoord: Mapped[str] = mapped_column(Text, nullable=False)
    trefwoorden: Mapped[list[str]] = mapped_column(JSON, default=list)
    categorie: Mapped[str] = mapped_column(String(40), default="algemeen")
    actief: Mapped[bool] = mapped_column(Boolean, default=True)

    # Onderwerpen waar Support nooit zelfstandig op antwoordt, ook al staat er
    # een goedgekeurd antwoord: geld, tarieven, contractvoorwaarden. De agent
    # escaleert dan naar Sebas en vermeldt welk antwoord hij zou hebben gebruikt.
    # Zo houdt Sebas de knop in handen zonder dat er code aangepast hoeft te worden.
    vereist_mens: Mapped[bool] = mapped_column(Boolean, default=False)

    aangemaakt_op: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=nu)


class Bericht(Base):
    """Uitgaand bericht in de outbox.

    ``inhoud`` is altijd het resultaat van een gerenderd sjabloon; er is geen
    pad waarlangs een agent hier vrije tekst in krijgt. Zie app/agents/sjablonen.py.
    """

    __tablename__ = "berichten"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    kanaal: Mapped[str] = mapped_column(String(20), nullable=False)
    sjabloon: Mapped[str] = mapped_column(String(60), nullable=False)
    ontvanger_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    ontvanger_naam: Mapped[str] = mapped_column(String(120), default="")
    onderwerp: Mapped[str] = mapped_column(String(200), default="")
    inhoud: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=BerichtStatus.KLAAR)

    aangemaakt_op: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=nu)
    verstuurd_op: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Supportvraag(Base):
    """Een binnengekomen vraag en hoe Support hem heeft afgehandeld."""

    __tablename__ = "supportvragen"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vraag: Mapped[str] = mapped_column(Text, nullable=False)
    steller_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    uitkomst: Mapped[str] = mapped_column(String(20), nullable=False)
    kennisbankitem_id: Mapped[int | None] = mapped_column(ForeignKey("kennisbank.id"))
    bericht_id: Mapped[int | None] = mapped_column(ForeignKey("berichten.id"))
    beslissing_id: Mapped[int | None] = mapped_column(ForeignKey("beslissingen.id"))
    door_llm: Mapped[bool] = mapped_column(Boolean, default=False)

    aangemaakt_op: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=nu)


class Hoek(Base):
    """Een door Sebas goedgekeurde invalshoek binnen de huisstijl.

    Paragraaf 3.1 geeft de Marketing-agent tier 1 voor "contentplanning binnen
    bestaande huisstijl". Deze tabel is die huisstijl: de agent mag zelfstandig
    content plannen op een hoek die hier staat. Een nieuwe hoek bedenken is
    een nieuwe campagne-richting en dus tier 3.
    """

    __tablename__ = "huisstijl_hoeken"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    naam: Mapped[str] = mapped_column(String(120), nullable=False)
    omschrijving: Mapped[str] = mapped_column(Text, default="")
    toon: Mapped[str] = mapped_column(Text, default="")
    voorbeelden: Mapped[list[str]] = mapped_column(JSON, default=list)
    goedgekeurd: Mapped[bool] = mapped_column(Boolean, default=True)

    aangemaakt_op: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=nu)


class Campagne(Base):
    """Een lopende advertentiecampagne.

    ``dagbudget_cent`` is wat er volgens WOSZ' eigen administratie per dag naar
    deze campagne gaat. Het systeem zet dat niet in Meta Ads Manager — daar is
    geen koppeling voor. Zie ``Budgetmutatie``.
    """

    __tablename__ = "campagnes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    naam: Mapped[str] = mapped_column(String(120), nullable=False)
    hoek_id: Mapped[int | None] = mapped_column(ForeignKey("huisstijl_hoeken.id"))
    kanaal: Mapped[str] = mapped_column(String(20), default=SocialKanaal.INSTAGRAM)
    dagbudget_cent: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default=CampagneStatus.ACTIEF)

    #: Maximaal percentage van het eigen dagbudget dat per dag verschoven mag
    #: worden zonder goedkeuring (paragraaf 3.1: bijv. 20%).
    bandbreedte_pct: Mapped[float] = mapped_column(Float, default=20.0)

    #: Waar we op mikken, om afwijkingen te kunnen signaleren.
    verwachte_kosten_per_aanmelding_cent: Mapped[int] = mapped_column(Integer, default=0)

    aangemaakt_op: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=nu)


class CampagneResultaat(Base):
    """Dagcijfers per campagne, handmatig of via een import ingevoerd."""

    __tablename__ = "campagne_resultaten"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    campagne_id: Mapped[int] = mapped_column(ForeignKey("campagnes.id"), nullable=False)
    datum: Mapped[date] = mapped_column(Date, nullable=False)
    uitgaven_cent: Mapped[int] = mapped_column(Integer, default=0)
    vertoningen: Mapped[int] = mapped_column(Integer, default=0)
    klikken: Mapped[int] = mapped_column(Integer, default=0)
    aanmeldingen: Mapped[int] = mapped_column(Integer, default=0)

    @property
    def kosten_per_aanmelding_cent(self) -> int | None:
        if not self.aanmeldingen:
            return None
        return round(self.uitgaven_cent / self.aanmeldingen)


class Contentitem(Base):
    """Eén item op de content-kalender.

    De agent plant items; publiceren doet hij niet en kan hij niet. Er is geen
    koppeling met een social-platform. ``GEPUBLICEERD`` wordt achteraf door
    Sebas gezet.
    """

    __tablename__ = "contentitems"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    geplande_datum: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    kanaal: Mapped[str] = mapped_column(String(20), default=SocialKanaal.INSTAGRAM)
    hoek_id: Mapped[int] = mapped_column(ForeignKey("huisstijl_hoeken.id"), nullable=False)
    campagne_id: Mapped[int | None] = mapped_column(ForeignKey("campagnes.id"))

    haak: Mapped[str] = mapped_column(String(200), nullable=False)
    concepttekst: Mapped[str] = mapped_column(Text, default="")
    aanleiding: Mapped[str] = mapped_column(String(200), default="")
    status: Mapped[str] = mapped_column(String(20), default=ContentStatus.GEPLAND)
    door_llm: Mapped[bool] = mapped_column(Boolean, default=False)

    aangemaakt_op: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=nu)
    gepubliceerd_op: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Budgetmutatie(Base):
    """Een voorgestelde budgetwijziging die Sebas zelf doorvoert.

    Dit is het marketing-equivalent van ``Uitbetalingsopdracht``: een
    werkinstructie, geen API-aanroep. Het systeem heeft geen toegang tot Meta
    Ads Manager.
    """

    __tablename__ = "budgetmutaties"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    van_campagne_id: Mapped[int | None] = mapped_column(ForeignKey("campagnes.id"))
    naar_campagne_id: Mapped[int | None] = mapped_column(ForeignKey("campagnes.id"))
    bedrag_cent: Mapped[int] = mapped_column(Integer, nullable=False)
    reden: Mapped[str] = mapped_column(Text, default="")
    soort: Mapped[str] = mapped_column(String(30), default="verschuiving")
    status: Mapped[str] = mapped_column(
        String(30), default=BudgetmutatieStatus.KLAAR_VOOR_UITVOERING
    )

    beslissing_id: Mapped[int | None] = mapped_column(ForeignKey("beslissingen.id"))
    aangemaakt_op: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=nu)
    doorgevoerd_op: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Doelstelling(Base):
    """Voedt het ``voortgang``-blok van het dagrapport in de frontend."""

    __tablename__ = "doelstellingen"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    label: Mapped[str] = mapped_column(String(120), nullable=False)
    waarde: Mapped[float] = mapped_column(Float, default=0.0)
    doel: Mapped[float] = mapped_column(Float, default=0.0)
    is_euro: Mapped[bool] = mapped_column(Boolean, default=False)
    volgorde: Mapped[int] = mapped_column(Integer, default=0)


__all__ = [
    "Base",
    "User",
    "Bedrijf",
    "Shift",
    "Match",
    "Level",
    "Referral",
    "Factuur",
    "Beslissing",
    "Activiteit",
    "AgentEvent",
    "Uitbetalingsopdracht",
    "Kennisbankitem",
    "Bericht",
    "Supportvraag",
    "Hoek",
    "Campagne",
    "CampagneResultaat",
    "Contentitem",
    "Budgetmutatie",
    "Doelstelling",
]
