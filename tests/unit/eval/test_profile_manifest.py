from pathlib import Path

import pytest
from eval.profile_manifest import load_profile_manifest, select_manifest_observations


def test_load_profile_manifest_reads_species_and_image(tmp_path: Path) -> None:
    manifest_path = tmp_path / "quick.yaml"
    manifest_path.write_text(
        """
observations:
  - species: tiger lily
    image: image_07162.jpg
  - species: sweet pea
    image: image_05629.jpg
""".strip()
        + "\n",
        encoding="utf-8",
    )

    manifest = load_profile_manifest(manifest_path)
    assert len(manifest.observations) == 2
    assert manifest.observations[0].species == "tiger lily"
    assert manifest.observations[0].image_name == "image_07162.jpg"


def test_select_manifest_observations_honors_profile_size() -> None:
    manifest = load_profile_manifest(
        Path("eval/profiles/quick.yaml"),
    )
    smoke = select_manifest_observations(manifest, "smoke")
    quick = select_manifest_observations(manifest, "quick")

    assert len(smoke) == 4
    assert len(quick) == 8
    assert len({row.species for row in quick}) == 8


def test_mixed16_manifest_has_sixteen_distinct_species() -> None:
    manifest = load_profile_manifest(Path("eval/profiles/mixed16.yaml"))
    mixed16 = select_manifest_observations(manifest, "mixed16")

    assert len(mixed16) == 16
    assert len({row.species for row in mixed16}) == 16
    assert mixed16[0].image_name == "image_06734.jpg"
    assert mixed16[1].image_name == "image_05147.jpg"


def test_validate_manifest_rejects_species_image_mismatch() -> None:
    from eval.dataset import default_dataset_root, load_oxford_splits, split_image_indices
    from eval.profile_manifest import ProfileObservationSpec, validate_manifest_against_dataset
    from plant_id.infrastructure.config.settings import Settings
    from plant_id.infrastructure.species.file_catalog import FileSpeciesCatalog

    root = default_dataset_root()
    if not (root / "setid.mat").is_file():
        pytest.skip("Oxford 102 dataset not present")

    class_names = FileSpeciesCatalog(Settings().species_catalog_path).list_class_names()
    jpg_dir = root / "jpg"
    labels_mat = root / "imagelabels.mat"
    splits = load_oxford_splits(str((root / "setid.mat").resolve()))
    test_indices = set(split_image_indices(splits, "test"))

    with pytest.raises(ValueError, match="Manifest mismatch"):
        validate_manifest_against_dataset(
            (
                ProfileObservationSpec(
                    species="tiger lily",
                    image_name="image_05629.jpg",
                ),
            ),
            class_names=class_names,
            jpg_dir=jpg_dir,
            labels_mat=labels_mat,
            split_name="test",
            test_indices=test_indices,
        )
