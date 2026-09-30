"""Run Oxford 102 eval profiles against local identification backends."""

from __future__ import annotations

import argparse
import re
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

from eval.baselines.plantnet import identify_image, plantnet_api_key
from eval.dataset import EvalProfile, list_eval_images, resolve_profile
from eval.eval_run_roots import full_identify_eval_runs_root
from eval.failure_forensics import (
    ensure_eval_failure_forensics,
    eval_failures_dir,
    write_eval_failure_artifact,
)
from eval.inference_usage import aggregate_token_usage, usage_from_identification_raw
from eval.metrics import (
    ObservationResultRow,
    compute_metrics,
    top1_correct,
    top3_correct,
)
from eval.report import (
    InferenceReportSection,
    ObservationReportRow,
    PlantNetReportSection,
    build_report,
    write_report,
)
from eval.retrieval_report import build_retrieval_report_extras
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
from plant_id.infrastructure.observability.opik_tracing import eval_trace_session
from plant_id.infrastructure.species.file_catalog import FileSpeciesCatalog
from plant_id.interfaces.composition import execute_identify, load_settings, resolve_settings
from plant_id.interfaces.composition.container import Backend
from plant_id.interfaces.composition.retrieval import RetrievalBackend, build_species_retrieval_repo

_DURATION_PATTERN = re.compile(
    r"^(?:(?P<hours>\d+)h)?(?:(?P<minutes>\d+)m)?(?:(?P<seconds>\d+)s?)?$",
    re.IGNORECASE,
)


def parse_duration_budget(text: str) -> int:
    """Parse a duration string such as ``30m`` or ``1h30m`` into milliseconds."""
    normalized = text.strip().lower()
    if not normalized:
        raise ValueError("Duration budget must not be empty.")

    match = _DURATION_PATTERN.fullmatch(normalized)
    if match is None:
        raise ValueError(
            f"Invalid duration {text!r}; expected forms like 30m, 90s, or 1h30m."
        )

    hours = int(match.group("hours") or 0)
    minutes = int(match.group("minutes") or 0)
    seconds = int(match.group("seconds") or 0)
    total_seconds = hours * 3600 + minutes * 60 + seconds
    if total_seconds <= 0:
        raise ValueError(f"Duration budget must be positive (got {text!r}).")
    return total_seconds * 1000


def default_eval_run_id() -> str:
    return datetime.now(tz=UTC).strftime("eval-%Y%m%d-%H%M%S")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run Oxford 102 eval profiles against local backends.",
    )
    parser.add_argument(
        "--profile",
        choices=[profile.value for profile in EvalProfile],
        default=EvalProfile.QUICK.value,
        help="Eval profile (default: quick)",
    )
    parser.add_argument(
        "--eval-run-id",
        default=None,
        help="Correlation id for report and Opik traces (default: timestamp slug)",
    )
    parser.add_argument(
        "--run-purpose",
        required=True,
        help="Non-empty human-readable reason for this eval run (required)",
    )
    parser.add_argument(
        "--backend",
        choices=["vlm", "vlm-cloud", "classical"],
        default="vlm-cloud",
        help="Identification backend wired through composition (default: vlm-cloud)",
    )
    parser.add_argument(
        "--split",
        default="test",
        help="Oxford split name (train, validation, test)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Override profile image count",
    )
    parser.add_argument(
        "--max-duration",
        default=None,
        help="Stop when budget exceeded, e.g. 30m",
    )
    parser.add_argument(
        "--quiet",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Suppress Rich progress output (default: true)",
    )
    parser.add_argument(
        "--dataset-root",
        type=Path,
        default=None,
        help="Oxford 102 dataset root (default: data/flowers)",
    )
    parser.add_argument(
        "--profile-manifest",
        type=Path,
        default=None,
        help=(
            "YAML manifest of species/image pairs for smoke and quick "
            "(default: eval/profiles/quick.yaml)"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Report output path (default: eval_runs/<run-id>/eval/report.json)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Allow reusing an existing eval_runs/<run-id> directory",
    )
    parser.add_argument(
        "--plantnet-baseline",
        action="store_true",
        help="Include optional Pl@ntNet baseline metrics",
    )
    parser.add_argument(
        "--rag",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Enable species RAG prompt injection (default: PLANT_ID_RAG_ENABLED).",
    )
    parser.add_argument(
        "--think",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            "Enable Ollama thinking mode for this eval run "
            "(default: false, or PLANT_ID_OLLAMA_THINK)."
        ),
    )
    parser.add_argument(
        "--retrieval-backend",
        choices=["nemotron-prototype", "describe-hybrid"],
        default="nemotron-prototype",
        help="Backend for retrieval metrics scored after identify (default: nemotron-prototype)",
    )
    return parser


