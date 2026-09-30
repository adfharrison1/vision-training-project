"""Composition wiring for species retrieval backends."""

from __future__ import annotations

from typing import Literal

from plant_id.domain.species_retrieval import SpeciesRetrievalRepository
from plant_id.infrastructure.config.settings import Settings
from plant_id.infrastructure.retrieval.describe_hybrid_backend import (
    DescribeHybridRetrievalRepository,
)
from plant_id.infrastructure.retrieval.openrouter_prototype_backend import (
    build_in_memory_nemotron_repo,
    build_qdrant_nemotron_repo,
)

RetrievalBackend = Literal["nemotron-prototype", "describe-hybrid"]


def build_species_retrieval_repo(
    backend: RetrievalBackend,
    settings: Settings | None = None,
    *,
    use_qdrant: bool = True,
) -> SpeciesRetrievalRepository:
    settings = settings or Settings()
    if backend == "nemotron-prototype":
        if use_qdrant:
            return build_qdrant_nemotron_repo(settings)
        return build_in_memory_nemotron_repo(settings)
    if backend == "describe-hybrid":
        return DescribeHybridRetrievalRepository(settings)
    raise ValueError(f"Unknown retrieval backend: {backend!r}")
