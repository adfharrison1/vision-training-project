"""Unit tests for Oxford train prototype split enforcement."""

from __future__ import annotations

from pathlib import Path

import pytest
from eval.dataset import load_oxford_splits, split_image_indices
from eval.oxford_train_prototypes import assert_not_test_split


@pytest.mark.parametrize(
    "setid_mat",
    [
        pytest.param(
            Path(__file__).resolve().parents[2] / "data" / "flowers" / "setid.mat",
            marks=pytest.mark.skipif(
                not (
                    Path(__file__).resolve().parents[2] / "data" / "flowers" / "setid.mat"
                ).is_file(),
                reason="Oxford dataset not present",
            ),
        )
    ],
)
def test_train_indices_exclude_test(setid_mat: Path) -> None:
    splits = load_oxford_splits(str(setid_mat.resolve()))
    train = set(split_image_indices(splits, "train"))
    test = set(split_image_indices(splits, "test"))
    assert train.isdisjoint(test)


def test_assert_not_test_split_rejects_test_index(tmp_path: Path) -> None:
    fake = tmp_path / "setid.mat"
    pytest.importorskip("scipy")
    import numpy as np
    import scipy.io

    scipy.io.savemat(
        fake,
        {
            "trnid": np.array([[1]], dtype=np.int32),
            "valid": np.array([[2]], dtype=np.int32),
            "tstid": np.array([[3]], dtype=np.int32),
        },
    )
    image = tmp_path / "image_00003.jpg"
    image.write_bytes(b"")
    with pytest.raises(ValueError, match="Test-split"):
        assert_not_test_split(image, setid_mat=fake)