def _report_model_tag(settings, backend: Backend) -> str:
    if backend == "vlm-cloud":
        return settings.vlm_cloud_model
    return settings.vision_model


def _inference_section(
    settings,
    backend: Backend,
    rows: list[ObservationResultRow],
) -> InferenceReportSection:
    cloud_host = None
    if backend == "vlm-cloud":
        cloud_host = urlparse(settings.vlm_cloud_base_url).netloc or None
    per_observation: list[dict[str, int] | None] = []
    for row in rows:
        if row.prompt_tokens is None and row.completion_tokens is None and row.total_tokens is None:
            per_observation.append(None)
            continue
        per_observation.append(
            {
                "prompt_tokens": row.prompt_tokens or 0,
                "completion_tokens": row.completion_tokens or 0,
                "total_tokens": row.total_tokens or 0,
            }
        )
    return InferenceReportSection(
        backend=backend,
        model=_report_model_tag(settings, backend),
        prompt_version=settings.prompt_version,
        cloud_vendor=settings.vlm_cloud_vendor if backend == "vlm-cloud" else None,
        cloud_base_url_host=cloud_host,
        usage=aggregate_token_usage(per_observation),
    )


def _observation_id(eval_run_id: str, image_path: Path) -> str:
    return f"eval-{eval_run_id}-{image_path.stem}"


def _run_local_observation(
    *,
    backend: Backend,
    image_path: Path,
    ground_truth: str,
    eval_run_id: str,
    profile: str,
    settings,
    artifact_dir: Path,
    eval_runs_root: Path,
) -> ObservationResultRow:
    observation_id = _observation_id(eval_run_id, image_path)
    started = time.perf_counter()
    with eval_trace_session(
        eval_run_id,
        profile,
        ground_truth=ground_truth,
    ) as session:
        outcome = execute_identify(
            backend,
            [image_path],
            observation_id,
            settings,
            artifact_dir=artifact_dir,
        )
        trace_id = session.trace_id

    duration_ms = int((time.perf_counter() - started) * 1000)
    usage = usage_from_identification_raw(getattr(outcome, "identification_raw", None))

    def _token_fields() -> dict[str, int | None]:
        if usage is None:
            return {
                "prompt_tokens": None,
                "completion_tokens": None,
                "total_tokens": None,
            }
        return {
            "prompt_tokens": usage["prompt_tokens"],
            "completion_tokens": usage["completion_tokens"],
            "total_tokens": usage["total_tokens"],
        }

    tokens = _token_fields()
    if outcome.error_message or outcome.result is None:
        error = outcome.error_message or "Identification returned no result."
        write_eval_failure_artifact(
            eval_run_id=eval_run_id,
            image=image_path.name,
            ground_truth=ground_truth,
            observation_id=observation_id,
            failure_kind="parse",
            error=error,
            trace_id=trace_id,
            identification_raw=outcome.identification_raw,
            eval_runs_root=eval_runs_root,
        )
        return ObservationResultRow(
            image=image_path.name,
            ground_truth=ground_truth,
            predicted=None,
            top1_match=False,
            top3_match=False,
            duration_ms=duration_ms,
            observation_id=observation_id,
            trace_id=trace_id,
            error=error,
            **tokens,
        )

    predictions = tuple(prediction.species_label for prediction in outcome.result.predictions)
    predicted = predictions[0] if predictions else None
    top1 = top1_correct(predictions, ground_truth)
    top3 = top3_correct(predictions, ground_truth)
    if not top1:
        write_eval_failure_artifact(
            eval_run_id=eval_run_id,
            image=image_path.name,
            ground_truth=ground_truth,
            observation_id=observation_id,
            failure_kind="misclassification",
            trace_id=trace_id,
            identification_raw=outcome.identification_raw,
            eval_runs_root=eval_runs_root,
            predicted=predicted,
            predictions=predictions,
            top3_match=top3,
        )
    return ObservationResultRow(
        image=image_path.name,
        ground_truth=ground_truth,
        predicted=predicted,
        top1_match=top1,
        top3_match=top3,
        duration_ms=duration_ms,
        observation_id=observation_id,
        trace_id=trace_id,
        predictions=predictions,
        **tokens,
    )


