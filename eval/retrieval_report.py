"""Retrieval sections for eval JSON reports."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field

from eval.retrieval_metrics import (
    RetrievalMetrics,
    RetrievalObservationRow,
    RetrievalPerClassStats,
    compute_retrieval_per_class,
)

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


class PrototypeHitReportRow(BaseModel):
    model_config = ConfigDict(frozen=True)

    catalog_label: str
    prototype_kind: str | None = None
    prototype_id: str | None = None
    source_image: str | None = None
    score: float = 0.0


class RetrievalPerClassReportRow(BaseModel):
    model_config = ConfigDict(frozen=True)

    total: int
    recall_at_k: dict[int, float]


class RetrievalObservationReportRow(BaseModel):
    model_config = ConfigDict(frozen=True)

    image: str
    ground_truth: str
    retrieved_labels: tuple[str, ...]
    scores: tuple[float, ...]
    recall_at_k: dict[int, bool]
    reciprocal_rank: float
    error: str | None = None
    winning_prototypes: tuple[PrototypeHitReportRow, ...] = ()
    raw_hits: tuple[PrototypeHitReportRow, ...] = ()


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
    retrieval_per_class: dict[str, RetrievalPerClassReportRow] = Field(default_factory=dict)
    failures: list[RetrievalFailureRow] = Field(default_factory=list)


def _prototype_hit_row(row) -> PrototypeHitReportRow:
    return PrototypeHitReportRow(
        catalog_label=row.catalog_label,
        prototype_kind=row.prototype_kind,
        prototype_id=row.prototype_id,
        source_image=row.source_image,
        score=row.score,
    )


def _observation_report_row(row: RetrievalObservationRow) -> RetrievalObservationReportRow:
    return RetrievalObservationReportRow(
        image=row.image,
        ground_truth=row.ground_truth,
        retrieved_labels=row.retrieved_labels,
        scores=row.scores,
        recall_at_k=row.recall_at_k,
        reciprocal_rank=row.reciprocal_rank,
        error=row.error,
        winning_prototypes=tuple(_prototype_hit_row(hit) for hit in row.winning_prototypes),
        raw_hits=tuple(_prototype_hit_row(hit) for hit in row.raw_hits),
    )


def _per_class_report(
    stats: dict[str, RetrievalPerClassStats],
) -> dict[str, RetrievalPerClassReportRow]:
    return {
        label: RetrievalPerClassReportRow(total=entry.total, recall_at_k=entry.recall_at_k)
        for label, entry in stats.items()
    }


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
    dict[str, RetrievalPerClassReportRow],
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
    per_class = _per_class_report(compute_retrieval_per_class(metrics.observations))
    return section, observations, failures, per_class


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
    section, observations, failures, per_class = build_retrieval_report_extras(
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
        retrieval_per_class=per_class,
        failures=failures,
    )


def write_retrieval_only_report(report: RetrievalOnlyEvalReport, output_path) -> None:
    from pathlib import Path

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report.model_dump_json(indent=2) + "\n", encoding="utf-8")
