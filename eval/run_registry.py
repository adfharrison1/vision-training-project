"""Eval run directory layout, manifests, and index catalog."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


def safe_eval_run_id(eval_run_id: str) -> str:
    return eval_run_id.replace("/", "-").replace(" ", "-")


@dataclass(frozen=True)
class EvalRunPaths:
    run_dir: Path
    artifacts_dir: Path
    eval_dir: Path
    report_path: Path
    failures_dir: Path
    manifest_path: Path


def eval_run_paths(eval_runs_root: Path, eval_run_id: str) -> EvalRunPaths:
    safe_id = safe_eval_run_id(eval_run_id)
    run_dir = eval_runs_root / safe_id
    eval_dir = run_dir / "eval"
    return EvalRunPaths(
        run_dir=run_dir,
        artifacts_dir=run_dir / "artifacts",
        eval_dir=eval_dir,
        report_path=eval_dir / "report.json",
        failures_dir=eval_dir / "failures",
        manifest_path=run_dir / "manifest.json",
    )


def ensure_run_dirs(paths: EvalRunPaths) -> None:
    paths.artifacts_dir.mkdir(parents=True, exist_ok=True)
    paths.eval_dir.mkdir(parents=True, exist_ok=True)


def run_dir_exists(paths: EvalRunPaths) -> bool:
    return paths.run_dir.is_dir() and any(paths.run_dir.iterdir())


def capture_git_commit() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return None
    commit = result.stdout.strip()
    return commit or None


class EvalRunManifest(BaseModel):
    model_config = ConfigDict(frozen=True)

    eval_run_id: str
    run_purpose: str
    profile: str
    backend: str
    model_tag: str
    prompt_version: str
    split: str
    started_at: str
    finished_at: str
    git_commit: str | None = None
    report_path: str
    artifacts_dir: str
    failures_dir: str
    observation_count: int = 0
    success_count: int = 0
    top1_accuracy_all: float = 0.0
    top3_accuracy_all: float = 0.0
    parse_failure_count: int = 0
    misclassification_count: int = 0
    partial: bool = False


class EvalRunIndexEntry(BaseModel):
    model_config = ConfigDict(frozen=True)

    eval_run_id: str
    run_purpose: str
    profile: str
    backend: str
    started_at: str
    finished_at: str
    report_path: str
    top1_accuracy_all: float = 0.0
    observation_count: int = 0
    git_commit: str | None = None


class EvalRunIndex(BaseModel):
    model_config = ConfigDict(frozen=True)

    runs: list[EvalRunIndexEntry] = Field(default_factory=list)


def _relative_path(path: Path, base: Path) -> str:
    try:
        return str(path.relative_to(base))
    except ValueError:
        return str(path)


def write_manifest(
    *,
    paths: EvalRunPaths,
    eval_runs_root: Path,
    manifest: EvalRunManifest,
) -> Path:
    paths.manifest_path.parent.mkdir(parents=True, exist_ok=True)
    paths.manifest_path.write_text(
        manifest.model_dump_json(indent=2) + "\n",
        encoding="utf-8",
    )
    return paths.manifest_path


def append_index_entry(
    eval_runs_root: Path,
    entry: EvalRunIndexEntry,
) -> Path:
    index_path = eval_runs_root / "index.json"
    eval_runs_root.mkdir(parents=True, exist_ok=True)

    if index_path.is_file():
        payload = json.loads(index_path.read_text(encoding="utf-8"))
        index = EvalRunIndex.model_validate(payload)
        runs = [r for r in index.runs if r.eval_run_id != entry.eval_run_id]
        runs.append(entry)
    else:
        runs = [entry]

    runs.sort(key=lambda r: r.finished_at, reverse=True)
    index_path.write_text(
        EvalRunIndex(runs=runs).model_dump_json(indent=2) + "\n",
        encoding="utf-8",
    )
    return index_path


def manifest_from_report(
    *,
    paths: EvalRunPaths,
    eval_runs_root: Path,
    run_purpose: str,
    prompt_version: str,
    started_at: str,
    finished_at: str,
    git_commit: str | None,
    report_payload: dict[str, Any],
) -> EvalRunManifest:
    return EvalRunManifest(
        eval_run_id=str(report_payload["eval_run_id"]),
        run_purpose=run_purpose,
        profile=str(report_payload["profile"]),
        backend=str(report_payload["backend"]),
        model_tag=str(report_payload["model_tag"]),
        prompt_version=prompt_version,
        split=str(report_payload["split"]),
        started_at=started_at,
        finished_at=finished_at,
        git_commit=git_commit,
        report_path=_relative_path(paths.report_path, eval_runs_root),
        artifacts_dir=_relative_path(paths.artifacts_dir, eval_runs_root),
        failures_dir=_relative_path(paths.failures_dir, eval_runs_root),
        observation_count=int(report_payload.get("observation_count", 0)),
        success_count=int(report_payload.get("success_count", 0)),
        top1_accuracy_all=float(report_payload.get("top1_accuracy_all", 0.0)),
        top3_accuracy_all=float(report_payload.get("top3_accuracy_all", 0.0)),
        parse_failure_count=int(report_payload.get("parse_failure_count", 0)),
        misclassification_count=int(report_payload.get("misclassification_count", 0)),
        partial=bool(report_payload.get("partial", False)),
    )


def index_entry_from_manifest(manifest: EvalRunManifest) -> EvalRunIndexEntry:
    return EvalRunIndexEntry(
        eval_run_id=manifest.eval_run_id,
        run_purpose=manifest.run_purpose,
        profile=manifest.profile,
        backend=manifest.backend,
        started_at=manifest.started_at,
        finished_at=manifest.finished_at,
        report_path=manifest.report_path,
        top1_accuracy_all=manifest.top1_accuracy_all,
        observation_count=manifest.observation_count,
        git_commit=manifest.git_commit,
    )


def utc_now_iso() -> str:
    return datetime.now(tz=UTC).isoformat()
