"""Identify a plant observation via repository ports."""

from __future__ import annotations

from plant_id.domain.exceptions import IdentificationError
from plant_id.domain.models import Observation, ObservationResult
from plant_id.domain.repositories import ArtifactRepository, IdentificationRepository


class IdentifyPlantUseCase:
    """Application entry point for single-plant species identification."""

    def __init__(
        self,
        identification_repo: IdentificationRepository,
        artifact_repo: ArtifactRepository,
    ) -> None:
        self._identification_repo = identification_repo
        self._artifact_repo = artifact_repo

    def execute(self, observation: Observation) -> ObservationResult:
        raw: dict = {}
        try:
            result, raw = self._identification_repo.identify(observation)
        except IdentificationError as exc:
            self._artifact_repo.save_identification_run(
                observation=observation,
                raw=exc.raw,
                result=None,
                error=str(exc),
            )
            raise
        except Exception as exc:
            self._artifact_repo.save_identification_run(
                observation=observation,
                raw=raw,
                result=None,
                error=str(exc),
            )
            raise IdentificationError(
                f"Identification failed for observation {observation.observation_id}."
            ) from exc

        self._artifact_repo.save_identification_run(
            observation=observation,
            raw=raw,
            result=result,
            error=None,
        )
        return result
