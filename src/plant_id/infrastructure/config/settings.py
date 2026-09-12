from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _project_root() -> Path:
    return Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    """Application configuration loaded from environment variables and defaults."""

    model_config = SettingsConfigDict(
        env_prefix="PLANT_ID_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ollama_host: str = Field(
        default="http://127.0.0.1:11434",
        description="Base URL for the local Ollama server.",
    )
    ollama_timeout_seconds: float = Field(
        default=600.0,
        gt=0,
        description=(
            "Maximum seconds to wait for a single Ollama chat request "
            "(vision calls on 2b typically finish within a few minutes)."
        ),
    )
    ollama_think: bool = Field(
        default=False,
        description=(
            "When true, allow qwen3 thinking mode on Ollama chat requests. "
            "Default false avoids token-budget death spirals on closed-set identify."
        ),
    )
    vision_model: str = Field(
        default="qwen3-vl:2b",
        description=(
            "Ollama vision model tag (default 2b for fast local iteration; "
            "override e.g. qwen3-vl:8b for comparison)."
        ),
    )
    min_ollama_version: str = Field(
        default="0.33.3",
        description="Minimum supported Ollama server version.",
    )
    species_catalog_path: Path = Field(
        default_factory=lambda: _project_root()
        / "resources"
        / "species_catalog"
        / "default.txt",
        description="Newline-delimited closed-set species label list for identification.",
    )
    uncertainty_threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Top prediction confidence below this marks result as uncertain.",
    )
    artifacts_dir: Path = Field(
        default_factory=lambda: _project_root() / "artifacts",
        description="Directory for persisted identification run JSON artifacts.",
    )
    prompt_version: str = Field(
        default="closed-set-v3",
        description="Prompt template version recorded in artifacts.",
    )
    opik_enabled: bool = Field(
        default=False,
        description="Export Ollama VLM traces to a local self-hosted Opik server.",
    )
    opik_base_url: str = Field(
        default="http://127.0.0.1:5173/api",
        description="Self-hosted Opik API base URL (local only — no Comet cloud).",
    )
    opik_project_name: str = Field(
        default="plant-id",
        description="Opik project name for identification traces.",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
