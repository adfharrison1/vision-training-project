from pathlib import Path

from plant_id.infrastructure.config.settings import Settings


def test_settings_defaults_use_project_paths() -> None:
    settings = Settings()
    root = Path(__file__).resolve().parents[2]
    assert settings.species_catalog_path == root / "resources" / "species_catalog" / "default.txt"
    assert settings.identify_artifacts_dir == root / "identify_artifacts"
    assert settings.eval_runs_dir == root / "eval_runs"
    assert settings.vision_model == "qwen3-vl:2b"
    assert settings.uncertainty_threshold == 0.5
    assert settings.prompt_version == "closed-set-v4.3"
    assert settings.ollama_timeout_seconds == 600.0
    assert settings.ollama_think is False
    assert settings.ollama_content_retry_enabled is True


def test_settings_load_from_environment(monkeypatch) -> None:
    monkeypatch.setenv("PLANT_ID_VISION_MODEL", "llava:7b")
    monkeypatch.setenv("PLANT_ID_UNCERTAINTY_THRESHOLD", "0.7")
    settings = Settings()
    assert settings.vision_model == "llava:7b"
    assert settings.uncertainty_threshold == 0.7


def test_settings_opik_defaults_and_env(monkeypatch) -> None:
    monkeypatch.delenv("PLANT_ID_OPIK_ENABLED", raising=False)
    monkeypatch.delenv("PLANT_ID_OPIK_BASE_URL", raising=False)
    monkeypatch.delenv("PLANT_ID_OPIK_PROJECT_NAME", raising=False)
    settings = Settings()
    assert settings.opik_enabled is False
    assert settings.opik_base_url == "http://127.0.0.1:5173/api"
    assert settings.opik_project_name == "plant-id"

    monkeypatch.setenv("PLANT_ID_OPIK_ENABLED", "true")
    monkeypatch.setenv("PLANT_ID_OPIK_BASE_URL", "http://127.0.0.1:9999/api")
    monkeypatch.setenv("PLANT_ID_OPIK_PROJECT_NAME", "test-project")
    settings = Settings()
    assert settings.opik_enabled is True
    assert settings.opik_base_url == "http://127.0.0.1:9999/api"
    assert settings.opik_project_name == "test-project"


def test_settings_ollama_think_from_environment(monkeypatch) -> None:
    monkeypatch.delenv("PLANT_ID_OLLAMA_THINK", raising=False)
    assert Settings().ollama_think is False

    monkeypatch.setenv("PLANT_ID_OLLAMA_THINK", "true")
    assert Settings().ollama_think is True


def test_settings_ollama_content_retry_from_environment(monkeypatch) -> None:
    monkeypatch.delenv("PLANT_ID_OLLAMA_CONTENT_RETRY_ENABLED", raising=False)
    assert Settings().ollama_content_retry_enabled is True

    monkeypatch.setenv("PLANT_ID_OLLAMA_CONTENT_RETRY_ENABLED", "false")
    assert Settings().ollama_content_retry_enabled is False


def test_settings_vlm_cloud_defaults_and_env(monkeypatch) -> None:
    monkeypatch.delenv("PLANT_ID_VLM_CLOUD_API_KEY", raising=False)
    monkeypatch.delenv("PLANT_ID_VLM_CLOUD_BASE_URL", raising=False)
    monkeypatch.delenv("PLANT_ID_VLM_CLOUD_MODEL", raising=False)
    monkeypatch.delenv("PLANT_ID_VLM_CLOUD_VENDOR", raising=False)
    monkeypatch.delenv("PLANT_ID_VLM_CLOUD_TIMEOUT_SECONDS", raising=False)
    monkeypatch.delenv("PLANT_ID_VLM_CLOUD_REASONING_EFFORT", raising=False)

    settings = Settings()
    assert settings.vlm_cloud_api_key is None
    assert settings.vlm_cloud_base_url == "https://api.fireworks.ai/inference/v1"
    assert settings.vlm_cloud_model == "accounts/fireworks/models/qwen3-vl-8b-instruct"
    assert settings.vlm_cloud_timeout_seconds == 120.0
    assert settings.vlm_cloud_vendor is None
    assert settings.vlm_cloud_reasoning_effort == "none"

    monkeypatch.setenv("PLANT_ID_VLM_CLOUD_API_KEY", "cloud-key")
    monkeypatch.setenv("PLANT_ID_VLM_CLOUD_BASE_URL", "https://custom.example/v1")
    monkeypatch.setenv("PLANT_ID_VLM_CLOUD_MODEL", "custom-model")
    monkeypatch.setenv("PLANT_ID_VLM_CLOUD_VENDOR", "fireworks")
    monkeypatch.setenv("PLANT_ID_VLM_CLOUD_TIMEOUT_SECONDS", "90")
    monkeypatch.setenv("PLANT_ID_VLM_CLOUD_REASONING_EFFORT", "high")

    settings = Settings()
    assert settings.vlm_cloud_api_key == "cloud-key"
    assert settings.vlm_cloud_base_url == "https://custom.example/v1"
    assert settings.vlm_cloud_model == "custom-model"
    assert settings.vlm_cloud_vendor == "fireworks"
    assert settings.vlm_cloud_timeout_seconds == 90.0
    assert settings.vlm_cloud_reasoning_effort == "high"


def test_settings_invalid_label_retry_from_environment(monkeypatch) -> None:
    monkeypatch.delenv("PLANT_ID_INVALID_LABEL_RETRY_ENABLED", raising=False)
    assert Settings().invalid_label_retry_enabled is True

    monkeypatch.setenv("PLANT_ID_INVALID_LABEL_RETRY_ENABLED", "false")
    assert Settings().invalid_label_retry_enabled is False
