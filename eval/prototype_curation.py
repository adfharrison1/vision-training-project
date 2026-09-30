"""Optional curated train-image prototypes for retrieval index build."""

from __future__ import annotations

from pathlib import Path

import yaml

from eval.dataset import default_jpg_dir
from eval.oxford102_ground_truth import default_labels_mat_path, ground_truth_species_label
from eval.oxford_train_prototypes import assert_not_test_split

PROTOTYPES_FILENAME = "prototypes.yaml"


def prototypes_yaml_path(species_sheets_dir: Path) -> Path:
    return species_sheets_dir / PROTOTYPES_FILENAME


def load_prototype_curation(species_sheets_dir: Path) -> dict[str, list[str]]:
    """Return catalog_label → train image filenames (e.g. image_01234.jpg)."""
    path = prototypes_yaml_path(species_sheets_dir)
    if not path.is_file():
        return {}
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise ValueError(f"{path} must be a YAML mapping of catalog_label → filename list.")
    curation: dict[str, list[str]] = {}
    for label, filenames in raw.items():
        if not isinstance(label, str):
            raise ValueError(f"{path}: keys must be catalog labels (strings).")
        if filenames is None:
            continue
        if not isinstance(filenames, list) or not filenames:
            raise ValueError(f"{path}: {label!r} must be a non-empty list of filenames.")
        names: list[str] = []
        for item in filenames:
            if not isinstance(item, str) or not item.strip():
                raise ValueError(f"{path}: {label!r} entries must be non-empty filename strings.")
            names.append(item.strip())
        curation[label] = names
    return curation


def resolve_curated_train_paths(
    catalog_label: str,
    filenames: list[str],
    *,
    class_names: list[str],
    jpg_dir: Path | None = None,
    labels_mat: Path | None = None,
) -> list[Path]:
    """Resolve curated filenames to train-split paths with matching ground truth."""
    jpg_root = jpg_dir or default_jpg_dir()
    labels_path = labels_mat or default_labels_mat_path()
    resolved: list[Path] = []
    for name in filenames:
        image_path = jpg_root / Path(name).name
        if not image_path.is_file():
            raise FileNotFoundError(
                f"Curated prototype image not found for {catalog_label!r}: {image_path}"
            )
        assert_not_test_split(image_path)
        label = ground_truth_species_label(image_path, class_names, labels_path)
        if label != catalog_label:
            raise ValueError(
                f"Curated image {image_path.name} is labelled {label!r}, "
                f"expected {catalog_label!r}."
            )
        resolved.append(image_path)
    return resolved
