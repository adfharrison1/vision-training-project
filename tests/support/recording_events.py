from collections.abc import Iterator
from contextlib import contextmanager

from plant_id.domain.application_events import use_application_events


@contextmanager
def recording_application_events() -> Iterator[RecordingApplicationEvents]:
    events = RecordingApplicationEvents()
    with use_application_events(events):
        yield events


class RecordingApplicationEvents:
    """Test double that records event calls."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, ...]] = []

    def begin_session(self, message: str) -> None:
        self.calls.append(("begin_session", message))

    def end_session(self, message: str) -> None:
        self.calls.append(("end_session", message))

    def log_event(self, message: str) -> None:
        self.calls.append(("log_event", message))

    def log_stage(self, step: int, total: int, message: str) -> None:
        self.calls.append(("log_stage", str(step), str(total), message))

    @contextmanager
    def log_wait(self, step: int, total: int, message: str) -> Iterator[None]:
        self.calls.append(("log_wait_begin", str(step), str(total), message))
        yield
        self.calls.append(("log_wait_end", str(step), str(total), message))
