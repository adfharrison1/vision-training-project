"""JSON artifact persistence for identification runs."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from plant_id.domain.application_events import log_event
from plant_id.domain.models import Observation, ObservationResult


class FileArtifactRepository:
    """Write identification run records as JSON files."""

    def __init__(self, artifacts_dir: Path) -> None:
        self._artifacts_dir = artifacts_dir

    def save_identification_run(
        self,
        observation: Observation,
        raw: dict,
        result: ObservationResult | None,
        error: str | None,
    ) -> Path:
        self._artifacts_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(tz=UTC)
        filename = f"{timestamp.strftime('%Y%m%dT%H%M%S')}_{observation.observation_id}.json"
        path = self._artifacts_dir / filename

        request_meta = raw.get("request", {})
        payload = {
            "observation_id": observation.observation_id,
            "photo_paths": [str(photo_path) for photo_path in observation.photo_paths],
            "timestamp": timestamp.isoformat(),
            "raw": raw,
            "result": result.model_dump(mode="json") if result is not None else None,
            "error": error,
            "model_tag": result.model_tag if result is not None else request_meta.get("model"),
            "prompt_version": (
                result.prompt_version if result is not None else request_meta.get("prompt_version")
            ),
        }
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        log_event(f"Saved run artifact to {path}")
        return path
