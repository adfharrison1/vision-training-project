from dataclasses import dataclass, field
from pathlib import Path

import pytest

from plant_id.application.use_cases.identify_plant import IdentifyPlantUseCase
from plant_id.domain.exceptions import IdentificationError
from plant_id.domain.models import Observation, ObservationResult, Prediction


@dataclass
class FakeIdentificationRepository:
    result: ObservationResult
    backend_id: str = "fake:test"
    calls: list[tuple[str, Observation]] = field(default_factory=list)
    error: Exception | None = None

    def identify(self, observation: Observation) -> tuple[ObservationResult, dict]:
        self.calls.append(("identify", observation))
        if self.error is not None:
            raise self.error
        return self.result, {"fake": True}


@dataclass
class FakeArtifactRepository:
    calls: list[tuple[str, Observation, dict, ObservationResult | None, str | None]] = field(
        default_factory=list
    )
    saved_path: Path = Path("/tmp/artifact.json")

    def save_identification_run(
        self,
        observation: Observation,
        raw: dict,
        result: ObservationResult | None,
        error: str | None,
    ) -> Path:
        self.calls.append(("save", observation, raw, result, error))
        return self.saved_path


def sample_result(observation_id: str = "obs-1") -> ObservationResult:
    return ObservationResult(
        observation_id=observation_id,
        predictions=(
            Prediction(
                rank=1,
                species_label="pink primrose",
                evidence="five pink petals",
                confidence=0.9,
            ),
        ),
        model_tag="fake:test",
        prompt_version="test-v1",
    )


def test_use_case_returns_identification_result() -> None:
    observation = Observation(observation_id="obs-1", photo_paths=[Path("a.jpg")])
    id_repo = FakeIdentificationRepository(result=sample_result())
    artifact_repo = FakeArtifactRepository()
    use_case = IdentifyPlantUseCase(id_repo, artifact_repo)

    result = use_case.execute(observation)

    assert result.observation_id == "obs-1"
    assert result.predictions[0].species_label == "pink primrose"


def test_use_case_calls_identify_before_persist() -> None:
    observation = Observation(observation_id="obs-2", photo_paths=[Path("a.jpg")])
    id_repo = FakeIdentificationRepository(result=sample_result("obs-2"))
    artifact_repo = FakeArtifactRepository()
    use_case = IdentifyPlantUseCase(id_repo, artifact_repo)

    use_case.execute(observation)

    assert len(id_repo.calls) == 1
    assert len(artifact_repo.calls) == 1
    assert id_repo.calls[0][0] == "identify"
    assert artifact_repo.calls[0][0] == "save"
    assert artifact_repo.calls[0][3] is not None
    assert artifact_repo.calls[0][4] is None


def test_use_case_persists_error_when_identification_fails() -> None:
    observation = Observation(observation_id="obs-3", photo_paths=[Path("a.jpg")])
    id_repo = FakeIdentificationRepository(
        result=sample_result("obs-3"),
        error=RuntimeError("backend unavailable"),
    )
    artifact_repo = FakeArtifactRepository()
    use_case = IdentifyPlantUseCase(id_repo, artifact_repo)

    with pytest.raises(IdentificationError, match="obs-3"):
        use_case.execute(observation)

    assert len(artifact_repo.calls) == 1
    assert artifact_repo.calls[0][3] is None
    assert artifact_repo.calls[0][4] == "backend unavailable"


def test_use_case_persists_identification_error_from_repository() -> None:
    observation = Observation(observation_id="obs-4", photo_paths=[Path("a.jpg")])
    id_repo = FakeIdentificationRepository(
        result=sample_result("obs-4"),
        error=IdentificationError("parse failed"),
    )
    artifact_repo = FakeArtifactRepository()
    use_case = IdentifyPlantUseCase(id_repo, artifact_repo)

    with pytest.raises(IdentificationError, match="parse failed"):
        use_case.execute(observation)

    assert len(id_repo.calls) == 1
    assert len(artifact_repo.calls) == 1
    assert artifact_repo.calls[0][4] == "parse failed"
