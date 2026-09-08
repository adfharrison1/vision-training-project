"""CLI-specific presentation for composition entrypoints."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from plant_id.interfaces.cli.rich_events import RichApplicationEvents
from plant_id.interfaces.composition import Backend, IdentifyRunResult, Settings, execute_identify


def identify_with_cli_presentation(
    backend: Backend,
    photo_paths: Sequence[Path | str],
    observation_id: str,
    settings: Settings | None = None,
    *,
    quiet: bool = False,
) -> IdentifyRunResult:
    """Run identification with optional Rich progress on stderr."""
    if quiet:
        return execute_identify(backend, photo_paths, observation_id, settings)

    photo_count = len(tuple(photo_paths))
    header = f"Identifying with {backend} backend ({photo_count} photo(s))"
    return execute_identify(
        backend,
        photo_paths,
        observation_id,
        settings,
        event_handler=RichApplicationEvents(),
        session_header=header,
        session_footer="Identification complete",
    )
