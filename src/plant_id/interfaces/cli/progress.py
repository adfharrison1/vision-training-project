"""Bind CLI presentation for an identification run."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from plant_id.domain.application_events import use_application_events
from plant_id.infrastructure.composition.container import Backend
from plant_id.infrastructure.config.settings import Settings
from plant_id.interfaces.cli.rich_events import RichApplicationEvents


@contextmanager
def identification_progress(
    backend: Backend,
    photo_count: int,
    settings: Settings,
    *,
    quiet: bool = False,
) -> Iterator[None]:
    """Bind Rich CLI events for the duration of an identification run."""
    if quiet:
        yield
        return

    header = f"Identifying with {backend} backend ({photo_count} photo(s))"
    events = RichApplicationEvents()
    with use_application_events(events):
        events.begin_session(header)
        try:
            yield
        finally:
            events.end_session("Identification complete")
