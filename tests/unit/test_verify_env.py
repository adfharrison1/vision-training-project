from unittest.mock import MagicMock, patch

from plant_id.infrastructure.config.settings import Settings
from plant_id.infrastructure.ollama.environment import verify_environment


def test_verify_environment_fails_when_ollama_unreachable() -> None:
    settings = Settings(ollama_host="http://127.0.0.1:59999")
    result = verify_environment(settings)
    assert result.ok is False
    assert any("unreachable" in message.lower() for message in result.messages)


@patch(
    "plant_id.infrastructure.ollama.environment._fetch_ollama_version",
    return_value="0.33.3",
)
@patch("plant_id.infrastructure.ollama.environment.ollama.Client")
def test_verify_environment_succeeds_when_model_present(
    mock_client_cls: MagicMock,
    _mock_version: MagicMock,
) -> None:
    mock_client = mock_client_cls.return_value
    mock_model = MagicMock()
    mock_model.model = "qwen3-vl:8b"
    mock_client.list.return_value = MagicMock(models=[mock_model])

    settings = Settings()
    result = verify_environment(settings)
    assert result.ok is True
    assert any("ready" in message.lower() for message in result.messages)


@patch(
    "plant_id.infrastructure.ollama.environment._fetch_ollama_version",
    return_value="0.33.3",
)
@patch("plant_id.infrastructure.ollama.environment.ollama.Client")
def test_verify_environment_fails_when_model_missing(
    mock_client_cls: MagicMock,
    _mock_version: MagicMock,
) -> None:
    mock_client = mock_client_cls.return_value
    mock_client.list.return_value = MagicMock(models=[])

    settings = Settings()
    result = verify_environment(settings)
    assert result.ok is False
    assert any("ollama pull" in message for message in result.messages)
