import json

from eval.retrieval_metrics import RetrievalMetrics, RetrievalObservationRow
from eval.retrieval_report import RUN_TYPE_RAG_RETRIEVAL_ONLY, build_retrieval_only_report
from eval.run_registry import manifest_from_report


def test_retrieval_only_report_has_no_identify_accuracy_aliases() -> None:
    metrics = RetrievalMetrics(
        observation_count=2,
        success_count=2,
        failure_count=0,
        recall_at_k={1: 0.5, 3: 1.0, 5: 1.0},
        mrr=0.75,
    )
    report = build_retrieval_only_report(
        eval_run_id="retrieval-test",
        run_purpose="unit test",
        git_commit=None,
        profile="smoke",
        split="test",
        backend="nemotron-prototype",
        model_tag="nemotron-prototype:test",
        metrics=metrics,
        top_k=3,
    )
    payload = json.loads(report.model_dump_json())
    assert payload["run_type"] == RUN_TYPE_RAG_RETRIEVAL_ONLY
    assert payload["retrieval"]["mrr"] == 0.75
    assert "top1_accuracy_all" not in payload
    assert "top3_accuracy_all" not in payload


def test_retrieval_only_report_includes_per_class_and_prototype_fields() -> None:
    metrics = RetrievalMetrics(
        observation_count=2,
        success_count=2,
        failure_count=0,
        recall_at_k={1: 0.5, 3: 1.0, 5: 1.0},
        mrr=0.75,
        observations=[
            RetrievalObservationRow(
                image="a.jpg",
                ground_truth="canterbury bells",
                retrieved_labels=("bolero deep blue",),
                scores=(0.9,),
                recall_at_k={1: False, 3: True},
                reciprocal_rank=0.5,
                winning_prototypes=(),
                raw_hits=(),
            ),
            RetrievalObservationRow(
                image="b.jpg",
                ground_truth="bolero deep blue",
                retrieved_labels=("bolero deep blue",),
                scores=(0.95,),
                recall_at_k={1: True, 3: True},
                reciprocal_rank=1.0,
            ),
        ],
    )
    report = build_retrieval_only_report(
        eval_run_id="retrieval-test",
        run_purpose="unit test",
        git_commit=None,
        profile="bolero_and_canterbury",
        split="test",
        backend="nemotron-prototype",
        model_tag="nemotron-prototype:test",
        metrics=metrics,
        top_k=3,
    )
    payload = json.loads(report.model_dump_json())
    assert payload["retrieval_per_class"]["canterbury bells"]["recall_at_k"]["1"] == 0.0
    assert payload["retrieval_per_class"]["bolero deep blue"]["recall_at_k"]["1"] == 1.0


def test_manifest_from_report_reads_retrieval_block(tmp_path) -> None:
    from eval.run_registry import eval_run_paths

    paths = eval_run_paths(tmp_path, "r1")
    payload = {
        "eval_run_id": "r1",
        "run_type": "rag_retrieval_only",
        "profile": "smoke",
        "backend": "nemotron-prototype",
        "model_tag": "nemotron-prototype:test",
        "split": "test",
        "observation_count": 4,
        "success_count": 4,
        "retrieval": {"recall_at_k": {1: 0.25, 3: 0.5}, "mrr": 0.3},
    }
    manifest = manifest_from_report(
        paths=paths,
        eval_runs_root=tmp_path,
        run_purpose="test",
        prompt_version="closed-set-v3",
        started_at="2026-01-01T00:00:00+00:00",
        finished_at="2026-01-01T00:01:00+00:00",
        git_commit=None,
        report_payload=payload,
    )
    assert manifest.run_type == "rag_retrieval_only"
    assert manifest.retrieval_recall_at_1 == 0.25
    assert manifest.retrieval_mrr == 0.3
