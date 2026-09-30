"""Unit tests for retrieval scoring and metrics."""

from __future__ import annotations

from eval.retrieval_metrics import (
    RetrievalObservationRow,
    compute_retrieval_metrics,
    recall_at_k,
    reciprocal_rank,
)

from plant_id.infrastructure.retrieval.scoring import aggregate_max_per_label


def test_aggregate_max_per_label() -> None:
    hits = [
        ({"catalog_label": "a", "context_block": "A"}, 0.2),
        ({"catalog_label": "a", "context_block": "A"}, 0.9),
        ({"catalog_label": "b", "context_block": "B"}, 0.5),
    ]
    ranked = aggregate_max_per_label(hits, k=2)
    assert [item.catalog_label for item in ranked] == ["a", "b"]
    assert ranked[0].score == 0.9


def test_recall_and_mrr() -> None:
    assert recall_at_k(("x", "y"), "y", 2)
    assert reciprocal_rank(("x", "y"), "y") == 0.5
    row = RetrievalObservationRow(
        image="image_00001.jpg",
        ground_truth="y",
        retrieved_labels=("x", "y"),
        scores=(0.1, 0.2),
        recall_at_k={1: False, 3: True},
        reciprocal_rank=0.5,
    )
    metrics = compute_retrieval_metrics([row], k_values=(1, 3))
    assert metrics.mrr == 0.5
    assert metrics.recall_at_k[3] == 1.0
