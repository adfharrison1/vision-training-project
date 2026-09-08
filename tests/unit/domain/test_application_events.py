from tests.support.recording_events import recording_application_events

from plant_id.domain.application_events import (
    NoopApplicationEvents,
    application_events,
    log_event,
    log_stage,
    use_application_events,
)


def test_application_events_defaults_to_noop() -> None:
    assert isinstance(application_events(), NoopApplicationEvents)


def test_log_event_uses_bound_handler() -> None:
    with recording_application_events() as events:
        log_event("saved artifact")

    assert events.calls == [("log_event", "saved artifact")]


def test_log_stage_uses_bound_handler() -> None:
    with recording_application_events() as events:
        log_stage(1, 4, "Validated photos")

    assert events.calls == [("log_stage", "1", "4", "Validated photos")]


def test_use_application_events_restores_previous_binding() -> None:
    from tests.support.recording_events import RecordingApplicationEvents

    outer = RecordingApplicationEvents()
    inner = RecordingApplicationEvents()

    with use_application_events(outer):
        log_event("outer")
        with use_application_events(inner):
            log_event("inner")
        log_event("outer again")

    assert outer.calls == [("log_event", "outer"), ("log_event", "outer again")]
    assert inner.calls == [("log_event", "inner")]
