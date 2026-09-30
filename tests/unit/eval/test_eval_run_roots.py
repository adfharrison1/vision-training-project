from pathlib import Path

from eval.eval_run_roots import (
    FULL_IDENTIFY_SUBDIR,
    RAG_RETRIEVAL_ONLY_SUBDIR,
    classify_eval_run_dir,
)


def test_classify_retrieval_run_type(tmp_path: Path) -> None:
    run_dir = tmp_path / "r1"
    report_dir = run_dir / "eval"
    report_dir.mkdir(parents=True)
    report_dir.joinpath("report.json").write_text(
        '{"run_type": "rag_retrieval_only", "backend": "nemotron-prototype"}\n',
        encoding="utf-8",
    )
    assert classify_eval_run_dir(run_dir) == RAG_RETRIEVAL_ONLY_SUBDIR


def test_classify_legacy_retrieval_report(tmp_path: Path) -> None:
    run_dir = tmp_path / "nemotron-smoke"
    report_dir = run_dir / "eval"
    report_dir.mkdir(parents=True)
    report_dir.joinpath("report.json").write_text(
        '{"run_type": "retrieval", "backend": "nemotron-prototype", "recall_at_k": {}}\n',
        encoding="utf-8",
    )
    assert classify_eval_run_dir(run_dir) == RAG_RETRIEVAL_ONLY_SUBDIR


def test_classify_identify_report(tmp_path: Path) -> None:
    run_dir = tmp_path / "smoke-check"
    report_dir = run_dir / "eval"
    report_dir.mkdir(parents=True)
    report_dir.joinpath("report.json").write_text(
        '{"top1_accuracy": 0.5, "misclassification_count": 1}\n',
        encoding="utf-8",
    )
    assert classify_eval_run_dir(run_dir) == FULL_IDENTIFY_SUBDIR
