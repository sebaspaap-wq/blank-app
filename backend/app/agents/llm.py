"""Koppeling met de Anthropic API voor agent-beslissingen.

De agents gebruiken Claude alleen waar een regel tekortschiet — bijvoorbeeld
wanneer meerdere kandidaten even geschikt lijken. Het model kiest dan via
function calling, zodat het antwoord gestructureerd terugkomt en niet als
vrije tekst geïnterpreteerd hoeft te worden.

Zonder ``ANTHROPIC_API_KEY`` valt het systeem terug op de deterministische
regels van de agent zelf. Dat is geen noodgreep: het houdt de backend
testbaar zonder netwerk en zorgt dat een storing bij de API het matchen niet
stillegt.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from app.config import get_agent_settings

logger = logging.getLogger(__name__)

#: Maximaal aantal tokens per beslissing. Ruim genoeg voor het redeneerwerk
#: plus de tool-call, en klein genoeg om de kosten voorspelbaar te houden.
MAX_TOKENS = 8000


class LLMNietBeschikbaar(RuntimeError):
    """Er is geen API-key geconfigureerd."""


def llm_beschikbaar() -> bool:
    return get_agent_settings().llm_beschikbaar


async def vraag_gestructureerd_besluit(
    *,
    systeemprompt: str,
    situatie: str,
    tool_naam: str,
    tool_beschrijving: str,
    schema: dict[str, Any],
) -> dict[str, Any] | None:
    """Laat Claude één gestructureerd besluit nemen via function calling.

    Geeft de tool-input terug als dict, of ``None`` als er geen key is of de
    aanroep mislukt. De aanroeper hoort in beide gevallen op zijn eigen regels
    terug te vallen — een agent mag nooit blokkeren op de API.
    """
    instellingen = get_agent_settings()
    if not instellingen.llm_beschikbaar:
        return None

    try:
        from anthropic import AsyncAnthropic
    except ImportError:  # pragma: no cover - alleen als de dependency ontbreekt
        logger.warning("anthropic-package niet geïnstalleerd; agent gebruikt regelmodus")
        return None

    client = AsyncAnthropic(api_key=instellingen.anthropic_api_key)
    tool = {
        "name": tool_naam,
        "description": tool_beschrijving,
        "input_schema": schema,
    }

    try:
        antwoord = await client.messages.create(
            model=instellingen.anthropic_model,
            max_tokens=MAX_TOKENS,
            output_config={"effort": instellingen.anthropic_effort},
            system=systeemprompt,
            tools=[tool],
            tool_choice={"type": "tool", "name": tool_naam},
            messages=[{"role": "user", "content": situatie}],
        )
    except asyncio.CancelledError:
        raise
    except Exception as fout:  # noqa: BLE001 — nooit blokkeren op de API
        logger.warning("Anthropic-aanroep mislukt (%s); agent valt terug op regels", fout)
        return None

    if antwoord.stop_reason == "refusal":
        logger.warning("Anthropic weigerde de aanvraag; agent valt terug op regels")
        return None

    for blok in antwoord.content:
        if getattr(blok, "type", None) == "tool_use" and blok.name == tool_naam:
            return dict(blok.input)

    logger.warning("Geen tool-call in het antwoord; agent valt terug op regels")
    return None
