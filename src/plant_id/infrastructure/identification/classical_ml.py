"""Classical ML identification backend (stub until Change 3)."""

from __future__ import annotations

from plant_id.domain.exceptions import IdentificationError
from plant_id.domain.models import Observation, ObservationResult
from plant_id.domain.repositories import SpeciesCatalogRepository
from plant_id.infrastructure.config.settings import Settings


class ClassicalMlIdentificationRepository:
    """Placeholder for a trained classical ML backend."""

    def __init__(
        self,
        settings: Settings,
        species_catalog: SpeciesCatalogRepository,
    ) -> None:
        self._settings = settings
        self._species_catalog = species_catalog

    @property
    def backend_id(self) -> str:
        return "ml:not-implemented"

    def identify(self, observation: Observation) -> tuple[ObservationResult, dict]:
        _ = self._species_catalog.list_class_names()
        raise IdentificationError(
            "Classical ML backend is not implemented yet. Use --backend vlm."
            f" (observation {observation.observation_id})"
        )
