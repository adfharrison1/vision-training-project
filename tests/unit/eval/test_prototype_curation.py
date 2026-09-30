"""Unit tests for optional prototype curation YAML."""

from __future__ import annotations

from pathlib import Path

import pytest
from eval.prototype_curation import load_prototype_curation, resolve_curated_train_paths


def test_load_prototype_curation_missing_file(tmp_path: Path) -> None:
    assert load_prototype_curation(tmp_path) == {}


def test_load_prototype_curation_parses_labels(tmp_path: Path) -> None:
    path = tmp_path / "prototypes.yaml"
    path.write_text(
        "bolero deep blue:\n  - image_00001.jpg\n",
        encoding="utf-8",
    )
    assert load_prototype_curation(tmp_path) == {
        "bolero deep blue": ["image_00001.jpg"],
    }


def test_resolve_curated_train_paths_validates_label(tmp_path: Path, monkeypatch) -> None:
    jpg_dir = tmp_path / "jpg"
    jpg_dir.mkdir()
    image = jpg_dir / "image_00001.jpg"
    image.write_bytes(b"x")
    monkeypatch.setattr(
        "eval.prototype_curation.assert_not_test_split",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        "eval.prototype_curation.ground_truth_species_label",
        lambda *_args, **_kwargs: "wrong label",
    )
    with pytest.raises(ValueError, match="expected"):
        resolve_curated_train_paths(
            "bolero deep blue",
            ["image_00001.jpg"],
            class_names=["bolero deep blue"],
            jpg_dir=jpg_dir,
            labels_mat=tmp_path / "labels.mat",
        )


def test_resolve_curated_train_paths_accepts_train_image(tmp_path: Path, monkeypatch) -> None:
    jpg_dir = tmp_path / "jpg"
    jpg_dir.mkdir()
    image = jpg_dir / "image_00001.jpg"
    image.write_bytes(b"x")
    monkeypatch.setattr(
        "eval.prototype_curation.assert_not_test_split",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        "eval.prototype_curation.ground_truth_species_label",
        lambda *_args, **_kwargs: "bolero deep blue",
    )
    paths = resolve_curated_train_paths(
        "bolero deep blue",
        ["image_00001.jpg"],
        class_names=["bolero deep blue"],
        jpg_dir=jpg_dir,
        labels_mat=tmp_path / "labels.mat",
    )
    assert paths == [image]
