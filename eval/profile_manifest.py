"""Load fixed species/image manifests for smoke and quick eval profiles."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from eval.oxford102_ground_truth import (
    ground_truth_species_label,
    parse_image_index,
    project_root,
)

PROFILE_OBSERVATION_COUNTS = {
    "smoke": 4,
    "quick": 8,
    "mixed16": 16,
    "yellow16": 16,
    "primula_repeat10": 10,
    "english_marigold_repeat10": 10,
    "curated48": 48,
}

PROFILE_MANIFEST_FILES = {
    "smoke": "quick.yaml",
    "quick": "quick.yaml",
    "mixed16": "mixed16.yaml",
    "yellow16": "yellow16.yaml",
    "primula_repeat10": "primula_repeat10.yaml",
    "english_marigold_repeat10": "english_marigold_repeat10.yaml",
    "curated48": "curated48.yaml",
}


@dataclass(frozen=True)
class ProfileObservationSpec:
    species: str
    image_name: str


@dataclass(frozen=True)
class ProfileManifest:
    observations: tuple[ProfileObservationSpec, ...]


def default_profile_manifest_path(profile: str) -> Path:
    manifest_file = PROFILE_MANIFEST_FILES.get(profile)
    if manifest_file is None:
        raise ValueError(f"Profile {profile!r} does not use a fixed manifest.")
    return project_root() / "eval" / "profiles" / manifest_file


def load_profile_manifest(path: Path) -> ProfileManifest:
    if not path.is_file():
        raise FileNotFoundError(f"Profile manifest not found: {path}")

    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Profile manifest must be a mapping: {path}")

    raw_observations = payload.get("observations")
    if not isinstance(raw_observations, list) or not raw_observations:
        raise ValueError(f"Profile manifest must include a non-empty observations list: {path}")

    observations: list[ProfileObservationSpec] = []
    for index, item in enumerate(raw_observations, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Observation {index} in {path} must be a mapping.")
        species = item.get("species")
        image = item.get("image")
        if not isinstance(species, str) or not species.strip():
            raise ValueError(f"Observation {index} in {path} requires non-empty species.")
        if not isinstance(image, str) or not image.strip():
            raise ValueError(f"Observation {index} in {path} requires non-empty image.")
        observations.append(
            ProfileObservationSpec(
                species=species.strip(),
                image_name=Path(image.strip()).name,
            )
        )

    return ProfileManifest(observations=tuple(observations))


def select_manifest_observations(
    manifest: ProfileManifest,
    profile: str,
    *,
    limit: int | None = None,
) -> tuple[ProfileObservationSpec, ...]:
    if profile not in PROFILE_OBSERVATION_COUNTS:
        raise ValueError(f"Profile {profile!r} does not use a fixed manifest.")

    profile_limit = PROFILE_OBSERVATION_COUNTS[profile]
    selected = manifest.observations[:profile_limit]
    if limit is not None:
        if limit < 1:
            raise ValueError("--limit must be at least 1.")
        selected = selected[:limit]
    if len(selected) < profile_limit and limit is None:
        raise ValueError(
            f"Profile manifest defines {len(manifest.observations)} observation(s) but "
            f"profile {profile!r} requires {profile_limit}."
        )
    return selected


def validate_manifest_against_dataset(
    observations: tuple[ProfileObservationSpec, ...],
    *,
    class_names: list[str],
    jpg_dir: Path,
    labels_mat: Path,
    split_name: str,
    test_indices: set[int],
) -> None:
    allowed_species = set(class_names)
    for row in observations:
        if row.species not in allowed_species:
            raise ValueError(
                f"Manifest species {row.species!r} is not in the species catalog."
            )

        image_path = jpg_dir / row.image_name
        if not image_path.is_file():
            raise FileNotFoundError(f"Manifest image not found: {image_path}")

        image_index = parse_image_index(image_path)
        if split_name == "test" and image_index not in test_indices:
            raise ValueError(
                f"Manifest image {row.image_name} is not in the {split_name} split."
            )

        ground_truth = ground_truth_species_label(image_path, class_names, labels_mat)
        if ground_truth != row.species:
            raise ValueError(
                f"Manifest mismatch for {row.image_name}: species={row.species!r} "
                f"but imagelabels.mat ground truth is {ground_truth!r}."
            )
