"""Composition root: wire settings, repositories, and use cases."""

from __future__ import annotations

from typing import Literal

from plant_id.application.use_cases.identify_plant import IdentifyPlantUseCase
from plant_id.infrastructure.config.settings import Settings
from plant_id.infrastructure.identification.classical_ml import ClassicalMlIdentificationRepository
from plant_id.infrastructure.identification.vlm_ollama import VlmOllamaIdentificationRepository
from plant_id.infrastructure.ollama.environment import VerifyEnvResult, verify_environment
from plant_id.infrastructure.persistence.file_artifacts import FileArtifactRepository
from plant_id.infrastructure.species.file_catalog import FileSpeciesCatalog

Backend = Literal["vlm", "classical"]


def load_settings() -> Settings:
    """Load runtime settings from environment and defaults."""
    return Settings()


def resolve_settings(
    settings: Settings | None = None,
    *,
    ollama_think: bool | None = None,
) -> Settings:
    """Merge optional per-run overrides onto loaded settings."""
    resolved = settings or load_settings()
    if ollama_think is None:
        return resolved
    return resolved.model_copy(update={"ollama_think": ollama_think})


def build_identify_use_case(
    backend: Backend,
    settings: Settings | None = None,
) -> IdentifyPlantUseCase:
    """Build an identification use case for the requested backend."""
    settings = settings or load_settings()
    species_catalog = FileSpeciesCatalog(settings.species_catalog_path)

    if backend == "vlm":
        identification_repo = VlmOllamaIdentificationRepository(settings, species_catalog)
    elif backend == "classical":
        identification_repo = ClassicalMlIdentificationRepository(settings, species_catalog)
    else:
        raise ValueError(f"Unknown backend: {backend!r}")

    artifact_repo = FileArtifactRepository(settings.artifacts_dir)
    return IdentifyPlantUseCase(identification_repo, artifact_repo)


__all__ = [
    "Backend",
    "IdentifyPlantUseCase",
    "Settings",
    "VerifyEnvResult",
    "build_identify_use_case",
    "load_settings",
    "resolve_settings",
    "verify_environment",
]
