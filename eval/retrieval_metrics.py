"""Retrieval ranking metrics (Recall@K, MRR)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class PrototypeHitRow:
    catalog_label: str
    prototype_kind: str | None = None
    prototype_id: str | None = None
    source_image: str | None = None
    score: float = 0.0


@dataclass(frozen=True)
class RetrievalPerClassStats:
    total: int
    recall_at_k: dict[int, float]


@dataclass(frozen=True)
class RetrievalObservationRow:
    image: str
    ground_truth: str
    retrieved_labels: tuple[str, ...]
    scores: tuple[float, ...]
    recall_at_k: dict[int, bool]
    reciprocal_rank: float
    error: str | None = None
    winning_prototypes: tuple[PrototypeHitRow, ...] = ()
    raw_hits: tuple[PrototypeHitRow, ...] = ()


@dataclass
class RetrievalMetrics:
    observation_count: int
    success_count: int
    failure_count: int
    recall_at_k: dict[int, float]
    mrr: float
    observations: list[RetrievalObservationRow] = field(default_factory=list)
    misses: list[RetrievalObservationRow] = field(default_factory=list)


def recall_at_k(retrieved: tuple[str, ...], ground_truth: str, k: int) -> bool:
    return ground_truth in retrieved[:k]


def reciprocal_rank(retrieved: tuple[str, ...], ground_truth: str) -> float:
    for index, label in enumerate(retrieved, start=1):
        if label == ground_truth:
            return 1.0 / index
    return 0.0


def compute_retrieval_metrics(
    rows: list[RetrievalObservationRow],
    *,
    k_values: tuple[int, ...] = (1, 3, 5),
) -> RetrievalMetrics:
    successful = [row for row in rows if row.error is None]
    failures = [row for row in rows if row.error is not None]
    recall_totals = {k: 0 for k in k_values}
    mrr_total = 0.0
    misses: list[RetrievalObservationRow] = []
    for row in successful:
        mrr_total += row.reciprocal_rank
        for k in k_values:
            if row.recall_at_k.get(k, False):
                recall_totals[k] += 1
        if not row.recall_at_k.get(max(k_values), False):
            misses.append(row)
    count = len(successful)
    recall_at_k_avg = {
        k: (recall_totals[k] / count if count else 0.0) for k in k_values
    }
    return RetrievalMetrics(
        observation_count=len(rows),
        success_count=count,
        failure_count=len(failures),
        recall_at_k=recall_at_k_avg,
        mrr=(mrr_total / count if count else 0.0),
        observations=rows,
        misses=misses,
    )


def compute_retrieval_per_class(
    rows: list[RetrievalObservationRow],
    *,
    k_values: tuple[int, ...] = (1, 3, 5),
) -> dict[str, RetrievalPerClassStats]:
    totals: dict[str, dict[int, int]] = {}
    counts: dict[str, int] = {}
    for row in rows:
        if row.error is not None:
            continue
        label = row.ground_truth
        counts[label] = counts.get(label, 0) + 1
        bucket = totals.setdefault(label, {k: 0 for k in k_values})
        for k in k_values:
            if row.recall_at_k.get(k, False):
                bucket[k] += 1
    per_class: dict[str, RetrievalPerClassStats] = {}
    for label, total in counts.items():
        hits = totals[label]
        per_class[label] = RetrievalPerClassStats(
            total=total,
            recall_at_k={
                k: (hits[k] / total if total else 0.0) for k in k_values
            },
        )
    return per_class
