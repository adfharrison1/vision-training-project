"""Compare an identification result to Oxford 102 ground truth."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from eval.oxford102_ground_truth import default_labels_mat_path, ground_truth_species_label
from plant_id.domain.models import Observation
from plant_id.infrastructure.composition.container import build_identify_use_case
from plant_id.infrastructure.config.settings import Settings
from plant_id.infrastructure.species.file_catalog import FileSpeciesCatalog
from plant_id.interfaces.cli.progress import identification_progress


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Look up Oxford 102 ground truth for an image file.",
    )
    parser.add_argument(
        "photo",
        type=Path,
        help="Path to image_XXXXX.jpg under data/flowers/jpg/",
    )
    parser.add_argument(
        "--labels-mat",
        type=Path,
        default=None,
        help="Path to imagelabels.mat (default: data/flowers/imagelabels.mat)",
    )
    parser.add_argument(
        "--identify",
        action="store_true",
        help="Run VLM identification and compare top-1 prediction to ground truth",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress CLI progress output when running identification",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    photo_path = args.photo.resolve()
    if not photo_path.is_file():
        print(f"Photo not found: {photo_path}", file=sys.stderr)
        return 1

    settings = Settings()
    labels_mat = args.labels_mat or default_labels_mat_path()
    catalog = FileSpeciesCatalog(settings.species_catalog_path)
    class_names = catalog.list_class_names()

    try:
        ground_truth = ground_truth_species_label(photo_path, class_names, labels_mat)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(f"Image: {photo_path.name}")
    print(f"Ground truth: {ground_truth}")

    if not args.identify:
        return 0

    observation = Observation(
        observation_id=f"ground-truth-check-{photo_path.stem}",
        photo_paths=[photo_path],
    )
    use_case = build_identify_use_case("vlm", settings)
    try:
        with identification_progress("vlm", 1, settings, quiet=args.quiet):
            result = use_case.execute(observation)
    except Exception as exc:
        print(f"Identification failed: {exc}", file=sys.stderr)
        return 1

    top_prediction = result.predictions[0].species_label
    match = top_prediction == ground_truth
    print(f"Predicted (top-1): {top_prediction}")
    print(f"Match: {'yes' if match else 'no'}")
    print(json.dumps(result.model_dump(mode="json"), indent=2))
    return 0 if match else 2


if __name__ == "__main__":
    sys.exit(main())
