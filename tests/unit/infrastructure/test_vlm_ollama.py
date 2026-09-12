import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from plant_id.domain.exceptions import IdentificationError
from plant_id.domain.models import Observation
from plant_id.infrastructure.config.settings import Settings
from plant_id.infrastructure.identification.classical_ml import ClassicalMlIdentificationRepository
from plant_id.infrastructure.identification.vlm_ollama import VlmOllamaIdentificationRepository
from plant_id.infrastructure.species.file_catalog import FileSpeciesCatalog


@pytest.fixture
def settings() -> Settings:
    return Settings()


@pytest.fixture
def catalog(settings: Settings) -> FileSpeciesCatalog:
    return FileSpeciesCatalog(settings.species_catalog_path)


def test_vlm_client_uses_configured_ollama_timeout(
    settings: Settings,
    catalog: FileSpeciesCatalog,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    class FakeClient:
        def __init__(self, host: str | None = None, **kwargs: object) -> None:
            captured["host"] = host
            captured["timeout"] = kwargs.get("timeout")

    monkeypatch.setattr(
        "plant_id.infrastructure.identification.vlm_ollama.Client",
        FakeClient,
    )
    VlmOllamaIdentificationRepository(settings, catalog)
    assert captured["host"] == settings.ollama_host
    assert captured["timeout"] == settings.ollama_timeout_seconds


def test_vlm_parse_result_marks_uncertain_when_confidence_low(
    settings: Settings,
    catalog: FileSpeciesCatalog,
) -> None:
    repo = VlmOllamaIdentificationRepository(settings, catalog, client=MagicMock())
    observation = Observation(observation_id="obs-1", photo_paths=[Path("a.jpg")])
    payload = {
        "predictions": [
            {
                "rank": 1,
                "species_label": "pink primrose",
                "evidence": "soft pink petals",
                "confidence": 0.2,
            }
        ]
    }

    result = repo._parse_result(observation, payload)

    assert result.uncertain is True
    assert result.predictions[0].species_label == "pink primrose"


def test_vlm_parse_result_rejects_unknown_label(
    settings: Settings,
    catalog: FileSpeciesCatalog,
) -> None:
    repo = VlmOllamaIdentificationRepository(settings, catalog, client=MagicMock())
    observation = Observation(observation_id="obs-2", photo_paths=[Path("a.jpg")])

    with pytest.raises(IdentificationError, match="Unknown species_label"):
        repo._parse_result(
            observation,
            {
                "predictions": [
                    {
                        "rank": 1,
                        "species_label": "not a real flower",
                        "evidence": "unknown",
                        "confidence": 0.9,
                    }
                ]
            },
        )


def test_vlm_identify_sends_all_photos_to_ollama(
    settings: Settings,
    catalog: FileSpeciesCatalog,
    tmp_path: Path,
) -> None:
    photo_a = tmp_path / "a.jpg"
    photo_b = tmp_path / "b.jpg"
    photo_a.write_bytes(b"fake")
    photo_b.write_bytes(b"fake")

    client = MagicMock()
    response = MagicMock()
    response.message.content = json.dumps(
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
    response.model_dump.return_value = {"message": {"content": response.message.content}}
    client.chat.return_value = response

    repo = VlmOllamaIdentificationRepository(settings, catalog, client=client)
    observation = Observation(
        observation_id="obs-3",
        photo_paths=[photo_a, photo_b],
    )

    result, raw = repo.identify(observation)

    assert len(result.predictions) == 1
    assert result.uncertain is False
    chat_kwargs = client.chat.call_args.kwargs
    assert chat_kwargs["options"] == {"temperature": 0}
    assert "think" not in chat_kwargs
    images = chat_kwargs["messages"][0]["images"]
    assert len(images) == 2
    assert raw["request"]["photo_paths"] == images


def test_classical_ml_stub_raises_clear_error(
    settings: Settings,
    catalog: FileSpeciesCatalog,
) -> None:
    repo = ClassicalMlIdentificationRepository(settings, catalog)
    observation = Observation(observation_id="obs-4", photo_paths=[Path("a.jpg")])

    with pytest.raises(IdentificationError, match="not implemented"):
        repo.identify(observation)


def test_vlm_identify_emits_stage_events(
    settings: Settings,
    catalog: FileSpeciesCatalog,
    tmp_path: Path,
) -> None:
    from tests.support.recording_events import recording_application_events

    photo = tmp_path / "photo.jpg"
    photo.write_bytes(b"fake-image")
    client = MagicMock()
    response = MagicMock()
    response.message.content = json.dumps(
        {
            "predictions": [
                {
                    "rank": 1,
                    "species_label": "pink primrose",
                    "evidence": "soft pink petals",
                    "confidence": 0.9,
                }
            ]
        }
    )
    response.message.thinking = ""
    response.model_dump.return_value = {"message": {"content": response.message.content}}
    client.chat.return_value = response

    repo = VlmOllamaIdentificationRepository(settings, catalog, client=client)
    observation = Observation(observation_id="obs-progress", photo_paths=[photo])

    with recording_application_events() as events:
        repo.identify(observation)

    stage_calls = [call for call in events.calls if call[0] == "log_stage"]
    wait_calls = [call for call in events.calls if call[0] == "log_wait_begin"]
    assert len(stage_calls) == 3
    assert stage_calls[0][3].startswith("Validated")
    assert wait_calls[0][3].startswith("Calling Ollama")
