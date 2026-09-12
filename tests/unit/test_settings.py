from pathlib import Path

from plant_id.infrastructure.config.settings import Settings


def test_settings_defaults_use_project_paths() -> None:
    settings = Settings()
    root = Path(__file__).resolve().parents[2]
    assert settings.species_catalog_path == root / "resources" / "species_catalog" / "default.txt"
    assert settings.artifacts_dir == root / "artifacts"
    assert settings.vision_model == "qwen3-vl:2b"
    assert settings.uncertainty_threshold == 0.5
    assert settings.prompt_version == "closed-set-v2"
    assert settings.ollama_timeout_seconds == 600.0


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
