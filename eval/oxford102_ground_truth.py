"""Oxford 102 ground-truth labels from imagelabels.mat."""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

import scipy.io

IMAGE_FILENAME_PATTERN = re.compile(r"^image_(\d+)\.jpg$", re.IGNORECASE)


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def default_labels_mat_path(root: Path | None = None) -> Path:
    return (root or project_root()) / "data" / "flowers" / "imagelabels.mat"


def parse_image_index(photo_path: Path) -> int:
    """Return 1-based Oxford image index from ``image_00018.jpg`` style names."""
    match = IMAGE_FILENAME_PATTERN.match(photo_path.name)
    if match is None:
        raise ValueError(
            f"Photo filename must match image_XXXXX.jpg (got {photo_path.name!r})."
        )
    return int(match.group(1))


@lru_cache
def load_class_ids(labels_mat_path: str) -> tuple[int, ...]:
    """Load per-image class ids (1-based) from imagelabels.mat."""
    path = Path(labels_mat_path)
    if not path.is_file():
        raise FileNotFoundError(f"Labels file not found: {path}")
    matrix = scipy.io.loadmat(path)["labels"]
    flat = matrix.reshape(-1)
    return tuple(int(value) for value in flat)


def ground_truth_species_label(
    photo_path: Path,
    class_names: list[str],
    labels_mat_path: Path | None = None,
) -> str:
    """Look up the canonical species label for an Oxford 102 image file."""
    image_index = parse_image_index(photo_path)
    mat_path = labels_mat_path or default_labels_mat_path()
    class_ids = load_class_ids(str(mat_path.resolve()))
    if image_index < 1 or image_index > len(class_ids):
        raise ValueError(
            f"Image index {image_index} out of range for {len(class_ids)} labelled images."
        )
    class_id = class_ids[image_index - 1]
    if class_id < 1 or class_id > len(class_names):
        raise ValueError(f"Class id {class_id} out of range for {len(class_names)} names.")
    return class_names[class_id - 1]
