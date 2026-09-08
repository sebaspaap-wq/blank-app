"""Het fundament onder het AI-team.

Eén Agent is: een rol, een werkwijze, een setje gereedschap en een model dat
ermee aan de slag gaat. De agents delen dezelfde merkbriefing en dezelfde
reclameregels, zodat alles wat het bedrijf uitstuurt uit één mond lijkt te komen.

Er is bewust geen magie: elke agent doet zijn werk met dezelfde tools die jij
ook met de hand kunt aanroepen (zie quitter/tools/). Wat een agent maakt, komt
als bestand in het project terecht. Niets verdwijnt in een chatvenster.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Sequence

from ..brand import MERK
from ..compliance import instructie_voor_agents
from ..paths import DATA

# Standaardmodel voor het hele team. Het duurste onderdeel van QUITTER is niet
# het model, het is een verkeerde advertentie of een verkeerd antwoord aan een
# klant. Daarom draait alles standaard op het beste model.
MODEL = "claude-opus-5"
MAX_TOKENS = 16000

LOGBESTAND = DATA / "agent-log.jsonl"


@dataclass
class Resultaat:
    agent: str
    opdracht: str
    tekst: str
    gereedschap_gebruikt: list[dict] = field(default_factory=list)
    seconden: float = 0.0
    tokens_in: int = 0
    tokens_uit: int = 0

    @property
    def kosten_dollar(self) -> float:
        """Ruwe kostenschatting op basis van de prijs van claude-opus-5."""
        return self.tokens_in / 1_000_000 * 5.0 + self.tokens_uit / 1_000_000 * 25.0

    def __str__(self) -> str:
        return self.tekst


@dataclass
class Agent:
    """Een medewerker van QUITTER die toevallig geen mens is."""

    naam: str
    rol: str
    opdracht: str
    werkwijze: Sequence[str]
    tools: Sequence[Callable] = ()
    model: str = MODEL
    effort: str = "high"
    merkbriefing: bool = True
    reclameregels: bool = True

    # ------------------------------------------------------------------
    def systeemprompt(self) -> str:
        werkwijze = "\n".join(f"- {r}" for r in self.werkwijze)
        blokken = [
            f"Je bent {self.naam}, {self.rol} bij QUITTER.",
            "",
            "# Waar je voor bent",
            self.opdracht,
            "",
            "# Hoe je werkt",
            werkwijze,
        ]
        if self.merkbriefing:
            blokken += ["", MERK.briefing()]
        if self.reclameregels:
            blokken += ["", instructie_voor_agents()]
        blokken += [
            "",
            "# Algemeen",
            "- Schrijf in het Nederlands, tenzij de opdracht iets anders vraagt.",
            "- Verzin geen cijfers. Aantallen, prijzen, marges en schema's haal je op met je gereedschap.",
            "- Weet je iets niet, zeg dat dan en zeg wat je nodig hebt om het wel te weten.",
            "- Lever af: als je iets maakt dat bewaard moet blijven, sla het op met schrijf_bestand.",
            "- Vat aan het eind in twee of drie zinnen samen wat je gedaan hebt en wat de volgende stap is.",
        ]
        return "\n".join(blokken)

    # ------------------------------------------------------------------
    def voer_uit(self, opdracht: str, *, context: str = "", client=None) -> Resultaat:
        """Laat deze agent één opdracht uitvoeren."""
        import anthropic
        from anthropic import beta_tool

        client = client or anthropic.Anthropic()
        gereedschap = [beta_tool(f) for f in self.tools]
        bericht = opdracht if not context else f"{opdracht}\n\n# Context\n{context}"

        start = time.monotonic()
        runner = client.beta.messages.tool_runner(
            model=self.model,
            max_tokens=MAX_TOKENS,
            system=self.systeemprompt(),
            thinking={"type": "adaptive"},
            output_config={"effort": self.effort},
            tools=gereedschap,
            messages=[{"role": "user", "content": bericht}],
        )

        gebruikt: list[dict] = []
        tokens_in = tokens_uit = 0
        laatste = None
        for antwoord in runner:
            laatste = antwoord
            tokens_in += antwoord.usage.input_tokens
            tokens_uit += antwoord.usage.output_tokens
            for blok in antwoord.content:
                if blok.type == "tool_use":
                    gebruikt.append({"tool": blok.name, "invoer": blok.input})

        tekst = ""
        if laatste is not None:
            tekst = "\n".join(b.text for b in laatste.content if b.type == "text").strip()
            if laatste.stop_reason == "refusal":
                tekst = tekst or "(het model heeft deze opdracht geweigerd)"

        resultaat = Resultaat(
            agent=self.naam,
            opdracht=opdracht,
            tekst=tekst,
            gereedschap_gebruikt=gebruikt,
            seconden=time.monotonic() - start,
            tokens_in=tokens_in,
            tokens_uit=tokens_uit,
        )
        _log(resultaat)
        return resultaat


def _log(resultaat: Resultaat) -> None:
    """Elke actie van elke agent komt in het logboek. Zo blijft het navolgbaar."""
    regel = {
        "moment": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "agent": resultaat.agent,
        "opdracht": resultaat.opdracht[:400],
        "gereedschap": [g["tool"] for g in resultaat.gereedschap_gebruikt],
        "seconden": round(resultaat.seconden, 1),
        "tokens_in": resultaat.tokens_in,
        "tokens_uit": resultaat.tokens_uit,
        "kosten_dollar": round(resultaat.kosten_dollar, 4),
        "antwoord": resultaat.tekst[:2000],
    }
    LOGBESTAND.parent.mkdir(parents=True, exist_ok=True)
    with LOGBESTAND.open("a", encoding="utf-8") as f:
        f.write(json.dumps(regel, ensure_ascii=False) + "\n")
