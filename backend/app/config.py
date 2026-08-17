"""Configuratie uit environment variables.

Belangrijk architectuurpunt: er zijn twee gescheiden settings-objecten.

``AgentSettings`` is wat de agents krijgen. Dat object bevat structureel geen
enkel veld dat met uitbetalen te maken heeft — niet omdat een agent zich moet
inhouden, maar omdat de velden er simpelweg niet in zitten. ``Settings`` is de
volledige applicatieconfiguratie en wordt alleen door de API-laag gebruikt.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class AgentSettings(BaseSettings):
    """Configuratie die agents mogen zien.

    Bevat bewust GEEN betaal-, bank- of exportinstellingen. Een agent die om
    betaalcredentials vraagt, krijgt niets — er is niets om te geven.
    """

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE, env_file_encoding="utf-8", extra="ignore"
    )

    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    anthropic_model: str = Field(default="claude-opus-5", alias="WOSZ_ANTHROPIC_MODEL")
    anthropic_effort: str = Field(default="medium", alias="WOSZ_ANTHROPIC_EFFORT")

    tier2_deadline_uren: int = Field(default=24, alias="WOSZ_TIER2_DEADLINE_UREN")

    @property
    def llm_beschikbaar(self) -> bool:
        """True als er een API-key is; anders draaien agents in regelmodus."""
        return bool(self.anthropic_api_key.strip())


class Settings(BaseSettings):
    """Volledige applicatieconfiguratie (API-laag, database, scheduler)."""

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE, env_file_encoding="utf-8", extra="ignore"
    )

    database_url: str = Field(
        default="sqlite+aiosqlite:///./wosz.db", alias="WOSZ_DATABASE_URL"
    )
    event_poll_seconden: int = Field(default=5, alias="WOSZ_EVENT_POLL_SECONDEN")
    event_max_pogingen: int = Field(default=3, alias="WOSZ_EVENT_MAX_POGINGEN")
    cors_origins: str = Field(default="*", alias="WOSZ_CORS_ORIGINS")

    # Alleen de uitbetalingsmodule leest dit veld. Agents hebben geen toegang
    # tot dit object — zie app/payouts/README.md.
    uitbetaling_export_map: str = Field(
        default="./exports", alias="WOSZ_UITBETALING_EXPORT_MAP"
    )

    @property
    def cors_origin_lijst(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


@lru_cache
def get_agent_settings() -> AgentSettings:
    return AgentSettings()
