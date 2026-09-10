import json
from pathlib import Path

from eval.metrics import ObservationResultRow, compute_metrics
from eval.report import build_report, write_report


def test_write_report_creates_valid_json(tmp_path: Path) -> None:
    rows = [
        ObservationResultRow(
            image="image_00001.jpg",
            ground_truth="tiger lily",
            predicted="tiger lily",
            top1_match=True,
            top3_match=True,
            duration_ms=100,
            observation_id="obs-1",
            trace_id="trace-123",
        )
    ]
    metrics = compute_metrics(rows)
    report = build_report(
        eval_run_id="prompt-v1",
        profile="smoke",
        model_tag="qwen3-vl:2b",
        backend="vlm",
        split="test",
        metrics=metrics,
        duration_total_ms=100,
    )
    output_path = tmp_path / "nested" / "report.json"
    write_report(report, output_path)

    assert output_path.is_file()
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["eval_run_id"] == "prompt-v1"
    assert payload["profile"] == "smoke"
    assert payload["observations"][0]["trace_id"] == "trace-123"
    assert payload["failures"] == []
