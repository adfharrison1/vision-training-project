import json
from pathlib import Path
from unittest.mock import patch

import pytest

from plant_id.domain.models import ObservationResult, Prediction
from plant_id.interfaces.cli.commands.demo import default_demo_image, run_demo
from plant_id.interfaces.cli.commands.identify import run_identify
from plant_id.interfaces.composition import IdentifyRunResult


def _sample_result(observation_id: str = "obs-1") -> ObservationResult:
    return ObservationResult(
        observation_id=observation_id,
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


def test_run_identify_quiet_suppresses_progress(capsys) -> None:
    with patch(
        "plant_id.interfaces.cli.commands.identify.identify_with_cli_presentation",
        return_value=IdentifyRunResult(exit_code=0, result=_sample_result()),
    ):
        exit_code = run_identify("vlm", photos="photo.jpg", observation_id="obs-1", quiet=True)

    assert exit_code == 0
    assert capsys.readouterr().err == ""


def test_run_identify_prints_json_result(capsys) -> None:
    with patch(
        "plant_id.interfaces.cli.commands.identify.identify_with_cli_presentation",
        return_value=IdentifyRunResult(exit_code=0, result=_sample_result()),
    ):
        exit_code = run_identify("vlm", photos="photo.jpg", observation_id="obs-1")

    assert exit_code == 0
    printed = json.loads(capsys.readouterr().out)
    assert printed["observation_id"] == "obs-1"
    assert printed["predictions"][0]["species_label"] == "pink primrose"


def test_run_identify_reports_identification_error(capsys) -> None:
    with patch(
        "plant_id.interfaces.cli.commands.identify.identify_with_cli_presentation",
        return_value=IdentifyRunResult(exit_code=1, error_message="parse failed"),
    ):
        exit_code = run_identify("vlm", photos="photo.jpg")

    assert exit_code == 1
    assert "parse failed" in capsys.readouterr().err


def test_run_identify_rejects_invalid_photo_count(capsys) -> None:
    exit_code = run_identify("vlm", photos="a.jpg,b.jpg,c.jpg,d.jpg")

    assert exit_code == 1
    assert "1 to 3" in capsys.readouterr().err


def test_default_demo_image_points_at_project_data_path() -> None:
    root = Path(__file__).resolve().parents[3]
    assert default_demo_image() == root / "data" / "flowers" / "jpg" / "image_00001.jpg"


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


def test_run_identify_applies_ollama_think_override() -> None:
    with patch(
        "plant_id.interfaces.cli.commands.identify.identify_with_cli_presentation",
        return_value=IdentifyRunResult(exit_code=0, result=_sample_result()),
    ) as mock_identify:
        run_identify("vlm", photos="photo.jpg", ollama_think=True)

    assert mock_identify.call_args.args[3].ollama_think is True


def test_cli_identify_think_flag_parsed() -> None:
    from plant_id.interfaces.cli.main import build_parser

    parser = build_parser()
    args = parser.parse_args(["identify", "--photos", "a.jpg", "--think"])
    assert args.think is True
    args = parser.parse_args(["identify", "--photos", "a.jpg", "--no-think"])
    assert args.think is False
    args = parser.parse_args(["identify", "--photos", "a.jpg"])
    assert args.think is None


def test_cli_backend_choices_include_vlm_cloud() -> None:
    from plant_id.interfaces.cli.main import build_parser

    parser = build_parser()
    args = parser.parse_args(["identify", "--photos", "a.jpg", "--backend", "vlm-cloud"])
    assert args.backend == "vlm-cloud"
