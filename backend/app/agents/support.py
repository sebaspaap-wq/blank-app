"""Support-agent — in Fase 1 alleen de no-show-waarschuwing.

Paragraaf 3.3 zet "no-show-waarschuwingen" expliciet op tier 1: de agent mag
die zelfstandig versturen. Dat deel is hier af. De chatbot, de kennisbank en de
tier 3-escalatie van klachten komen in Fase 2.

Let op hoe de waarschuwing hier terechtkomt: de Matching-agent stuurt geen
bericht aan Support, maar publiceert een ``NoShowGesignaleerd``-event met vaste
velden. Support beslist zelf wat het daarmee doet.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base import BaseAgent
from app.core.domein import Afdeling, Tier
from app.core.events import NoShowGesignaleerd, handelt
from app.core.tiers import Voorstel, registreer_uitvoerder
from app.db.models import AgentEvent, Beslissing


class SupportAgent(BaseAgent):
    afdeling = Afdeling.SUPPORT
    systeemprompt = (
        "Je bent de Support-agent van WOSZ. Je beantwoordt vragen van medewerkers en "
        "bedrijven op basis van de kennisbank en verstuurt standaardberichten. Je doet "
        "nooit toezeggingen over geld, tarieven of contractvoorwaarden — die vragen "
        "escaleer je naar Sebas."
    )

    async def waarschuw_na_no_show(
        self, sessie: AsyncSession, event: NoShowGesignaleerd, bron: AgentEvent | None = None
    ) -> None:
        """Verstuur een standaardwaarschuwing namens Matching (tier 1)."""
        tekst = (
            f"Waarschuwing verstuurd naar {event.medewerker_naam} "
            f"na no-show bij {event.bedrijf_naam}"
        )
        if event.aantal_no_shows > 1:
            tekst += f" ({event.aantal_no_shows}e keer dit seizoen)"

        await self.voer_uit(
            sessie,
            Voorstel(
                afdeling=self.afdeling,
                tier=Tier.ZELFSTANDIG,
                logtekst=tekst,
                actie={
                    "uitvoerder": "support.verstuur_standaardbericht",
                    "params": {
                        "sjabloon": "no_show_waarschuwing",
                        "medewerker_id": event.medewerker_id,
                        "tekst": tekst,
                    },
                },
            ),
        )


@handelt(NoShowGesignaleerd)
async def _op_no_show(
    sessie: AsyncSession, event: NoShowGesignaleerd, bron: AgentEvent
) -> None:
    await SupportAgent().waarschuw_na_no_show(sessie, event, bron)


@registreer_uitvoerder("support.verstuur_standaardbericht")
async def _verstuur_standaardbericht(
    _sessie: AsyncSession, params: dict, _beslissing: Beslissing | None
) -> str:
    """Verstuur een template-bericht.

    In Fase 1 is dit een no-op met logregel: de WhatsApp/e-mail-koppeling komt in
    Fase 2, samen met de rest van de Support-agent. De logregel is wel echt —
    daardoor klopt de audit-trail nu al.
    """
    return str(params.get("tekst", ""))