def _run_plantnet_observation(
    image_path: Path,
    ground_truth: str,
    eval_run_id: str,
    class_names: list[str],
) -> ObservationReportRow:
    observation_id = _observation_id(eval_run_id, image_path)
    started = time.perf_counter()
    result = identify_image(image_path, class_names=class_names)
    duration_ms = int((time.perf_counter() - started) * 1000)
    if result.error:
        return ObservationReportRow(
            image=image_path.name,
            ground_truth=ground_truth,
            predicted=result.raw_best_match,
            top1_match=False,
            top3_match=False,
            duration_ms=duration_ms,
            observation_id=observation_id,
            error=result.error,
            predictions=result.labels,
        )

    predicted = result.labels[0] if result.labels else result.raw_best_match
    return ObservationReportRow(
        image=image_path.name,
        ground_truth=ground_truth,
        predicted=predicted,
        top1_match=top1_correct(result.labels, ground_truth),
        top3_match=top3_correct(result.labels, ground_truth),
        duration_ms=duration_ms,
        observation_id=observation_id,
        predictions=result.labels,
    )


def run_eval(args: argparse.Namespace) -> int:
    settings = resolve_settings(load_settings(), ollama_think=args.think)
    if getattr(args, "rag", None) is not None:
        settings = settings.model_copy(update={"rag_enabled": args.rag})
    run_purpose = (args.run_purpose or "").strip()
    if not run_purpose:
        print("--run-purpose must be a non-empty string.", file=sys.stderr)
        return 1

    eval_run_id = args.eval_run_id or default_eval_run_id()
    profile = resolve_profile(args.profile).value
    backend: Backend = args.backend
    eval_runs_root = full_identify_eval_runs_root(settings)
    paths = eval_run_paths(eval_runs_root, eval_run_id)

    if run_dir_exists(paths) and not args.force:
        print(
            f"Eval run directory already exists: {paths.run_dir}\n"
            "Use --force to reuse or choose a new --eval-run-id.",
            file=sys.stderr,
        )
        return 1

    ensure_run_dirs(paths)
    started_at = utc_now_iso()
    git_commit = capture_git_commit()

    catalog = FileSpeciesCatalog(settings.species_catalog_path)
    class_names = catalog.list_class_names()

    try:
        images = list_eval_images(
            class_names=class_names,
            split=args.split,
            profile=profile,
            limit=args.limit,
            dataset_root=args.dataset_root,
            profile_manifest=args.profile_manifest,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    max_duration_ms = parse_duration_budget(args.max_duration) if args.max_duration else None
    rows: list[ObservationResultRow] = []
    plantnet_rows: list[ObservationReportRow] = []
    plantnet_section: PlantNetReportSection | None = None
    run_started = time.perf_counter()
    stopped_reason: str | None = None

    if args.plantnet_baseline:
        api_key = plantnet_api_key()
        if api_key is None:
            print(
                "Pl@ntNet baseline skipped: PLANTNET_API_KEY is not configured.",
                file=sys.stderr,
            )
            plantnet_section = PlantNetReportSection(
                enabled=False,
                skipped_reason="PLANTNET_API_KEY is not configured.",
            )
        else:
            plantnet_section = PlantNetReportSection(enabled=True)

    for index, image in enumerate(images, start=1):
        elapsed_ms = int((time.perf_counter() - run_started) * 1000)
        if max_duration_ms is not None and elapsed_ms >= max_duration_ms:
            stopped_reason = f"max-duration exceeded after {index - 1} observation(s)"
            break

        if not args.quiet:
            print(f"[{index}/{len(images)}] {image.image_path.name}", file=sys.stderr)

        row = _run_local_observation(
            backend=backend,
            image_path=image.image_path,
            ground_truth=image.ground_truth,
            eval_run_id=eval_run_id,
            profile=profile,
            settings=settings,
            artifact_dir=paths.artifacts_dir,
            eval_runs_root=eval_runs_root,
        )
        rows.append(row)

        if plantnet_section is not None and plantnet_section.enabled:
            plantnet_row = _run_plantnet_observation(
                image.image_path,
                image.ground_truth,
                eval_run_id,
                class_names,
            )
            plantnet_rows.append(plantnet_row)

    duration_total_ms = int((time.perf_counter() - run_started) * 1000)
    ensure_eval_failure_forensics(
        eval_run_id=eval_run_id,
        rows=rows,
        artifacts_dir=paths.artifacts_dir,
        eval_runs_root=eval_runs_root,
    )
    metrics = compute_metrics(rows)
    partial = stopped_reason is not None or len(rows) < len(images)

    if plantnet_section is not None and plantnet_section.enabled:
        plantnet_metrics_rows = [
            ObservationResultRow(
                image=row.image,
                ground_truth=row.ground_truth,
                predicted=row.predicted,
                top1_match=row.top1_match,
                top3_match=row.top3_match,
                duration_ms=row.duration_ms,
                observation_id=row.observation_id,
                error=row.error,
                predictions=row.predictions,
            )
            for row in plantnet_rows
        ]
        plantnet_metrics = compute_metrics(plantnet_metrics_rows)
        plantnet_section = PlantNetReportSection(
            enabled=True,
            observation_count=plantnet_metrics.observation_count,
            success_count=plantnet_metrics.success_count,
            failure_count=plantnet_metrics.failure_count,
            top1_accuracy=plantnet_metrics.top1_accuracy,
            top3_accuracy=plantnet_metrics.top3_accuracy,
            observations=plantnet_rows,
        )

    retrieval_backend: RetrievalBackend = args.retrieval_backend  # type: ignore[assignment]
    top_k = settings.retrieval_top_k
    use_qdrant = retrieval_backend == "nemotron-prototype"
    retrieval_repo = build_species_retrieval_repo(
        retrieval_backend,
        settings,
        use_qdrant=use_qdrant,
    )
    scored_images = images[: len(rows)]
    retrieval_metrics = score_retrieval_observations(
        retrieval_repo,
        scored_images,
        top_k=top_k,
        artifacts_dir=None,
        failures_dir=None,
    )
    retrieval_section, retrieval_observations, retrieval_failures, retrieval_per_class = (
        build_retrieval_report_extras(
            retrieval_metrics,
            backend=retrieval_backend,
            model_tag=retrieval_repo.backend_id,
            top_k=top_k,
            rag_enabled_for_identify=settings.rag_enabled,
        )
    )

    report = build_report(
        eval_run_id=eval_run_id,
        run_purpose=run_purpose,
        git_commit=git_commit,
        profile=profile,
        model_tag=_report_model_tag(settings, backend),
        backend=backend,
        split=args.split,
        metrics=metrics,
        duration_total_ms=duration_total_ms,
        plantnet=plantnet_section,
        partial=partial,
        stopped_reason=stopped_reason,
        inference=_inference_section(settings, backend, rows),
        failure_artifacts_dir=eval_failures_dir(eval_run_id, eval_runs_root=eval_runs_root)
        if metrics.parse_failure_count or metrics.misclassification_count
        else None,
        eval_runs_root=eval_runs_root,
        retrieval=retrieval_section,
        retrieval_observations=retrieval_observations,
        retrieval_failures=retrieval_failures,
        retrieval_per_class=retrieval_per_class,
    )
    output_path = args.output or paths.report_path
    write_report(report, output_path)

    finished_at = utc_now_iso()
    report_payload = report.model_dump(mode="json")
    manifest = manifest_from_report(
        paths=paths,
        eval_runs_root=eval_runs_root,
        run_purpose=run_purpose,
        prompt_version=settings.prompt_version,
        started_at=started_at,
        finished_at=finished_at,
        git_commit=git_commit,
        report_payload=report_payload,
    )
    write_manifest(
        paths=paths,
        eval_runs_root=eval_runs_root,
        manifest=manifest,
    )
    append_index_entry(eval_runs_root, index_entry_from_manifest(manifest))

    if not args.quiet:
        print(f"Report written: {output_path}", file=sys.stderr)
        usage_line = ""
        if report.inference is not None and report.inference.usage is not None:
            usage = report.inference.usage
            usage_line = (
                f" tokens={usage.total_tokens} "
                f"(prompt={usage.prompt_tokens} completion={usage.completion_tokens})"
            )
        benchmark_misses = metrics.parse_failure_count + metrics.misclassification_count
        print(
            f"top-1={report.top1_accuracy:.3f} (success) / "
            f"{report.top1_accuracy_all:.3f} (all) "
            f"top-3={report.top3_accuracy:.3f} (success) / "
            f"{report.top3_accuracy_all:.3f} (all) "
            f"benchmark_misses={benchmark_misses} "
            f"(parse={report.parse_failure_count} misclass={report.misclassification_count}) "
            f"parsed_ok={report.success_count}/{report.observation_count}{usage_line}",
            file=sys.stderr,
        )
        if report.failure_artifacts_dir:
            print(
                f"Failure forensics: {report.failure_artifacts_dir}/",
                file=sys.stderr,
            )
        print(
            f"retrieval Recall@1={report.retrieval.recall_at_k.get(1, 0.0):.3f} "
            f"MRR={report.retrieval.mrr:.3f} "
            f"(backend={report.retrieval.backend}, rag_for_identify={settings.rag_enabled})",
            file=sys.stderr,
        )

    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return run_eval(args)


if __name__ == "__main__":
    sys.exit(main())
