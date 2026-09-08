"""Run identification through the composition root."""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from plant_id.domain.application_events import ApplicationEvents
from plant_id.domain.exceptions import IdentificationError, InvalidObservationError
from plant_id.domain.models import Observation, ObservationResult
from plant_id.interfaces.composition.container import (
    Backend,
    Settings,
    build_identify_use_case,
    load_settings,
)
from plant_id.interfaces.composition.events import application_events_session


@dataclass(frozen=True)
class IdentifyRunResult:
    exit_code: int
    error_message: str | None = None
    result: ObservationResult | None = None

    @property
    def output_json(self) -> str | None:
        if self.result is None:
            return None
        return json.dumps(self.result.model_dump(mode="json"), indent=2)


def execute_identify(
    backend: Backend,
    photo_paths: Sequence[Path | str],
    observation_id: str,
    settings: Settings | None = None,
    *,
    event_handler: ApplicationEvents | None = None,
    session_header: str | None = None,
    session_footer: str | None = None,
) -> IdentifyRunResult:
    """Build an observation, run the use case, and return a structured outcome."""
    settings = settings or load_settings()
    paths = tuple(Path(path) for path in photo_paths)

    try:
        observation = Observation(observation_id=observation_id, photo_paths=paths)
    except InvalidObservationError as exc:
        return IdentifyRunResult(exit_code=1, error_message=str(exc))

    def run() -> IdentifyRunResult:
        use_case = build_identify_use_case(backend, settings)
        try:
            result = use_case.execute(observation)
        except IdentificationError as exc:
            return IdentifyRunResult(exit_code=1, error_message=str(exc))
        return IdentifyRunResult(exit_code=0, result=result)

    if event_handler is None:
        return run()

    with application_events_session(event_handler):
        if session_header is not None:
            event_handler.begin_session(session_header)
        try:
            return run()
        finally:
            if session_footer is not None:
                event_handler.end_session(session_footer)
