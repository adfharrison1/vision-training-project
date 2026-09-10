
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

    class_names = [f"class-{index}" for index in range(1, 103)]
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
    assert smoke[0].image_index < smoke[1].image_index


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
