from unittest.mock import MagicMock, patch

from plant_id.domain.models import ObservationResult, Prediction
from plant_id.interfaces.cli.presentation import identify_with_cli_presentation


def _sample_result() -> ObservationResult:
    return ObservationResult(
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


@patch("plant_id.interfaces.composition.identify.build_identify_use_case")
def test_identify_with_cli_presentation_writes_stages(
    mock_build: MagicMock,
    capsys,
) -> None:
    mock_build.return_value.execute.return_value = _sample_result()

    outcome = identify_with_cli_presentation(
        "vlm",
        ["photo.jpg"],
        "obs-1",
        quiet=False,
    )

    assert outcome.exit_code == 0
    stderr = capsys.readouterr().err
    assert "Identifying with vlm backend" in stderr
    assert "Identification complete" in stderr


@patch("plant_id.interfaces.composition.identify.build_identify_use_case")
def test_identify_with_cli_presentation_quiet_is_silent(
    mock_build: MagicMock,
    capsys,
) -> None:
    mock_build.return_value.execute.return_value = _sample_result()

    identify_with_cli_presentation(
        "vlm",
        ["photo.jpg"],
        "obs-1",
        quiet=True,
    )

    assert capsys.readouterr().err == ""
