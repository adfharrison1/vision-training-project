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
    default_report_path,
    write_report,
)
from plant_id.infrastructure.observability.opik_tracing import eval_trace_session
from plant_id.infrastructure.species.file_catalog import FileSpeciesCatalog
from plant_id.interfaces.composition import execute_identify, load_settings, resolve_settings
from plant_id.interfaces.composition.container import Backend

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
        help="Report output path (default: artifacts/eval/<timestamp>-<run-id>.json)",
    )
    parser.add_argument(
        "--plantnet-baseline",
        action="store_true",
        help="Include optional Pl@ntNet baseline metrics",
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
        return ObservationResultRow(
            image=image_path.name,
            ground_truth=ground_truth,
            predicted=None,
            top1_match=False,
            top3_match=False,
            duration_ms=duration_ms,
            observation_id=observation_id,
            trace_id=trace_id,
            error=outcome.error_message or "Identification returned no result.",
            **tokens,
        )

    predictions = tuple(prediction.species_label for prediction in outcome.result.predictions)
    predicted = predictions[0] if predictions else None
    return ObservationResultRow(
        image=image_path.name,
        ground_truth=ground_truth,
        predicted=predicted,
        top1_match=top1_correct(predictions, ground_truth),
        top3_match=top3_correct(predictions, ground_truth),
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
    eval_run_id = args.eval_run_id or default_eval_run_id()
    profile = resolve_profile(args.profile).value
    backend: Backend = args.backend

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

    report = build_report(
        eval_run_id=eval_run_id,
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
    )
    output_path = args.output or default_report_path(eval_run_id)
    write_report(report, output_path)

    if not args.quiet:
        print(f"Report written: {output_path}", file=sys.stderr)
        usage_line = ""
        if report.inference is not None and report.inference.usage is not None:
            usage = report.inference.usage
            usage_line = (
                f" tokens={usage.total_tokens} "
                f"(prompt={usage.prompt_tokens} completion={usage.completion_tokens})"
            )
        print(
            f"top-1={report.top1_accuracy:.3f} top-3={report.top3_accuracy:.3f} "
            f"({report.success_count}/{report.observation_count} succeeded){usage_line}",
            file=sys.stderr,
        )

    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return run_eval(args)


if __name__ == "__main__":
    sys.exit(main())
