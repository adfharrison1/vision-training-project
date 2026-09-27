"""Accuracy metrics for Oxford 102 eval runs."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ObservationResultRow:
    image: str
    ground_truth: str
    predicted: str | None
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


@dataclass
class PerClassMetrics:
    total: int
    top1: int
    top3: int


@dataclass
class EvalMetrics:
    observation_count: int
    success_count: int
    failure_count: int
    parse_failure_count: int
    misclassification_count: int
    top1_accuracy: float
    top3_accuracy: float
    top1_accuracy_all: float
    top3_accuracy_all: float
    per_class: dict[str, PerClassMetrics] = field(default_factory=dict)
    observations: list[ObservationResultRow] = field(default_factory=list)
    failures: list[ObservationResultRow] = field(default_factory=list)


def labels_match(predicted: str, ground_truth: str) -> bool:
    return predicted == ground_truth


def top1_correct(predictions: tuple[str, ...], ground_truth: str) -> bool:
    if not predictions:
        return False
    return labels_match(predictions[0], ground_truth)


def top3_correct(predictions: tuple[str, ...], ground_truth: str) -> bool:
    return any(labels_match(label, ground_truth) for label in predictions[:3])


def compute_metrics(rows: list[ObservationResultRow]) -> EvalMetrics:
    successful = [row for row in rows if row.error is None]
    failures = [row for row in rows if row.error is not None]

    per_class: dict[str, PerClassMetrics] = {}
    top1_hits = 0
    top3_hits = 0

    for row in successful:
        stats = per_class.setdefault(
            row.ground_truth,
            PerClassMetrics(total=0, top1=0, top3=0),
        )
        stats.total += 1
        if row.top1_match:
            top1_hits += 1
            stats.top1 += 1
        if row.top3_match:
            top3_hits += 1
            stats.top3 += 1

    success_count = len(successful)
    observation_count = len(rows)
    top1_accuracy = top1_hits / success_count if success_count else 0.0
    top3_accuracy = top3_hits / success_count if success_count else 0.0

    top1_hits_all = sum(1 for row in rows if row.top1_match)
    top3_hits_all = sum(1 for row in rows if row.top3_match)
    top1_accuracy_all = top1_hits_all / observation_count if observation_count else 0.0
    top3_accuracy_all = top3_hits_all / observation_count if observation_count else 0.0

    misclassification_count = sum(1 for row in successful if not row.top1_match)

    return EvalMetrics(
        observation_count=observation_count,
        success_count=success_count,
        failure_count=len(failures),
        parse_failure_count=len(failures),
        misclassification_count=misclassification_count,
        top1_accuracy=top1_accuracy,
        top3_accuracy=top3_accuracy,
        top1_accuracy_all=top1_accuracy_all,
        top3_accuracy_all=top3_accuracy_all,
        per_class=per_class,
        observations=rows,
        failures=failures,
    )
