from plant_id.infrastructure.config.settings import Settings
from plant_id.interfaces.composition.container import resolve_settings


def test_resolve_settings_returns_defaults_when_no_override() -> None:
    base = Settings(ollama_think=False)
    resolved = resolve_settings(base, ollama_think=None)
    assert resolved is base


def test_resolve_settings_applies_ollama_think_override() -> None:
    base = Settings(ollama_think=False)
    resolved = resolve_settings(base, ollama_think=True)
    assert resolved.ollama_think is True
    assert base.ollama_think is False
