"""Oxford 102 dataset loading for offline eval runs."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from functools import lru_cache
from pathlib import Path

import scipy.io

from eval.oxford102_ground_truth import (
    ground_truth_species_label,
    parse_image_index,
    project_root,
)
from eval.profile_manifest import (
    default_profile_manifest_path,
    load_profile_manifest,
    select_manifest_observations,
    validate_manifest_against_dataset,
)

SPLIT_NAMES = ("train", "validation", "test")
EXPECTED_TEST_SPLIT_SIZE = 6149


class EvalProfile(StrEnum):
    SMOKE = "smoke"
    QUICK = "quick"
    FULL = "full"


PROFILE_SIZES: dict[EvalProfile, int | None] = {
    EvalProfile.SMOKE: 4,
    EvalProfile.QUICK: 8,
    EvalProfile.FULL: None,
}


@dataclass(frozen=True)
class EvalImage:
    """One Oxford 102 image with resolved ground-truth label."""

    image_path: Path
    image_index: int
    ground_truth: str
    split: str


def default_dataset_root(root: Path | None = None) -> Path:
    return (root or project_root()) / "data" / "flowers"


def default_setid_mat_path(root: Path | None = None) -> Path:
    return default_dataset_root(root) / "setid.mat"


def default_jpg_dir(root: Path | None = None) -> Path:
    return default_dataset_root(root) / "jpg"


def resolve_split_name(split: str) -> str:
    normalized = split.strip().lower()
    if normalized not in SPLIT_NAMES:
        raise ValueError(
            f"Unknown split {split!r}; expected one of {', '.join(SPLIT_NAMES)}."
        )
    return normalized


def resolve_profile(profile: str) -> EvalProfile:
    normalized = profile.strip().lower()
    try:
        return EvalProfile(normalized)
    except ValueError as exc:
        allowed = ", ".join(profile.value for profile in EvalProfile)
        raise ValueError(f"Unknown profile {profile!r}; expected one of {allowed}.") from exc


@dataclass(frozen=True)
class OxfordSplits:
    train: tuple[int, ...]
    validation: tuple[int, ...]
    test: tuple[int, ...]


@lru_cache
def load_oxford_splits(setid_mat_path: str) -> OxfordSplits:
    path = Path(setid_mat_path)
    if not path.is_file():
        raise FileNotFoundError(f"Split file not found: {path}")
    data = scipy.io.loadmat(path)
    missing = [key for key in ("trnid", "valid", "tstid") if key not in data]
    if missing:
        raise ValueError(
            f"setid.mat missing expected split arrays: {', '.join(missing)}. "
            "Expected Oxford 102 keys trnid, valid, tstid."
        )
    return OxfordSplits(
        train=tuple(int(value) for value in data["trnid"].reshape(-1)),
        validation=tuple(int(value) for value in data["valid"].reshape(-1)),
        test=tuple(int(value) for value in data["tstid"].reshape(-1)),
    )


def split_image_indices(splits: OxfordSplits, split: str) -> tuple[int, ...]:
    split_name = resolve_split_name(split)
    if split_name == "train":
        return splits.train
    if split_name == "validation":
        return splits.validation
    return splits.test


def _require_dataset_files(dataset_root: Path) -> tuple[Path, Path, Path]:
    jpg_dir = dataset_root / "jpg"
    labels_mat = dataset_root / "imagelabels.mat"
    setid_mat = dataset_root / "setid.mat"
    missing = [
        str(path)
        for path in (jpg_dir, labels_mat, setid_mat)
        if not path.exists()
    ]
    if missing:
        raise FileNotFoundError(
            "Oxford 102 dataset files missing: "
            f"{', '.join(missing)}. See README for download instructions."
        )
    return jpg_dir, labels_mat, setid_mat


def list_eval_images(
    *,
    class_names: list[str],
    split: str = "test",
    profile: str = EvalProfile.QUICK,
    limit: int | None = None,
    dataset_root: Path | None = None,
    profile_manifest: Path | None = None,
) -> list[EvalImage]:
    """Return eval images for a split/profile."""
    split_name = resolve_split_name(split)
    profile_enum = resolve_profile(profile)
    root = dataset_root or default_dataset_root()
    jpg_dir, labels_mat, setid_mat = _require_dataset_files(root)

    if profile_enum is EvalProfile.FULL:
        return _list_split_indices(
            class_names=class_names,
            split_name=split_name,
            indices=_full_split_indices(setid_mat, split_name, limit),
            jpg_dir=jpg_dir,
            labels_mat=labels_mat,
        )

    manifest_path = profile_manifest or default_profile_manifest_path(profile_enum.value)
    manifest = load_profile_manifest(manifest_path)
    observations = select_manifest_observations(manifest, profile_enum.value, limit=limit)

    splits = load_oxford_splits(str(setid_mat.resolve()))
    test_indices = set(split_image_indices(splits, split_name))
    validate_manifest_against_dataset(
        observations,
        class_names=class_names,
        jpg_dir=jpg_dir,
        labels_mat=labels_mat,
        split_name=split_name,
        test_indices=test_indices,
    )

    images: list[EvalImage] = []
    for row in observations:
        image_path = jpg_dir / row.image_name
        image_index = parse_image_index(image_path)
        images.append(
            EvalImage(
                image_path=image_path,
                image_index=image_index,
                ground_truth=row.species,
                split=split_name,
            )
        )
    return images


def _full_split_indices(
    setid_mat: Path,
    split_name: str,
    limit: int | None,
) -> tuple[int, ...]:
    splits = load_oxford_splits(str(setid_mat.resolve()))
    indices = sorted(split_image_indices(splits, split_name))
    if limit is not None:
        if limit < 1:
            raise ValueError("--limit must be at least 1.")
        indices = indices[:limit]
    return tuple(indices)


def _list_split_indices(
    *,
    class_names: list[str],
    split_name: str,
    indices: tuple[int, ...],
    jpg_dir: Path,
    labels_mat: Path,
) -> list[EvalImage]:
    images: list[EvalImage] = []
    for image_index in indices:
        image_path = jpg_dir / f"image_{image_index:05d}.jpg"
        if not image_path.is_file():
            raise FileNotFoundError(f"Expected Oxford image not found: {image_path}")
        ground_truth = ground_truth_species_label(
            image_path,
            class_names,
            labels_mat,
        )
        images.append(
            EvalImage(
                image_path=image_path,
                image_index=image_index,
                ground_truth=ground_truth,
                split=split_name,
            )
        )
    return images


def count_split_images(
    split: str,
    *,
    dataset_root: Path | None = None,
) -> int:
    split_name = resolve_split_name(split)
    root = dataset_root or default_dataset_root()
    _, _, setid_mat = _require_dataset_files(root)
    splits = load_oxford_splits(str(setid_mat.resolve()))
    return len(split_image_indices(splits, split_name))
