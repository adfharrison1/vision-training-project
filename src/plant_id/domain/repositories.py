"""Repository ports (interfaces) for plant identification."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from plant_id.domain.models import Observation, ObservationResult


class IdentificationRepository(Protocol):
    """Swappable backend for species identification."""

    @property
    def backend_id(self) -> str: ...

    def identify(self, observation: Observation) -> tuple[ObservationResult, dict]:
        """Return the structured result and raw model payload for artifact persistence."""
        ...


class ArtifactRepository(Protocol):
    """Persistence for identification run records."""

    def save_identification_run(
        self,
        observation: Observation,
        raw: dict,
        result: ObservationResult | None,
        error: str | None,
    ) -> Path: ...


class SpeciesCatalogRepository(Protocol):
    """Closed-set species vocabulary for label-constrained identification."""

    def list_class_names(self) -> list[str]: ...
