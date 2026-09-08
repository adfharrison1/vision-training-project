"""Bind ApplicationEvents handlers for the duration of a composition call."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from plant_id.domain.application_events import ApplicationEvents, use_application_events


@contextmanager
def application_events_session(handler: ApplicationEvents) -> Iterator[ApplicationEvents]:
    """Bind an event handler for the duration of a block."""
    with use_application_events(handler):
        yield handler
