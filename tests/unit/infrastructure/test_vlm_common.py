from pathlib import Path

import pytest

from plant_id.domain.exceptions import IdentificationError
from plant_id.domain.models import Observation
from plant_id.infrastructure.config.settings import Settings
from plant_id.infrastructure.identification.vlm_common import parse_vlm_result
from plant_id.infrastructure.species.file_catalog import FileSpeciesCatalog


def _catalog() -> FileSpeciesCatalog:
    return FileSpeciesCatalog(Settings().species_catalog_path)


def test_parse_vlm_result_drops_invalid_lower_rank_labels(tmp_path: Path) -> None:
    photo = tmp_path / "flower.jpg"
    photo.write_bytes(b"x")
    observation = Observation(observation_id="obs-1", photo_paths=[photo])
    payload = {
        "predictions": [
            {
                "rank": 1,
                "species_label": "sweet pea",
                "evidence": "papilionaceous flowers",
                "confidence": 0.98,
            },
            {
                "rank": 2,
                "species_label": "everlasting pea",
                "evidence": "similar structure",
                "confidence": 0.02,
            },
        ]
    }

    result = parse_vlm_result(
        observation,
        payload,
        settings=Settings(),
        species_catalog=_catalog(),
        model_tag="test-model",
    )

    assert len(result.predictions) == 1
    assert result.predictions[0].species_label == "sweet pea"


def test_parse_vlm_result_rejects_invalid_top_rank_label(tmp_path: Path) -> None:
    photo = tmp_path / "flower.jpg"
    photo.write_bytes(b"x")
    observation = Observation(observation_id="obs-2", photo_paths=[photo])
    payload = {
        "predictions": [
            {
                "rank": 1,
                "species_label": "calendula",
                "evidence": "orange flower",
                "confidence": 0.9,
            },
            {
                "rank": 2,
                "species_label": "barbeton daisy",
                "evidence": "also orange",
                "confidence": 0.1,
            },
        ]
    }

    with pytest.raises(IdentificationError, match="Unknown species_label: calendula"):
        parse_vlm_result(
            observation,
            payload,
            settings=Settings(),
            species_catalog=_catalog(),
            model_tag="test-model",
        )
