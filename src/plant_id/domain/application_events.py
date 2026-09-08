"""Application-wide event hooks (logging, progress) via context-local binding."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar, Token
from typing import Protocol


class ApplicationEvents(Protocol):
    """Port for cross-cutting runtime events without UI dependencies."""

    def begin_session(self, message: str) -> None: ...

    def end_session(self, message: str) -> None: ...

    def log_event(self, message: str) -> None: ...

    def log_stage(self, step: int, total: int, message: str) -> None: ...

    @contextmanager
    def log_wait(self, step: int, total: int, message: str) -> Iterator[None]: ...


class NoopApplicationEvents:
    """Default handler: silently ignore all events."""

    def begin_session(self, message: str) -> None:
        _ = message

    def end_session(self, message: str) -> None:
        _ = message

    def log_event(self, message: str) -> None:
        _ = message

    def log_stage(self, step: int, total: int, message: str) -> None:
        _ = (step, total, message)

    @contextmanager
    def log_wait(self, step: int, total: int, message: str) -> Iterator[None]:
        _ = (step, total, message)
        yield


_NOOP = NoopApplicationEvents()
_events: ContextVar[ApplicationEvents | None] = ContextVar("application_events", default=None)


def application_events() -> ApplicationEvents:
    """Return the bound event handler for the current context, or a no-op default."""
    return _events.get() or _NOOP


def bind_application_events(events: ApplicationEvents) -> Token[ApplicationEvents | None]:
    """Bind an event handler for the current context."""
    return _events.set(events)


def reset_application_events(token: Token[ApplicationEvents | None]) -> None:
    """Restore the previous event handler binding."""
    _events.reset(token)


@contextmanager
def use_application_events(events: ApplicationEvents) -> Iterator[None]:
    """Bind an event handler for the duration of a block."""
    token = bind_application_events(events)
    try:
        yield
    finally:
        reset_application_events(token)


def log_event(message: str) -> None:
    """Emit a general runtime event in the current context."""
    application_events().log_event(message)


def log_stage(step: int, total: int, message: str) -> None:
    """Mark a numbered pipeline stage complete in the current context."""
    application_events().log_stage(step, total, message)


@contextmanager
def log_wait(step: int, total: int, message: str) -> Iterator[None]:
    """Wrap a long-running stage in the current context."""
    with application_events().log_wait(step, total, message):
        yield
