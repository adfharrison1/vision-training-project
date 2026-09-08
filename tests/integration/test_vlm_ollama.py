from pathlib import Path

import pytest

from plant_id.domain.models import Observation
from plant_id.infrastructure.config.settings import Settings
from plant_id.infrastructure.identification.vlm_ollama import VlmOllamaIdentificationRepository
from plant_id.infrastructure.ollama.environment import verify_environment
from plant_id.infrastructure.species.file_catalog import FileSpeciesCatalog


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


@pytest.mark.integration
def test_vlm_repository_identifies_sample_image() -> None:
    env = verify_environment(Settings())
    if not env.ok:
        pytest.skip(env.messages[-1])

    settings = Settings()
    sample_image = _project_root() / "data" / "flowers" / "jpg" / "image_00001.jpg"
    if not sample_image.is_file():
        pytest.skip(f"Sample image not found: {sample_image}")

    catalog = FileSpeciesCatalog(settings.species_catalog_path)
    repo = VlmOllamaIdentificationRepository(settings, catalog)
    observation = Observation(
        observation_id="integration-1",
        photo_paths=[sample_image],
    )

    result, raw = repo.identify(observation)

    assert result.observation_id == "integration-1"
    assert 1 <= len(result.predictions) <= 3
    assert result.model_tag == settings.vision_model
    assert raw["response"]
