from pathlib import Path

import pytest
from pydantic import ValidationError

from plant_id.domain.exceptions import InvalidObservationError
from plant_id.domain.models import Observation, ObservationResult, Prediction


def test_observation_accepts_one_photo() -> None:
    observation = Observation(
        observation_id="obs-1",
        photo_paths=[Path("a.jpg")],
    )
    assert len(observation.photo_paths) == 1


def test_observation_accepts_three_photos() -> None:
    observation = Observation(
        observation_id="obs-2",
        photo_paths=[Path("a.jpg"), Path("b.jpg"), Path("c.jpg")],
    )
    assert len(observation.photo_paths) == 3


def test_observation_rejects_zero_photos() -> None:
    with pytest.raises(InvalidObservationError, match="1 to 3"):
        Observation(observation_id="obs-3", photo_paths=[])


def test_observation_rejects_four_photos() -> None:
    paths = [Path(f"{index}.jpg") for index in range(4)]
    with pytest.raises(InvalidObservationError, match="1 to 3"):
        Observation(observation_id="obs-4", photo_paths=paths)


def test_observation_rejects_empty_id() -> None:
    with pytest.raises(ValidationError):
        Observation(observation_id="", photo_paths=[Path("a.jpg")])


def test_prediction_requires_species_and_evidence() -> None:
    with pytest.raises(ValidationError):
        Prediction(rank=1, species_label="", evidence="visible petals")


def test_observation_result_requires_metadata_and_predictions() -> None:
    result = ObservationResult(
        observation_id="obs-5",
        predictions=[
            Prediction(
                rank=1,
                species_label="pink primrose",
                evidence="five pink petals",
                confidence=0.91,
            )
        ],
        model_tag="vlm:qwen3-vl:8b",
        prompt_version="closed-set-v1",
        uncertain=False,
    )
    assert result.predictions[0].species_label == "pink primrose"
    assert result.uncertain is False


def test_observation_result_rejects_non_consecutive_ranks() -> None:
    with pytest.raises(ValidationError, match="ranked consecutively"):
        ObservationResult(
            observation_id="obs-6",
            predictions=[
                Prediction(rank=1, species_label="a", evidence="a"),
                Prediction(rank=3, species_label="b", evidence="b"),
            ],
            model_tag="vlm:qwen3-vl:8b",
            prompt_version="closed-set-v1",
        )
