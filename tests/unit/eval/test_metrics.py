from eval.metrics import (
    ObservationResultRow,
    compute_metrics,
    labels_match,
    top1_correct,
    top3_correct,
)


def test_labels_match_is_exact_and_case_sensitive() -> None:
    assert labels_match("tiger lily", "tiger lily")
    assert not labels_match("Tiger lily", "tiger lily")


def test_top_k_metrics_with_synthetic_rows() -> None:
    rows = [
        ObservationResultRow(
            image="image_00001.jpg",
            ground_truth="tiger lily",
            predicted="tiger lily",
            top1_match=True,
            top3_match=True,
            duration_ms=100,
            observation_id="obs-1",
            predictions=("tiger lily", "english marigold"),
        ),
        ObservationResultRow(
            image="image_00002.jpg",
            ground_truth="sweet pea",
            predicted="english marigold",
            top1_match=False,
            top3_match=True,
            duration_ms=120,
            observation_id="obs-2",
            predictions=("english marigold", "sweet pea"),
        ),
        ObservationResultRow(
            image="image_00003.jpg",
            ground_truth="snapdragon",
            predicted=None,
            top1_match=False,
            top3_match=False,
            duration_ms=50,
            observation_id="obs-3",
            error="Identification failed",
        ),
    ]

    metrics = compute_metrics(rows)
    assert metrics.observation_count == 3
    assert metrics.success_count == 2
    assert metrics.failure_count == 1
    assert metrics.parse_failure_count == 1
    assert metrics.misclassification_count == 1
    assert metrics.top1_accuracy == 0.5
    assert metrics.top3_accuracy == 1.0
    assert metrics.top1_accuracy_all == 1 / 3
    assert metrics.top3_accuracy_all == 2 / 3
    assert metrics.per_class["tiger lily"].top1 == 1
    assert metrics.per_class["sweet pea"].top3 == 1


def test_top_helpers() -> None:
    assert top1_correct(("a", "b"), "a")
    assert top3_correct(("x", "y", "a"), "a")
    assert not top1_correct(("x",), "a")
