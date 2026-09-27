import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from plant_id.domain.exceptions import IdentificationError
from plant_id.domain.models import Observation
from plant_id.infrastructure.config.settings import Settings
from plant_id.infrastructure.identification.vlm_cloud import VlmCloudIdentificationRepository
from plant_id.infrastructure.species.file_catalog import FileSpeciesCatalog


def _settings(**updates) -> Settings:
    base = {
        "vlm_cloud_api_key": "test-key",
        "vlm_cloud_base_url": "https://example.com/v1",
        "vlm_cloud_model": "accounts/fireworks/models/qwen3-vl-8b-instruct",
        "vlm_cloud_reasoning_effort": "none",
    }
    base.update(updates)
    return Settings(**base)


def _repo(settings: Settings | None = None, client: MagicMock | None = None):
    settings = settings or _settings()
    catalog = FileSpeciesCatalog(settings.species_catalog_path)
    return VlmCloudIdentificationRepository(settings, catalog, client=client)


def test_vlm_cloud_backend_id_uses_model() -> None:
    repo = _repo()
    assert repo.backend_id == "vlm-cloud:accounts/fireworks/models/qwen3-vl-8b-instruct"


def test_vlm_cloud_missing_api_key_fails_before_request(tmp_path: Path) -> None:
    photo = tmp_path / "flower.jpg"
    photo.write_bytes(b"fake")
    repo = _repo(_settings(vlm_cloud_api_key=None))
    observation = Observation(observation_id="obs-cloud", photo_paths=[photo])

    with pytest.raises(IdentificationError, match="PLANT_ID_VLM_CLOUD_API_KEY"):
        repo.identify(observation)


def test_vlm_cloud_identify_parses_valid_response(tmp_path: Path) -> None:
    photo = tmp_path / "flower.jpg"
    photo.write_bytes(b"fake")
    payload = {
        "predictions": [
            {
                "rank": 1,
                "species_label": "tiger lily",
                "evidence": "orange petals",
                "confidence": 0.9,
            }
        ]
    }
    message = MagicMock()
    message.content = json.dumps(payload)
    choice = MagicMock()
    choice.message = message
    response = MagicMock()
    response.choices = [choice]
    response.model_dump.return_value = {"choices": [{"message": {"content": message.content}}]}

    client = MagicMock()
    client.chat.completions.create.return_value = response

    repo = _repo(client=client)
    observation = Observation(observation_id="obs-cloud", photo_paths=[photo])
    result, raw = repo.identify(observation)

    assert result.predictions[0].species_label == "tiger lily"
    assert result.model_tag == "accounts/fireworks/models/qwen3-vl-8b-instruct"
    assert raw["request"]["model"] == "accounts/fireworks/models/qwen3-vl-8b-instruct"
    client.chat.completions.create.assert_called_once()
    assert client.chat.completions.create.call_args.kwargs["reasoning_effort"] == "none"


def test_vlm_cloud_omits_reasoning_effort_when_unset(tmp_path: Path) -> None:
    photo = tmp_path / "flower.jpg"
    photo.write_bytes(b"fake")
    message = MagicMock()
    message.content = json.dumps(
        {
            "predictions": [
                {
                    "rank": 1,
                    "species_label": "tiger lily",
                    "evidence": "x",
                    "confidence": 0.9,
                }
            ]
        }
    )
    choice = MagicMock()
    choice.message = message
    response = MagicMock()
    response.choices = [choice]
    response.model_dump.return_value = {}

    client = MagicMock()
    client.chat.completions.create.return_value = response
    repo = _repo(_settings(vlm_cloud_reasoning_effort=None), client=client)
    observation = Observation(observation_id="obs-cloud", photo_paths=[photo])
    repo.identify(observation)

    assert "reasoning_effort" not in client.chat.completions.create.call_args.kwargs


def test_vlm_cloud_retries_unknown_species_label(tmp_path: Path) -> None:
    photo = tmp_path / "flower.jpg"
    photo.write_bytes(b"fake")
    bad_message = MagicMock()
    bad_message.content = json.dumps(
        {
            "predictions": [
                {
                    "rank": 1,
                    "species_label": "calendula",
                    "evidence": "orange flower",
                    "confidence": 0.9,
                }
            ]
        }
    )
    good_message = MagicMock()
    good_message.content = json.dumps(
        {
            "predictions": [
                {
                    "rank": 1,
                    "species_label": "tiger lily",
                    "evidence": "spots",
                    "confidence": 0.9,
                }
            ]
        }
    )
    bad_choice = MagicMock()
    bad_choice.message = bad_message
    bad_response = MagicMock()
    bad_response.choices = [bad_choice]
    bad_response.model_dump.return_value = {"attempt": 1}

    good_choice = MagicMock()
    good_choice.message = good_message
    good_response = MagicMock()
    good_response.choices = [good_choice]
    good_response.model_dump.return_value = {"attempt": 2}

    client = MagicMock()
    client.chat.completions.create.side_effect = [bad_response, good_response]
    repo = _repo(client=client)
    observation = Observation(observation_id="obs-cloud", photo_paths=[photo])

    result, raw = repo.identify(observation)

    assert result.predictions[0].species_label == "tiger lily"
    assert client.chat.completions.create.call_count == 2
    assert raw["invalid_label_retry"]["attempted"] is True


def test_vlm_cloud_identify_rejects_invalid_json(tmp_path: Path) -> None:
    photo = tmp_path / "flower.jpg"
    photo.write_bytes(b"fake")
    message = MagicMock()
    message.content = "not json"
    choice = MagicMock()
    choice.message = message
    response = MagicMock()
    response.choices = [choice]
    response.model_dump.return_value = {}

    client = MagicMock()
    client.chat.completions.create.return_value = response

    repo = _repo(client=client)
    observation = Observation(observation_id="obs-cloud", photo_paths=[photo])

    with pytest.raises(IdentificationError, match="Invalid model JSON"):
        repo.identify(observation)


def test_vlm_cloud_api_error_wrapped(tmp_path: Path) -> None:
    photo = tmp_path / "flower.jpg"
    photo.write_bytes(b"fake")
    client = MagicMock()
    client.chat.completions.create.side_effect = RuntimeError("upstream down")

    repo = _repo(client=client)
    observation = Observation(observation_id="obs-cloud", photo_paths=[photo])

    with pytest.raises(IdentificationError, match="Cloud VLM request failed"):
        repo.identify(observation)
