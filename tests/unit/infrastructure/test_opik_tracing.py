import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from plant_id.domain.models import Observation
from plant_id.infrastructure.config.settings import Settings
from plant_id.infrastructure.identification.vlm_ollama import VlmOllamaIdentificationRepository
from plant_id.infrastructure.species.file_catalog import FileSpeciesCatalog


@pytest.fixture
def settings(monkeypatch) -> Settings:
    monkeypatch.delenv("PLANT_ID_OPIK_ENABLED", raising=False)
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


def test_record_content_retry_updates_identify_span() -> None:
    settings = Settings().model_copy(update={"opik_enabled": True})

    with patch("opik.opik_context.update_current_span") as update_span:
        from plant_id.infrastructure.observability import opik_tracing

        opik_tracing.record_content_retry(settings, reason="json_in_thinking")

    update_span.assert_called_once_with(
        metadata={
            "content_retry": True,
            "content_retry_reason": "json_in_thinking",
        }
    )


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


def test_call_openai_chat_traced_records_usage() -> None:
    settings = Settings().model_copy(update={"opik_enabled": True})
    response = MagicMock()
    response.id = "resp-1"
    usage = MagicMock()
    usage.prompt_tokens = 10
    usage.completion_tokens = 5
    usage.total_tokens = 15
    response.usage = usage

    with patch("plant_id.infrastructure.observability.opik_tracing._configure_opik"):
        with patch("opik.start_as_current_span") as start_span:
            with patch("opik.opik_context.update_current_span") as update_span:
                start_span.return_value.__enter__ = MagicMock(return_value=None)
                start_span.return_value.__exit__ = MagicMock(return_value=False)
                from plant_id.infrastructure.observability import opik_tracing

                opik_tracing.call_openai_chat_traced(
                    settings,
                    lambda: response,
                    model="cloud-model",
                    prompt_version="closed-set-v3",
                    cloud_vendor="fireworks",
                )

    update_span.assert_called_once()
    assert update_span.call_args.kwargs["usage"]["total_tokens"] == 15
