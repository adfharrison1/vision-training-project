"""Identify a plant from photograph paths."""

from __future__ import annotations

import sys
import uuid
from pathlib import Path

from plant_id.interfaces.cli.presentation import identify_with_cli_presentation
from plant_id.interfaces.composition import Backend, Settings, load_settings


def run_identify(
    backend: Backend,
    photos: str,
    observation_id: str | None = None,
    settings: Settings | None = None,
    quiet: bool = False,
) -> int:
    settings = settings or load_settings()
    photo_paths = tuple(Path(path.strip()) for path in photos.split(",") if path.strip())
    obs_id = observation_id or str(uuid.uuid4())

    outcome = identify_with_cli_presentation(
        backend,
        photo_paths,
        obs_id,
        settings,
        quiet=quiet,
    )
    if outcome.error_message:
        print(outcome.error_message, file=sys.stderr)
    if outcome.output_json:
        print(outcome.output_json)
    return outcome.exit_code
