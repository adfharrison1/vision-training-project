"""Eval report models and JSON writer."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eval.metrics import EvalMetrics, ObservationResultRow
from eval.retrieval_report import (
    RUN_TYPE_FULL_IDENTIFY,
    RetrievalFailureRow,
    RetrievalObservationReportRow,
    RetrievalPerClassReportRow,
    RetrievalReportSection,
)


class FailureRow(BaseModel):
    model_config = ConfigDict(frozen=True)

    image: str
    ground_truth: str
    predicted: str | None = None
    top3_match: bool
    trace_id: str | None = None
    observation_id: str
    error: str | None = None


class ObservationReportRow(BaseModel):
    model_config = ConfigDict(frozen=True)

    image: str
    ground_truth: str
    predicted: str | None = None
    top1_match: bool
    top3_match: bool
    duration_ms: int
    observation_id: str
    trace_id: str | None = None
    error: str | None = None
    predictions: tuple[str, ...] = ()
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


class PerClassReportRow(BaseModel):
    model_config = ConfigDict(frozen=True)

    total: int
    top1: int
    top3: int


class PlantNetReportSection(BaseModel):
    model_config = ConfigDict(frozen=True)

    enabled: bool
    skipped_reason: str | None = None
    observation_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    top1_accuracy: float = 0.0
    top3_accuracy: float = 0.0
    observations: list[ObservationReportRow] = Field(default_factory=list)


class InferenceTokenUsage(BaseModel):
    model_config = ConfigDict(frozen=True)

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    observations_with_usage: int


class InferenceReportSection(BaseModel):
    model_config = ConfigDict(frozen=True)

    backend: str
    model: str
    prompt_version: str
    cloud_vendor: str | None = None
    cloud_base_url_host: str | None = None
    usage: InferenceTokenUsage | None = None


class EvalReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    eval_run_id: str
    run_type: str = RUN_TYPE_FULL_IDENTIFY
    run_purpose: str
    git_commit: str | None = None
    profile: str
    model_tag: str
    backend: str
    split: str
    observation_count: int
    success_count: int
    failure_count: int
    parse_failure_count: int
    misclassification_count: int
    duration_total_ms: int
    top1_accuracy: float
    top3_accuracy: float
    top1_accuracy_all: float
    top3_accuracy_all: float
    failure_artifacts_dir: str | None = None
    failures: list[FailureRow]
    observations: list[ObservationReportRow]
    per_class: dict[str, PerClassReportRow]
    plantnet: PlantNetReportSection | None = None
    generated_at: str
    partial: bool = False
    stopped_reason: str | None = None
    inference: InferenceReportSection | None = None
    retrieval: RetrievalReportSection | None = None
    retrieval_observations: list[RetrievalObservationReportRow] | None = None
    retrieval_failures: list[RetrievalFailureRow] | None = None
    retrieval_per_class: dict[str, RetrievalPerClassReportRow] | None = None


def default_report_path(
    eval_run_id: str,
    *,
    eval_runs_root: Path | None = None,
) -> Path:
    from eval.eval_run_roots import full_identify_eval_runs_root
    from eval.run_registry import eval_run_paths
    from plant_id.interfaces.composition import load_settings

    if eval_runs_root is not None:
        root = eval_runs_root
    else:
        root = full_identify_eval_runs_root(load_settings())
    return eval_run_paths(root, eval_run_id).report_path


def _observation_row(row: ObservationResultRow) -> ObservationReportRow:
    return ObservationReportRow(
        image=row.image,
        ground_truth=row.ground_truth,
        predicted=row.predicted,
        top1_match=row.top1_match,
        top3_match=row.top3_match,
        duration_ms=row.duration_ms,
        observation_id=row.observation_id,
        trace_id=row.trace_id,
        error=row.error,
        predictions=row.predictions,
        prompt_tokens=row.prompt_tokens,
        completion_tokens=row.completion_tokens,
        total_tokens=row.total_tokens,
    )


def build_report(
    *,
    eval_run_id: str,
    run_purpose: str,
    git_commit: str | None = None,
    profile: str,
    model_tag: str,
    backend: str,
    split: str,
    metrics: EvalMetrics,
    duration_total_ms: int,
    plantnet: PlantNetReportSection | None = None,
    partial: bool = False,
    stopped_reason: str | None = None,
    inference: InferenceReportSection | None = None,
    failure_artifacts_dir: Path | None = None,
    eval_runs_root: Path | None = None,
    retrieval: RetrievalReportSection | None = None,
    retrieval_observations: list[RetrievalObservationReportRow] | None = None,
    retrieval_failures: list[RetrievalFailureRow] | None = None,
    retrieval_per_class: dict[str, RetrievalPerClassReportRow] | None = None,
) -> EvalReport:
    observations = [_observation_row(row) for row in metrics.observations]
    failures = [
        FailureRow(
            image=row.image,
            ground_truth=row.ground_truth,
            predicted=row.predicted,
            top3_match=row.top3_match,
            trace_id=row.trace_id,
            observation_id=row.observation_id,
            error=row.error,
        )
        for row in metrics.observations
        if row.error is not None or not row.top1_match
    ]

    per_class = {
        label: PerClassReportRow(total=stats.total, top1=stats.top1, top3=stats.top3)
        for label, stats in metrics.per_class.items()
    }

    artifacts_dir: str | None = None
    if failure_artifacts_dir is not None and failure_artifacts_dir.is_dir():
        if eval_runs_root is not None:
            from eval.run_registry import relative_eval_run_path

            artifacts_dir = relative_eval_run_path(failure_artifacts_dir, eval_runs_root)
        else:
            artifacts_dir = str(failure_artifacts_dir)

    return EvalReport(
        eval_run_id=eval_run_id,
        run_purpose=run_purpose,
        git_commit=git_commit,
        profile=profile,
        model_tag=model_tag,
        backend=backend,
        split=split,
        observation_count=metrics.observation_count,
        success_count=metrics.success_count,
        failure_count=metrics.failure_count,
        parse_failure_count=metrics.parse_failure_count,
        misclassification_count=metrics.misclassification_count,
        duration_total_ms=duration_total_ms,
        top1_accuracy=metrics.top1_accuracy,
        top3_accuracy=metrics.top3_accuracy,
        top1_accuracy_all=metrics.top1_accuracy_all,
        top3_accuracy_all=metrics.top3_accuracy_all,
        failure_artifacts_dir=artifacts_dir,
        failures=failures,
        observations=observations,
        per_class=per_class,
        plantnet=plantnet,
        generated_at=datetime.now(tz=UTC).isoformat(),
        partial=partial,
        stopped_reason=stopped_reason,
        inference=inference,
        retrieval=retrieval,
        retrieval_observations=retrieval_observations,
        retrieval_failures=retrieval_failures,
        retrieval_per_class=retrieval_per_class,
    )


def write_report(report: EvalReport, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = report.model_dump(mode="json")
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return output_path
