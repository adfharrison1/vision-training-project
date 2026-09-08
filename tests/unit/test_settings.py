from pathlib import Path

from plant_id.infrastructure.config.settings import Settings


def test_settings_defaults_use_project_paths() -> None:
    settings = Settings()
    root = Path(__file__).resolve().parents[2]
    assert settings.class_names_path == root / "resources" / "oxford102" / "class_names.txt"
    assert settings.artifacts_dir == root / "artifacts"
    assert settings.vision_model == "qwen3-vl:8b"
    assert settings.uncertainty_threshold == 0.5
    assert settings.prompt_version == "oxford102-closed-set-v1"


def test_settings_load_from_environment(monkeypatch) -> None:
    monkeypatch.setenv("PLANT_ID_VISION_MODEL", "llava:7b")
    monkeypatch.setenv("PLANT_ID_UNCERTAINTY_THRESHOLD", "0.7")
    settings = Settings()
    assert settings.vision_model == "llava:7b"
    assert settings.uncertainty_threshold == 0.7
