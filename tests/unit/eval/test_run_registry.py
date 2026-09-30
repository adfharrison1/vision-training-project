from pathlib import Path

import pytest
from eval.run_oxford102 import build_parser, run_eval
from eval.run_registry import (
    EvalRunManifest,
    append_index_entry,
    capture_git_commit,
    eval_run_paths,
    index_entry_from_manifest,
    run_dir_exists,
    write_manifest,
)


def test_build_parser_requires_run_purpose() -> None:
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["--profile", "smoke", "--eval-run-id", "x"])


def test_run_dir_exists_detects_nonempty_dir(tmp_path: Path) -> None:
    paths = eval_run_paths(tmp_path, "my-run")
    assert run_dir_exists(paths) is False
    paths.run_dir.mkdir(parents=True)
    (paths.run_dir / "placeholder").write_text("x", encoding="utf-8")
    assert run_dir_exists(paths) is True


def test_index_append_replaces_same_run_id(tmp_path: Path) -> None:
    manifest = EvalRunManifest(
        eval_run_id="run-a",
        run_purpose="test",
        profile="smoke",
        backend="vlm",
        model_tag="qwen3-vl:2b",
        prompt_version="closed-set-v3",
        split="test",
        started_at="2026-01-01T00:00:00+00:00",
        finished_at="2026-01-02T00:00:00+00:00",
        report_path="run-a/eval/report.json",
        artifacts_dir="run-a/artifacts",
        failures_dir="run-a/eval/failures",
        top1_accuracy_all=0.5,
        observation_count=4,
    )
    append_index_entry(tmp_path, index_entry_from_manifest(manifest))
    manifest2 = manifest.model_copy(update={"finished_at": "2026-01-03T00:00:00+00:00"})
    append_index_entry(tmp_path, index_entry_from_manifest(manifest2))
    index_path = tmp_path / "index.json"
    payload = index_path.read_text(encoding="utf-8")
    assert payload.count('"eval_run_id": "run-a"') == 1


def test_write_manifest_round_trip(tmp_path: Path) -> None:
    paths = eval_run_paths(tmp_path, "manifest-test")
    manifest = EvalRunManifest(
        eval_run_id="manifest-test",
        run_purpose="unit test",
        profile="smoke",
        backend="vlm-cloud",
        model_tag="model",
        prompt_version="closed-set-v3",
        split="test",
        started_at="2026-01-01T00:00:00+00:00",
        finished_at="2026-01-01T00:01:00+00:00",
        git_commit=capture_git_commit(),
        report_path="manifest-test/eval/report.json",
        artifacts_dir="manifest-test/artifacts",
        failures_dir="manifest-test/eval/failures",
    )
    write_manifest(paths=paths, eval_runs_root=tmp_path, manifest=manifest)
    assert paths.manifest_path.is_file()


def test_run_eval_rejects_empty_run_purpose() -> None:
    from argparse import Namespace

    args = Namespace(
        profile="smoke",
        eval_run_id="unit-test",
        run_purpose="   ",
        backend="vlm",
        split="test",
        limit=None,
        max_duration=None,
        quiet=True,
        dataset_root=None,
        output=None,
        force=False,
        plantnet_baseline=False,
        profile_manifest=None,
        think=None,
        rag=None,
        retrieval_backend="nemotron-prototype",
    )
    assert run_eval(args) == 1
