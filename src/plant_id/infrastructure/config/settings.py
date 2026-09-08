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
    vision_model: str = Field(
        default="qwen3-vl:8b",
        description="Ollama vision model tag (confirm via hardware spike task 1.6).",
    )
    min_ollama_version: str = Field(
        default="0.33.3",
        description="Minimum supported Ollama server version.",
    )
    class_names_path: Path = Field(
        default_factory=lambda: _project_root() / "resources" / "oxford102" / "class_names.txt",
        description="Bundled Oxford 102 class name list.",
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
        default="oxford102-closed-set-v1",
        description="Prompt template version recorded in artifacts.",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
