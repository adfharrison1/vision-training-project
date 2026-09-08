import json
from pathlib import Path

from plant_id.domain.models import Observation, ObservationResult, Prediction
from plant_id.infrastructure.persistence.file_artifacts import FileArtifactRepository


def test_file_artifact_repository_writes_json(tmp_path: Path) -> None:
    repo = FileArtifactRepository(tmp_path)
    observation = Observation(observation_id="obs-1", photo_paths=[Path("a.jpg")])
    result = ObservationResult(
        observation_id="obs-1",
        predictions=(
            Prediction(
                rank=1,
                species_label="pink primrose",
                evidence="pink petals",
                confidence=0.9,
            ),
        ),
        model_tag="vlm:qwen3-vl:8b",
        prompt_version="closed-set-v1",
    )
    raw = {"response": {"message": {"content": "{}"}}}

    path = repo.save_identification_run(
        observation=observation,
        raw=raw,
        result=result,
        error=None,
    )

    assert path.exists()
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["observation_id"] == "obs-1"
    assert payload["result"]["predictions"][0]["species_label"] == "pink primrose"
    assert payload["raw"] == raw
    assert payload["error"] is None
