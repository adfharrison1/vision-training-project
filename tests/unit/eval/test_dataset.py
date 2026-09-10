
import pytest
from eval.dataset import (
    EXPECTED_TEST_SPLIT_SIZE,
    EvalProfile,
    count_split_images,
    list_eval_images,
    project_root,
    resolve_profile,
)


def test_resolve_profile_accepts_known_values() -> None:
    assert resolve_profile("quick") == EvalProfile.QUICK


def test_resolve_profile_rejects_unknown_value() -> None:
    with pytest.raises(ValueError, match="Unknown profile"):
        resolve_profile("mini")


def test_list_eval_images_profile_sizes() -> None:
    root = project_root() / "data" / "flowers"
    if not (root / "setid.mat").is_file():
        pytest.skip("Oxford 102 dataset not present")

    from plant_id.infrastructure.config.settings import Settings
    from plant_id.infrastructure.species.file_catalog import FileSpeciesCatalog

    class_names = FileSpeciesCatalog(Settings().species_catalog_path).list_class_names()
    smoke = list_eval_images(
        class_names=class_names,
        split="test",
        profile="smoke",
        dataset_root=root,
    )
    quick = list_eval_images(
        class_names=class_names,
        split="test",
        profile="quick",
        dataset_root=root,
    )
    assert len(smoke) == 4
    assert len(quick) == 8
    assert len({image.ground_truth for image in quick}) == 8
    assert smoke == quick[:4]


def test_test_split_count_sanity() -> None:
    root = project_root() / "data" / "flowers"
    if not (root / "setid.mat").is_file():
        pytest.skip("Oxford 102 dataset not present")

    count = count_split_images("test", dataset_root=root)
    assert count == EXPECTED_TEST_SPLIT_SIZE


def test_list_eval_images_rejects_invalid_limit() -> None:
    root = project_root() / "data" / "flowers"
    if not (root / "setid.mat").is_file():
        pytest.skip("Oxford 102 dataset not present")

    with pytest.raises(ValueError, match="--limit"):
        list_eval_images(
            class_names=["a"] * 102,
            split="test",
            profile="smoke",
            limit=0,
            dataset_root=root,
        )
