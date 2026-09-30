"""Oxford 102 train-split reference images for retrieval prototypes."""

from __future__ import annotations

from pathlib import Path

from eval.dataset import (
    default_jpg_dir,
    default_setid_mat_path,
    load_oxford_splits,
    split_image_indices,
)
from eval.oxford102_ground_truth import default_labels_mat_path, ground_truth_species_label


def train_image_paths_for_label(
    catalog_label: str,
    *,
    class_names: list[str],
    max_images: int,
    jpg_dir: Path | None = None,
    setid_mat: Path | None = None,
    labels_mat: Path | None = None,
) -> list[Path]:
    """Return up to max_images train-split paths for catalog_label (no test leakage)."""
    if max_images < 1:
        raise ValueError("max_images must be at least 1.")
    jpg_root = jpg_dir or default_jpg_dir()
    splits = load_oxford_splits(str((setid_mat or default_setid_mat_path()).resolve()))
    train_indices = split_image_indices(splits, "train")
    labels_path = labels_mat or default_labels_mat_path()
    matches: list[Path] = []
    for image_index in train_indices:
        image_path = jpg_root / f"image_{image_index:05d}.jpg"
        if not image_path.is_file():
            continue
        label = ground_truth_species_label(image_path, class_names, labels_path)
        if label == catalog_label:
            matches.append(image_path)
        if len(matches) >= max_images:
            break
    return matches


def assert_not_test_split(
    image_path: Path,
    *,
    setid_mat: Path | None = None,
) -> None:
    splits = load_oxford_splits(str((setid_mat or default_setid_mat_path()).resolve()))
    from eval.oxford102_ground_truth import parse_image_index

    index = parse_image_index(image_path)
    if index in set(splits.test):
        raise ValueError(f"Test-split image cannot be used as prototype: {image_path}")
