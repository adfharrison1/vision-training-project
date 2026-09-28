import json
from pathlib import Path

from eval.failure_forensics import (
    eval_failures_dir,
    extract_identification_forensics,
    invalid_species_label_from_error,
    write_eval_failure_artifact,
)


def test_invalid_species_label_from_error() -> None:
    assert invalid_species_label_from_error("Unknown species_label: calendula") == "calendula"
    assert invalid_species_label_from_error("Other") is None


def test_extract_identification_forensics_from_openai_raw() -> None:
    raw = {
        "response": {
            "choices": [
                {
                    "message": {
                        "content": '{"predictions": []}',
                        "reasoning_content": "x" * 9000,
                    }
                }
            ]
        }
    }
    forensics = extract_identification_forensics(raw)
    assert forensics is not None
    assert "predictions" in forensics["message_content"]
    assert forensics["reasoning_content_chars"] == 9000
    assert "truncated" in forensics["reasoning_content_preview"]


def test_write_eval_failure_artifact(tmp_path: Path) -> None:
    path = write_eval_failure_artifact(
        eval_run_id="debug-run",
        image="image_02189.jpg",
        ground_truth="barbeton daisy",
        observation_id="obs-1",
        error="Unknown species_label: calendula",
        trace_id="trace-1",
        identification_raw={
            "response": {
                "choices": [
                    {"message": {"content": '{"predictions":[{"species_label":"calendula"}]}'}}
                ]
            }
        },
        eval_runs_root=tmp_path,
    )
    assert path == eval_failures_dir("debug-run", eval_runs_root=tmp_path) / "image_02189.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["invalid_species_label"] == "calendula"
    assert "calendula" in payload["model"]["message_content"]
