"""Identify a plant from photograph paths."""

from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path

from plant_id.domain.exceptions import IdentificationError, InvalidObservationError
from plant_id.domain.models import Observation
from plant_id.infrastructure.composition.container import Backend, build_identify_use_case
from plant_id.infrastructure.config.settings import Settings
from plant_id.interfaces.cli.progress import identification_progress


def run_identify(
    backend: Backend,
    photos: str,
    observation_id: str | None = None,
    settings: Settings | None = None,
    quiet: bool = False,
) -> int:
    settings = settings or Settings()
    photo_paths = tuple(Path(path.strip()) for path in photos.split(",") if path.strip())
    obs_id = observation_id or str(uuid.uuid4())

    try:
        observation = Observation(observation_id=obs_id, photo_paths=photo_paths)
    except InvalidObservationError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    use_case = build_identify_use_case(backend, settings)
    try:
        with identification_progress(
            backend,
            len(photo_paths),
            settings,
            quiet=quiet,
        ):
            result = use_case.execute(observation)
    except IdentificationError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(json.dumps(result.model_dump(mode="json"), indent=2))
    return 0
