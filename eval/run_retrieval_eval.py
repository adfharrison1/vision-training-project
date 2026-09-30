"""Run retrieval-only eval profiles."""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime

from eval.dataset import EvalProfile, list_eval_images, resolve_profile
from eval.eval_run_roots import rag_retrieval_only_eval_runs_root
from eval.retrieval_report import build_retrieval_only_report, write_retrieval_only_report
from eval.retrieval_scoring import score_retrieval_observations
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
        default=EvalProfile.BOLERO_AND_CANTERBURY.value,
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
    eval_runs_root = rag_retrieval_only_eval_runs_root(settings)
    paths = eval_run_paths(eval_runs_root, eval_run_id)
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
    ensure_run_dirs(paths)

    metrics = score_retrieval_observations(
        repo,
        images,
        top_k=top_k,
        artifacts_dir=paths.artifacts_dir,
        failures_dir=paths.failures_dir,
    )

    git_commit = capture_git_commit()
    report = build_retrieval_only_report(
        eval_run_id=eval_run_id,
        run_purpose=args.run_purpose,
        git_commit=git_commit,
        profile=resolve_profile(args.profile).value,
        split=args.split,
        backend=backend,
        model_tag=repo.backend_id,
        metrics=metrics,
        top_k=top_k,
    )
    write_retrieval_only_report(report, paths.report_path)

    finished_at = utc_now_iso()
    report_payload = report.model_dump(mode="json")
    manifest = manifest_from_report(
        paths=paths,
        eval_runs_root=eval_runs_root,
        run_purpose=args.run_purpose,
        prompt_version=settings.prompt_version,
        started_at=started_at,
        finished_at=finished_at,
        git_commit=git_commit,
        report_payload=report_payload,
    )
    write_manifest(paths=paths, eval_runs_root=eval_runs_root, manifest=manifest)
    append_index_entry(eval_runs_root, index_entry_from_manifest(manifest))
    print(report.model_dump_json(indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
