from unittest.mock import MagicMock, patch

from plant_id.infrastructure.config.settings import Settings
from plant_id.infrastructure.observability import opik_tracing


def test_eval_trace_session_captures_trace_id() -> None:
    settings = Settings().model_copy(update={"opik_enabled": True})

    with patch("plant_id.infrastructure.observability.opik_tracing._configure_opik"):
        with patch(
            "opik.start_as_current_span",
        ) as start_span:
            with patch(
                "opik.opik_context.get_current_trace_data",
                return_value=MagicMock(id="trace-abc"),
            ):
                start_span.return_value.__enter__ = MagicMock(return_value=None)
                start_span.return_value.__exit__ = MagicMock(return_value=False)

                with opik_tracing.eval_trace_session("run-1", "smoke") as session:
                    with opik_tracing.identify_trace(
                        settings,
                        observation_id="eval-run-1-image_00001",
                        backend="vlm:qwen3-vl:2b",
                        photo_count=1,
                    ):
                        pass

                assert session.trace_id == "trace-abc"


def test_record_identify_outcome_adds_eval_metadata() -> None:
    settings = Settings().model_copy(update={"opik_enabled": True})

    with opik_tracing.eval_trace_session(
        "run-1",
        "quick",
        ground_truth="tiger lily",
    ):
        with patch("opik.opik_context.update_current_span") as update_span:
            opik_tracing.record_identify_outcome(
                settings,
                observation_id="eval-run-1-image_00001",
                result_summary={
                    "top_species": "english marigold",
                    "species_labels": ["english marigold", "tiger lily"],
                },
            )

    metadata = update_span.call_args.kwargs["metadata"]
    assert metadata["eval_run_id"] == "run-1"
    assert metadata["eval_profile"] == "quick"
    assert metadata["ground_truth"] == "tiger lily"
    assert metadata["match"] is False
    assert metadata["top3_match"] is True
