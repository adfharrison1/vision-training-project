from plant_id.infrastructure.config.settings import Settings
from plant_id.infrastructure.ollama.environment import verify_cloud_vlm_environment


def test_verify_cloud_vlm_fails_without_api_key() -> None:
    settings = Settings(vlm_cloud_api_key=None)
    result = verify_cloud_vlm_environment(settings)
    assert result.ok is False
    assert any("PLANT_ID_VLM_CLOUD_API_KEY" in message for message in result.messages)


def test_verify_cloud_vlm_succeeds_with_configuration() -> None:
    settings = Settings(
        vlm_cloud_api_key="secret",
        vlm_cloud_vendor="fireworks",
    )
    result = verify_cloud_vlm_environment(settings)
    assert result.ok is True
    assert any("Cloud VLM model" in message for message in result.messages)
