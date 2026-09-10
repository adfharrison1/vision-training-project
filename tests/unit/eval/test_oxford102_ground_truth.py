from pathlib import Path

import pytest
from eval.oxford102_ground_truth import (
    ground_truth_species_label,
    parse_image_index,
    project_root,
)


def test_parse_image_index_from_standard_filename() -> None:
    assert parse_image_index(Path("image_00018.jpg")) == 18


def test_parse_image_index_rejects_non_standard_filename() -> None:
    with pytest.raises(ValueError, match="image_XXXXX.jpg"):
        parse_image_index(Path("passion.jpg"))


def test_ground_truth_species_label_uses_labels_mat() -> None:
    labels_mat = project_root() / "data" / "flowers" / "imagelabels.mat"
    if not labels_mat.is_file():
        pytest.skip("imagelabels.mat not present")

    class_names = [f"class-{index}" for index in range(1, 103)]
    label = ground_truth_species_label(
        Path("image_00002.jpg"),
        class_names,
        labels_mat,
    )
    assert label == "class-77"


def test_ground_truth_rejects_out_of_range_index() -> None:
    labels_mat = project_root() / "data" / "flowers" / "imagelabels.mat"
    if not labels_mat.is_file():
        pytest.skip("imagelabels.mat not present")
    with pytest.raises(ValueError, match="out of range"):
        ground_truth_species_label(
            Path("image_99999.jpg"),
            ["a"] * 102,
            labels_mat,
        )


def test_ground_truth_rejects_invalid_filename() -> None:
    labels_mat = project_root() / "data" / "flowers" / "imagelabels.mat"
    if not labels_mat.is_file():
        pytest.skip("imagelabels.mat not present")
    with pytest.raises(ValueError, match="image_XXXXX.jpg"):
        ground_truth_species_label(
            Path("passion.jpg"),
            ["a"] * 102,
            labels_mat,
        )
