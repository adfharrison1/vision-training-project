"""Retrieval sections for eval JSON reports."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field

from eval.retrieval_metrics import RetrievalMetrics, RetrievalObservationRow

RUN_TYPE_FULL_IDENTIFY = "full_identify"
RUN_TYPE_RAG_RETRIEVAL_ONLY = "rag_retrieval_only"


class RetrievalReportSection(BaseModel):
    model_config = ConfigDict(frozen=True)

    backend: str
    model_tag: str
    top_k: int
    recall_at_k: dict[int, float]
    mrr: float
    rag_enabled_for_identify: bool | None = None


class RetrievalObservationReportRow(BaseModel):
    model_config = ConfigDict(frozen=True)

    image: str
    ground_truth: str
    retrieved_labels: tuple[str, ...]
    scores: tuple[float, ...]
    recall_at_k: dict[int, bool]
    reciprocal_rank: float
    error: str | None = None


class RetrievalFailureRow(BaseModel):
    model_config = ConfigDict(frozen=True)

    image: str
    ground_truth: str
    retrieved_labels: tuple[str, ...]
    error: str | None = None


class RetrievalOnlyEvalReport(BaseModel):
    """Retrieval-only eval report (no VLM identify metrics)."""

    model_config = ConfigDict(frozen=True)

    eval_run_id: str
    run_type: str = RUN_TYPE_RAG_RETRIEVAL_ONLY
    run_purpose: str
    git_commit: str | None = None
    profile: str
    split: str
    backend: str
    model_tag: str
    observation_count: int
    success_count: int
    failure_count: int
    partial: bool = False
    generated_at: str
    retrieval: RetrievalReportSection
    retrieval_observations: list[RetrievalObservationReportRow] = Field(default_factory=list)
    failures: list[RetrievalFailureRow] = Field(default_factory=list)


def _observation_report_row(row: RetrievalObservationRow) -> RetrievalObservationReportRow:
    return RetrievalObservationReportRow(
        image=row.image,
        ground_truth=row.ground_truth,
        retrieved_labels=row.retrieved_labels,
        scores=row.scores,
        recall_at_k=row.recall_at_k,
        reciprocal_rank=row.reciprocal_rank,
        error=row.error,
    )


def _failure_row(row: RetrievalObservationRow) -> RetrievalFailureRow:
    return RetrievalFailureRow(
        image=row.image,
        ground_truth=row.ground_truth,
        retrieved_labels=row.retrieved_labels,
        error=row.error,
    )


def build_retrieval_section(
    metrics: RetrievalMetrics,
    *,
    backend: str,
    model_tag: str,
    top_k: int,
    rag_enabled_for_identify: bool | None = None,
) -> RetrievalReportSection:
    return RetrievalReportSection(
        backend=backend,
        model_tag=model_tag,
        top_k=top_k,
        recall_at_k=metrics.recall_at_k,
        mrr=metrics.mrr,
        rag_enabled_for_identify=rag_enabled_for_identify,
    )


def build_retrieval_report_extras(
    metrics: RetrievalMetrics,
    *,
    backend: str,
    model_tag: str,
    top_k: int,
    rag_enabled_for_identify: bool | None = None,
) -> tuple[
    RetrievalReportSection,
    list[RetrievalObservationReportRow],
    list[RetrievalFailureRow],
]:
    section = build_retrieval_section(
        metrics,
        backend=backend,
        model_tag=model_tag,
        top_k=top_k,
        rag_enabled_for_identify=rag_enabled_for_identify,
    )
    observations = [_observation_report_row(row) for row in metrics.observations]
    failures = [_failure_row(row) for row in metrics.misses]
    for row in metrics.observations:
        if row.error is not None:
            failures.append(_failure_row(row))
    return section, observations, failures


def build_retrieval_only_report(
    *,
    eval_run_id: str,
    run_purpose: str,
    git_commit: str | None,
    profile: str,
    split: str,
    backend: str,
    model_tag: str,
    metrics: RetrievalMetrics,
    top_k: int,
    partial: bool = False,
) -> RetrievalOnlyEvalReport:
    section, observations, failures = build_retrieval_report_extras(
        metrics,
        backend=backend,
        model_tag=model_tag,
        top_k=top_k,
    )
    return RetrievalOnlyEvalReport(
        eval_run_id=eval_run_id,
        run_purpose=run_purpose,
        git_commit=git_commit,
        profile=profile,
        split=split,
        backend=backend,
        model_tag=model_tag,
        observation_count=metrics.observation_count,
        success_count=metrics.success_count,
        failure_count=metrics.failure_count,
        partial=partial,
        generated_at=datetime.now(tz=UTC).isoformat(),
        retrieval=section,
        retrieval_observations=observations,
        failures=failures,
    )


def write_retrieval_only_report(report: RetrievalOnlyEvalReport, output_path) -> None:
    from pathlib import Path

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report.model_dump_json(indent=2) + "\n", encoding="utf-8")
