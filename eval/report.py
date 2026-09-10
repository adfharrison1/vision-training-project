"""Eval report models and JSON writer."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eval.metrics import EvalMetrics, ObservationResultRow


class FailureRow(BaseModel):
    model_config = ConfigDict(frozen=True)

    image: str
    ground_truth: str
    predicted: str | None = None
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


class EvalReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    eval_run_id: str
    profile: str
    model_tag: str
    backend: str
    split: str
    observation_count: int
    success_count: int
    failure_count: int
    duration_total_ms: int
    top1_accuracy: float
    top3_accuracy: float
    failures: list[FailureRow]
    observations: list[ObservationReportRow]
    per_class: dict[str, PerClassReportRow]
    plantnet: PlantNetReportSection | None = None
    generated_at: str
    partial: bool = False
    stopped_reason: str | None = None


def default_report_path(eval_run_id: str, artifacts_root: Path | None = None) -> Path:
    root = artifacts_root or Path("artifacts") / "eval"
    timestamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    safe_run_id = eval_run_id.replace("/", "-").replace(" ", "-")
    return root / f"{timestamp}-{safe_run_id}.json"


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
    )


def build_report(
    *,
    eval_run_id: str,
    profile: str,
    model_tag: str,
    backend: str,
    split: str,
    metrics: EvalMetrics,
    duration_total_ms: int,
    plantnet: PlantNetReportSection | None = None,
    partial: bool = False,
    stopped_reason: str | None = None,
) -> EvalReport:
    observations = [_observation_row(row) for row in metrics.observations]
    failures = [
        FailureRow(
            image=row.image,
            ground_truth=row.ground_truth,
            predicted=row.predicted,
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

    return EvalReport(
        eval_run_id=eval_run_id,
        profile=profile,
        model_tag=model_tag,
        backend=backend,
        split=split,
        observation_count=metrics.observation_count,
        success_count=metrics.success_count,
        failure_count=metrics.failure_count,
        duration_total_ms=duration_total_ms,
        top1_accuracy=metrics.top1_accuracy,
        top3_accuracy=metrics.top3_accuracy,
        failures=failures,
        observations=observations,
        per_class=per_class,
        plantnet=plantnet,
        generated_at=datetime.now(tz=UTC).isoformat(),
        partial=partial,
        stopped_reason=stopped_reason,
    )


def write_report(report: EvalReport, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = report.model_dump(mode="json")
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return output_path
