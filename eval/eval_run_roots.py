"""Eval run directory roots under ``settings.eval_runs_dir``."""

from __future__ import annotations

from pathlib import Path

from plant_id.infrastructure.config.settings import Settings

FULL_IDENTIFY_SUBDIR = "full_identify"
RAG_RETRIEVAL_ONLY_SUBDIR = "rag_retrieval_only"

LAYOUT_SUBDIRS = frozenset({FULL_IDENTIFY_SUBDIR, RAG_RETRIEVAL_ONLY_SUBDIR})

RETRIEVAL_RUN_TYPES = frozenset({"rag_retrieval_only", "retrieval"})


def classify_eval_run_dir(run_dir: Path) -> str:
    """Return ``full_identify`` or ``rag_retrieval_only`` for a run bundle directory."""
    report_path = run_dir / "eval" / "report.json"
    if not report_path.is_file():
        return FULL_IDENTIFY_SUBDIR

    try:
        import json

        payload = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return FULL_IDENTIFY_SUBDIR

    run_type = str(payload.get("run_type", "")).strip().lower()
    if run_type in RETRIEVAL_RUN_TYPES:
        return RAG_RETRIEVAL_ONLY_SUBDIR
    if run_type == FULL_IDENTIFY_SUBDIR:
        return FULL_IDENTIFY_SUBDIR

    if "misclassification_count" in payload or "top1_accuracy" in payload:
        return FULL_IDENTIFY_SUBDIR
    if payload.get("retrieval") and "top1_accuracy_all" not in payload:
        return RAG_RETRIEVAL_ONLY_SUBDIR
    if str(payload.get("backend", "")).startswith("nemotron"):
        return RAG_RETRIEVAL_ONLY_SUBDIR
    return FULL_IDENTIFY_SUBDIR


def full_identify_eval_runs_root(settings: Settings) -> Path:
    return settings.eval_runs_dir / FULL_IDENTIFY_SUBDIR


def rag_retrieval_only_eval_runs_root(settings: Settings) -> Path:
    return settings.eval_runs_dir / RAG_RETRIEVAL_ONLY_SUBDIR


def resolve_eval_run_paths(
    settings: Settings,
    eval_run_id: str,
    *,
    prefer: str | None = None,
):
    """Locate a run under ``full_identify/`` or ``rag_retrieval_only/``."""
    from eval.run_registry import eval_run_paths

    order: list[Path]
    if prefer == FULL_IDENTIFY_SUBDIR:
        order = [full_identify_eval_runs_root(settings)]
    elif prefer == RAG_RETRIEVAL_ONLY_SUBDIR:
        order = [rag_retrieval_only_eval_runs_root(settings)]
    else:
        order = [
            full_identify_eval_runs_root(settings),
            rag_retrieval_only_eval_runs_root(settings),
            settings.eval_runs_dir,
        ]

    for root in order:
        paths = eval_run_paths(root, eval_run_id)
        if paths.report_path.is_file() or paths.run_dir.is_dir():
            return paths
    return eval_run_paths(full_identify_eval_runs_root(settings), eval_run_id)
