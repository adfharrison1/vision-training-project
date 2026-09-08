"""Composition root: wire settings, repositories, and use cases."""

from __future__ import annotations

from typing import Literal

from plant_id.application.use_cases.identify_plant import IdentifyPlantUseCase
from plant_id.infrastructure.config.settings import Settings
from plant_id.infrastructure.identification.classical_ml import ClassicalMlIdentificationRepository
from plant_id.infrastructure.identification.vlm_ollama import VlmOllamaIdentificationRepository
from plant_id.infrastructure.persistence.file_artifacts import FileArtifactRepository
from plant_id.infrastructure.species.file_catalog import FileSpeciesCatalog

Backend = Literal["vlm", "classical"]


def build_identify_use_case(
    backend: Backend,
    settings: Settings | None = None,
) -> IdentifyPlantUseCase:
    """Build an identification use case for the requested backend."""
    settings = settings or Settings()
    species_catalog = FileSpeciesCatalog(settings.species_catalog_path)

    if backend == "vlm":
        identification_repo = VlmOllamaIdentificationRepository(settings, species_catalog)
    elif backend == "classical":
        identification_repo = ClassicalMlIdentificationRepository(settings, species_catalog)
    else:
        raise ValueError(f"Unknown backend: {backend!r}")

    artifact_repo = FileArtifactRepository(settings.artifacts_dir)
    return IdentifyPlantUseCase(identification_repo, artifact_repo)
