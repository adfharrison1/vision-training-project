import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from plant_id.domain.models import Observation
from plant_id.infrastructure.config.settings import Settings
from plant_id.infrastructure.identification.vlm_ollama import VlmOllamaIdentificationRepository
from plant_id.infrastructure.species.file_catalog import FileSpeciesCatalog


@pytest.fixture
def settings() -> Settings:
    return Settings()


@pytest.fixture
def catalog(settings: Settings) -> FileSpeciesCatalog:
    return FileSpeciesCatalog(settings.species_catalog_path)


def _mock_chat_response(content: str) -> MagicMock:
    response = MagicMock()
    response.message.content = content
    response.message.thinking = ""
    response.model_dump.return_value = {"message": {"content": content}}
    return response


def test_vlm_identify_with_tracing_disabled_does_not_configure_opik(
    settings: Settings,
    catalog: FileSpeciesCatalog,
    tmp_path: Path,
) -> None:
    assert settings.opik_enabled is False
    photo = tmp_path / "photo.jpg"
    photo.write_bytes(b"fake-image")
    client = MagicMock()
    client.chat.return_value = _mock_chat_response(
        json.dumps(
            {
                "predictions": [
                    {
                        "rank": 1,
                        "species_label": "pink primrose",
                        "evidence": "pink petals",
                        "confidence": 0.95,
                    }
                ]
            }
        )
    )

    repo = VlmOllamaIdentificationRepository(settings, catalog, client=client)
    observation = Observation(observation_id="obs-no-opik", photo_paths=[photo])

    with patch("opik.config.update_session_config") as update_session_config:
        result, _ = repo.identify(observation)

    assert result.predictions[0].species_label == "pink primrose"
    update_session_config.assert_not_called()
    assert client.chat.call_count == 1


def test_vlm_identify_with_opik_unreachable_still_succeeds(
    settings: Settings,
    catalog: FileSpeciesCatalog,
    tmp_path: Path,
) -> None:
    settings = settings.model_copy(update={"opik_enabled": True})
    photo = tmp_path / "photo.jpg"
    photo.write_bytes(b"fake-image")
    client = MagicMock()
    client.chat.return_value = _mock_chat_response(
        json.dumps(
            {
                "predictions": [
                    {
                        "rank": 1,
                        "species_label": "pink primrose",
                        "evidence": "pink petals",
                        "confidence": 0.95,
                    }
                ]
            }
        )
    )

    repo = VlmOllamaIdentificationRepository(settings, catalog, client=client)
    observation = Observation(observation_id="obs-opik-down", photo_paths=[photo])

    with patch(
        "plant_id.infrastructure.observability.opik_tracing._configure_opik",
        side_effect=ConnectionError("Opik unreachable"),
    ):
        result, _ = repo.identify(observation)

    assert result.predictions[0].species_label == "pink primrose"
    assert client.chat.call_count == 1
