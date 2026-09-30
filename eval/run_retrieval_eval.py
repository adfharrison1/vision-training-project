"""Run retrieval-only eval profiles."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime

from eval.dataset import EvalProfile, list_eval_images, resolve_profile
from eval.retrieval_failure_forensics import write_retrieval_failure_artifact
from eval.retrieval_metrics import (
    RetrievalObservationRow,
    compute_retrieval_metrics,
    recall_at_k,
    reciprocal_rank,
)
from eval.run_registry import (
    append_index_entry,
    capture_git_commit,
    ensure_run_dirs,
    eval_run_paths,
    index_entry_from_manifest,
    manifest_from_report,
    run_dir_exists,
    utc_now_iso,
    write_manifest,
)
from plant_id.infrastructure.species.file_catalog import FileSpeciesCatalog
from plant_id.interfaces.composition.container import load_settings
from plant_id.interfaces.composition.retrieval import RetrievalBackend, build_species_retrieval_repo


def default_eval_run_id() -> str:
    return datetime.now(tz=UTC).strftime("retrieval-%Y%m%d-%H%M%S")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run retrieval-only Oxford eval profiles.")
    parser.add_argument(
        "--profile",
        choices=[profile.value for profile in EvalProfile],
        default=EvalProfile.CURATED48.value,
    )
    parser.add_argument("--eval-run-id", default=None)
    parser.add_argument("--run-purpose", required=True)
    parser.add_argument(
        "--retrieval-backend",
        choices=["nemotron-prototype", "describe-hybrid"],
        default="nemotron-prototype",
    )
    parser.add_argument("--split", default="test")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument(
        "--top-k",
        type=int,
        default=None,
        help="Recall@K cutoff (default settings)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = load_settings()
    top_k = args.top_k or settings.retrieval_top_k
    eval_run_id = args.eval_run_id or default_eval_run_id()
    paths = eval_run_paths(settings.eval_runs_dir, eval_run_id)
    if run_dir_exists(paths):
        print(f"Eval run directory already exists: {paths.run_dir}", file=sys.stderr)
        return 1

    catalog = FileSpeciesCatalog(settings.species_catalog_path)
    class_names = catalog.list_class_names()
    images = list_eval_images(
        class_names=class_names,
        split=args.split,
        profile=args.profile,
        limit=args.limit,
    )
    backend: RetrievalBackend = args.retrieval_backend  # type: ignore[assignment]
    use_qdrant = backend == "nemotron-prototype"
    repo = build_species_retrieval_repo(backend, settings, use_qdrant=use_qdrant)

    started_at = utc_now_iso()
    rows: list[RetrievalObservationRow] = []
    k_values = (1, 3, 5)
    ensure_run_dirs(paths)

    for image in images:
        try:
            contexts = repo.retrieve((image.image_path,), top_k)
            labels = tuple(ctx.catalog_label for ctx in contexts)
            scores = tuple(ctx.score for ctx in contexts)
            row = RetrievalObservationRow(
                image=str(image.image_path),
                ground_truth=image.ground_truth,
                retrieved_labels=labels,
                scores=scores,
                recall_at_k={k: recall_at_k(labels, image.ground_truth, k) for k in k_values},
                reciprocal_rank=reciprocal_rank(labels, image.ground_truth),
            )
            rows.append(row)
            artifact = {
                "image": str(image.image_path),
                "ground_truth": image.ground_truth,
                "retrieval_backend": repo.backend_id,
                "top_k": top_k,
                "retrieved": [
                    {"catalog_label": ctx.catalog_label, "score": ctx.score}
                    for ctx in contexts
                ],
            }
            artifact_path = paths.artifacts_dir / f"{image.image_path.stem}.json"
            artifact_path.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
            if not row.recall_at_k.get(top_k, False):
                write_retrieval_failure_artifact(
                    paths.failures_dir,
                    image_path=image.image_path,
                    payload={
                        **artifact,
                        "failure_reason": f"ground_truth not in top-{top_k}",
                    },
                )
        except Exception as exc:
            rows.append(
                RetrievalObservationRow(
                    image=str(image.image_path),
                    ground_truth=image.ground_truth,
                    retrieved_labels=(),
                    scores=(),
                    recall_at_k={k: False for k in k_values},
                    reciprocal_rank=0.0,
                    error=str(exc),
                )
            )

    metrics = compute_retrieval_metrics(rows, k_values=k_values)
    finished_at = utc_now_iso()
    report_payload = {
        "eval_run_id": eval_run_id,
        "run_type": "retrieval",
        "run_purpose": args.run_purpose,
        "profile": resolve_profile(args.profile).value,
        "backend": args.retrieval_backend,
        "model_tag": repo.backend_id,
        "split": args.split,
        "observation_count": metrics.observation_count,
        "success_count": metrics.success_count,
        "failure_count": metrics.failure_count,
        "recall_at_k": metrics.recall_at_k,
        "mrr": metrics.mrr,
        "top_k": top_k,
        "failures": [
            {
                "image": row.image,
                "ground_truth": row.ground_truth,
                "retrieved_labels": list(row.retrieved_labels),
            }
            for row in metrics.misses
        ],
        "partial": False,
        "top1_accuracy_all": metrics.recall_at_k.get(1, 0.0),
        "top3_accuracy_all": metrics.recall_at_k.get(3, 0.0),
    }
    paths.report_path.parent.mkdir(parents=True, exist_ok=True)
    paths.report_path.write_text(json.dumps(report_payload, indent=2) + "\n", encoding="utf-8")

    git_commit = capture_git_commit()
    manifest = manifest_from_report(
        paths=paths,
        eval_runs_root=settings.eval_runs_dir,
        run_purpose=args.run_purpose,
        prompt_version=settings.prompt_version,
        started_at=started_at,
        finished_at=finished_at,
        git_commit=git_commit,
        report_payload=report_payload,
    )
    write_manifest(paths=paths, eval_runs_root=settings.eval_runs_dir, manifest=manifest)
    append_index_entry(settings.eval_runs_dir, index_entry_from_manifest(manifest))
    print(json.dumps(report_payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
