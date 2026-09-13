import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from plant_id.domain.exceptions import IdentificationError
from plant_id.domain.models import Observation
from plant_id.infrastructure.config.settings import Settings
from plant_id.infrastructure.identification.classical_ml import ClassicalMlIdentificationRepository
from plant_id.infrastructure.identification.vlm_ollama import (
    CONTENT_RETRY_SUFFIX,
    VlmOllamaIdentificationRepository,
)
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
    assert chat_kwargs["think"] is False
    images = chat_kwargs["messages"][0]["images"]
    assert len(images) == 2
    assert raw["request"]["photo_paths"] == images
    assert raw["request"]["think"] is False


def test_vlm_identify_honors_ollama_think_setting(
    catalog: FileSpeciesCatalog,
    tmp_path: Path,
) -> None:
    photo = tmp_path / "photo.jpg"
    photo.write_bytes(b"fake")
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

    settings = Settings(ollama_think=True)
    repo = VlmOllamaIdentificationRepository(settings, catalog, client=client)
    observation = Observation(observation_id="obs-think", photo_paths=[photo])

    repo.identify(observation)

    assert client.chat.call_args.kwargs["think"] is True


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


def _valid_prediction_payload(
    *,
    species_label: str = "pink primrose",
    evidence: str = "pink petals",
    confidence: float = 0.95,
) -> dict[str, object]:
    return {
        "predictions": [
            {
                "rank": 1,
                "species_label": species_label,
                "evidence": evidence,
                "confidence": confidence,
            }
        ]
    }


def _mock_response(
    *,
    content: str = "",
    thinking: str = "",
    done_reason: str | None = None,
) -> MagicMock:
    response = MagicMock()
    response.message.content = content
    response.message.thinking = thinking
    response.done_reason = done_reason
    response.model_dump.return_value = {
        "message": {"content": content, "thinking": thinking},
        "done_reason": done_reason,
    }
    return response


def test_thinking_has_parseable_predictions() -> None:
    valid = json.dumps(_valid_prediction_payload())
    assert VlmOllamaIdentificationRepository._thinking_has_parseable_predictions(valid)
    assert not VlmOllamaIdentificationRepository._thinking_has_parseable_predictions("")
    assert not VlmOllamaIdentificationRepository._thinking_has_parseable_predictions(
        '{"predictions": []}'
    )
    assert not VlmOllamaIdentificationRepository._thinking_has_parseable_predictions("not json")


def test_json_in_thinking_triggers_retry_and_uses_retry_content(
    settings: Settings,
    catalog: FileSpeciesCatalog,
    tmp_path: Path,
) -> None:
    photo = tmp_path / "photo.jpg"
    photo.write_bytes(b"fake")
    thinking_json = json.dumps(_valid_prediction_payload(species_label="tiger lily"))
    retry_content = json.dumps(_valid_prediction_payload(species_label="pink primrose"))

    client = MagicMock()
    client.chat.side_effect = [
        _mock_response(content="", thinking=thinking_json),
        _mock_response(content=retry_content),
    ]

    repo = VlmOllamaIdentificationRepository(settings, catalog, client=client)
    observation = Observation(observation_id="obs-retry-success", photo_paths=[photo])

    result, raw = repo.identify(observation)

    assert client.chat.call_count == 2
    assert CONTENT_RETRY_SUFFIX in client.chat.call_args_list[1].kwargs["messages"][0]["content"]
    assert result.predictions[0].species_label == "pink primrose"
    assert raw["retry"]["attempted"] is True
    assert raw["retry"]["reason"] == "json_in_thinking"


def test_json_in_thinking_retry_falls_back_to_first_thinking(
    settings: Settings,
    catalog: FileSpeciesCatalog,
    tmp_path: Path,
) -> None:
    photo = tmp_path / "photo.jpg"
    photo.write_bytes(b"fake")
    thinking_json = json.dumps(_valid_prediction_payload(species_label="tiger lily"))

    client = MagicMock()
    client.chat.side_effect = [
        _mock_response(content="", thinking=thinking_json),
        _mock_response(content="", thinking=""),
    ]

    repo = VlmOllamaIdentificationRepository(settings, catalog, client=client)
    observation = Observation(observation_id="obs-retry-fallback", photo_paths=[photo])

    result, raw = repo.identify(observation)

    assert client.chat.call_count == 2
    assert result.predictions[0].species_label == "tiger lily"
    assert raw["retry"]["reason"] == "json_in_thinking"


def test_content_retry_disabled_uses_thinking_fallback_only(
    catalog: FileSpeciesCatalog,
    tmp_path: Path,
) -> None:
    photo = tmp_path / "photo.jpg"
    photo.write_bytes(b"fake")
    thinking_json = json.dumps(_valid_prediction_payload())

    client = MagicMock()
    client.chat.return_value = _mock_response(content="", thinking=thinking_json)

    settings = Settings(ollama_content_retry_enabled=False)
    repo = VlmOllamaIdentificationRepository(settings, catalog, client=client)
    observation = Observation(observation_id="obs-no-retry", photo_paths=[photo])

    result, raw = repo.identify(observation)

    assert client.chat.call_count == 1
    assert result.predictions[0].species_label == "pink primrose"
    assert "retry" not in raw


def test_wholly_empty_response_triggers_retry(
    settings: Settings,
    catalog: FileSpeciesCatalog,
    tmp_path: Path,
) -> None:
    photo = tmp_path / "photo.jpg"
    photo.write_bytes(b"fake")
    retry_content = json.dumps(_valid_prediction_payload(species_label="tiger lily"))

    client = MagicMock()
    client.chat.side_effect = [
        _mock_response(content="", thinking=""),
        _mock_response(content=retry_content),
    ]

    repo = VlmOllamaIdentificationRepository(settings, catalog, client=client)
    observation = Observation(observation_id="obs-empty-retry", photo_paths=[photo])

    result, raw = repo.identify(observation)

    assert client.chat.call_count == 2
    assert result.predictions[0].species_label == "tiger lily"
    assert raw["retry"]["reason"] == "empty_response"
