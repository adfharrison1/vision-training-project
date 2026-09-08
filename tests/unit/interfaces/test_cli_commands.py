import json
from pathlib import Path
from unittest.mock import patch

import pytest

from plant_id.domain.exceptions import IdentificationError
from plant_id.domain.models import ObservationResult, Prediction
from plant_id.interfaces.cli.commands.demo import default_demo_image, run_demo
from plant_id.interfaces.cli.commands.identify import run_identify


def test_run_identify_quiet_suppresses_progress(capsys) -> None:
    result = ObservationResult(
        observation_id="obs-1",
        predictions=(
            Prediction(
                rank=1,
                species_label="pink primrose",
                evidence="five petals",
                confidence=0.9,
            ),
        ),
        model_tag="vlm:test",
        prompt_version="closed-set-v1",
    )
    fake_use_case = type("FakeUseCase", (), {"execute": lambda self, obs: result})()

    with patch(
        "plant_id.interfaces.cli.commands.identify.build_identify_use_case",
        return_value=fake_use_case,
    ):
        exit_code = run_identify("vlm", photos="photo.jpg", observation_id="obs-1", quiet=True)

    assert exit_code == 0
    assert capsys.readouterr().err == ""


def test_run_identify_prints_json_result(capsys) -> None:
    result = ObservationResult(
        observation_id="obs-1",
        predictions=(
            Prediction(
                rank=1,
                species_label="pink primrose",
                evidence="five petals",
                confidence=0.9,
            ),
        ),
        model_tag="vlm:test",
        prompt_version="closed-set-v1",
    )
    fake_use_case = type("FakeUseCase", (), {"execute": lambda self, obs: result})()

    with patch(
        "plant_id.interfaces.cli.commands.identify.build_identify_use_case",
        return_value=fake_use_case,
    ):
        exit_code = run_identify("vlm", photos="photo.jpg", observation_id="obs-1")

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["observation_id"] == "obs-1"
    assert payload["predictions"][0]["species_label"] == "pink primrose"


def test_run_identify_reports_identification_error(capsys) -> None:
    fake_use_case = type(
        "FakeUseCase",
        (),
        {"execute": lambda self, obs: (_ for _ in ()).throw(IdentificationError("parse failed"))},
    )()

    with patch(
        "plant_id.interfaces.cli.commands.identify.build_identify_use_case",
        return_value=fake_use_case,
    ):
        exit_code = run_identify("vlm", photos="photo.jpg")

    assert exit_code == 1
    assert "parse failed" in capsys.readouterr().err


def test_run_identify_rejects_invalid_photo_count(capsys) -> None:
    exit_code = run_identify("vlm", photos="a.jpg,b.jpg,c.jpg,d.jpg")

    assert exit_code == 1
    assert "1 to 3" in capsys.readouterr().err


def test_run_demo_skips_when_sample_missing(capsys, tmp_path: Path) -> None:
    with patch(
        "plant_id.interfaces.cli.commands.demo.default_demo_image",
        return_value=tmp_path / "missing.jpg",
    ):
        exit_code = run_demo("vlm")

    assert exit_code == 1
    assert "not found" in capsys.readouterr().err.lower()


@pytest.mark.skipif(
    not default_demo_image().is_file(),
    reason="Demo image not downloaded",
)
def test_run_demo_calls_identify_with_sample_path() -> None:
    sample = default_demo_image()
    with patch(
        "plant_id.interfaces.cli.commands.demo.run_identify",
        return_value=0,
    ) as mock_identify:
        exit_code = run_demo("vlm")

    assert exit_code == 0
    mock_identify.assert_called_once()
    assert mock_identify.call_args.kwargs["photos"] == str(sample)
    assert mock_identify.call_args.kwargs["observation_id"] == "demo"
