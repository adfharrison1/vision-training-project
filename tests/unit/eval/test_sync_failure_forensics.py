import json
from pathlib import Path

from eval.failure_forensics import ensure_eval_failure_forensics, eval_failures_dir
from eval.metrics import ObservationResultRow
from eval.run_registry import eval_run_paths


def test_ensure_eval_failure_forensics_backfills_misclass(tmp_path: Path) -> None:
    eval_run_id = "backfill-run"
    paths = eval_run_paths(tmp_path, eval_run_id)
    paths.artifacts_dir.mkdir(parents=True)
    observation_id = "eval-backfill-run-image_00001"
    artifact = paths.artifacts_dir / f"20260101T000000_{observation_id}.json"
    artifact.write_text(
        json.dumps(
            {
                "observation_id": observation_id,
                "raw": {
                    "response": {
                        "choices": [
                            {
                                "message": {
                                    "content": '{"predictions":[{"species_label":"wrong"}]}'
                                }
                            }
                        ]
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    rows = [
        ObservationResultRow(
            image="image_00001.jpg",
            ground_truth="tiger lily",
            predicted="wrong",
            top1_match=False,
            top3_match=False,
            duration_ms=1,
            observation_id=observation_id,
            trace_id="trace-1",
            predictions=("wrong",),
        )
    ]
    ensure_eval_failure_forensics(
        eval_run_id=eval_run_id,
        rows=rows,
        artifacts_dir=paths.artifacts_dir,
        eval_runs_root=tmp_path,
    )
    failure_path = eval_failures_dir(eval_run_id, eval_runs_root=tmp_path) / "image_00001.json"
    assert failure_path.is_file()
    payload = json.loads(failure_path.read_text(encoding="utf-8"))
    assert payload["failure_kind"] == "misclassification"
    assert payload["predicted"] == "wrong"
