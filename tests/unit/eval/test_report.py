import json
from pathlib import Path

from eval.metrics import ObservationResultRow, compute_metrics
from eval.report import InferenceReportSection, build_report, write_report


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
        run_purpose="report unit test",
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


def test_build_report_failures_include_top3_match() -> None:
    rows = [
        ObservationResultRow(
            image="image_02639.jpg",
            ground_truth="geranium",
            predicted="pelargonium",
            top1_match=False,
            top3_match=True,
            duration_ms=100,
            observation_id="obs-1",
        ),
        ObservationResultRow(
            image="image_07123.jpg",
            ground_truth="bolero deep blue",
            predicted="canterbury bells",
            top1_match=False,
            top3_match=False,
            duration_ms=100,
            observation_id="obs-2",
        ),
    ]
    metrics = compute_metrics(rows)
    report = build_report(
        eval_run_id="failures-top3",
        run_purpose="failures top3_match field",
        profile="smoke",
        model_tag="test",
        backend="vlm-cloud",
        split="test",
        metrics=metrics,
        duration_total_ms=200,
    )
    assert len(report.failures) == 2
    by_image = {failure.image: failure for failure in report.failures}
    assert by_image["image_02639.jpg"].top3_match is True
    assert by_image["image_07123.jpg"].top3_match is False


def test_write_report_includes_inference_metadata(tmp_path: Path) -> None:
    rows = [
        ObservationResultRow(
            image="image_00001.jpg",
            ground_truth="tiger lily",
            predicted="tiger lily",
            top1_match=True,
            top3_match=True,
            duration_ms=100,
            observation_id="obs-1",
        )
    ]
    metrics = compute_metrics(rows)
    inference = InferenceReportSection(
        backend="vlm-cloud",
        model="accounts/fireworks/models/qwen3-vl-8b-instruct",
        prompt_version="closed-set-v3",
        cloud_vendor="fireworks",
        cloud_base_url_host="api.fireworks.ai",
    )
    report = build_report(
        eval_run_id="cloud-run",
        run_purpose="inference metadata test",
        profile="smoke",
        model_tag=inference.model,
        backend="vlm-cloud",
        split="test",
        metrics=metrics,
        duration_total_ms=100,
        inference=inference,
    )
    output_path = tmp_path / "report.json"
    write_report(report, output_path)
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["inference"]["cloud_vendor"] == "fireworks"
    assert payload["inference"]["cloud_base_url_host"] == "api.fireworks.ai"


def test_write_report_includes_aggregated_inference_usage(tmp_path: Path) -> None:
    from eval.report import InferenceReportSection, InferenceTokenUsage

    rows = [
        ObservationResultRow(
            image="image_00001.jpg",
            ground_truth="tiger lily",
            predicted="tiger lily",
            top1_match=True,
            top3_match=True,
            duration_ms=100,
            observation_id="obs-1",
            prompt_tokens=900,
            completion_tokens=600,
            total_tokens=1500,
        ),
        ObservationResultRow(
            image="image_00002.jpg",
            ground_truth="pink primrose",
            predicted="pink primrose",
            top1_match=True,
            top3_match=True,
            duration_ms=120,
            observation_id="obs-2",
            prompt_tokens=850,
            completion_tokens=550,
            total_tokens=1400,
        ),
    ]
    metrics = compute_metrics(rows)
    inference = InferenceReportSection(
        backend="vlm-cloud",
        model="accounts/fireworks/models/deepseek-v4p1-flash",
        prompt_version="closed-set-v3",
        usage=InferenceTokenUsage(
            prompt_tokens=1750,
            completion_tokens=1150,
            total_tokens=2900,
            observations_with_usage=2,
        ),
    )
    report = build_report(
        eval_run_id="cloud-run",
        run_purpose="inference metadata test",
        profile="smoke",
        model_tag=inference.model,
        backend="vlm-cloud",
        split="test",
        metrics=metrics,
        duration_total_ms=220,
        inference=inference,
    )
    output_path = tmp_path / "report.json"
    write_report(report, output_path)
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["inference"]["usage"]["total_tokens"] == 2900
    assert payload["observations"][0]["total_tokens"] == 1500


def test_build_report_failure_artifacts_dir_relative_to_eval_runs_root(
    tmp_path: Path,
) -> None:
    eval_root = tmp_path / "full_identify"
    run_id = "layout-run"
    failures_dir = eval_root / run_id / "eval" / "failures"
    failures_dir.mkdir(parents=True)
    (failures_dir / "image_00001.json").write_text("{}", encoding="utf-8")

    rows = [
        ObservationResultRow(
            image="image_00001.jpg",
            ground_truth="tiger lily",
            predicted="wrong",
            top1_match=False,
            top3_match=False,
            duration_ms=1,
            observation_id="obs-1",
        )
    ]
    metrics = compute_metrics(rows)
    report = build_report(
        eval_run_id=run_id,
        run_purpose="relative failure dir",
        profile="smoke",
        model_tag="test",
        backend="vlm",
        split="test",
        metrics=metrics,
        duration_total_ms=1,
        failure_artifacts_dir=failures_dir,
        eval_runs_root=eval_root,
    )
    assert report.failure_artifacts_dir == f"{run_id}/eval/failures"
