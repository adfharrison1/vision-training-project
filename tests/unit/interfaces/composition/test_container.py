from pathlib import Path

import pytest

from plant_id.domain.exceptions import IdentificationError
from plant_id.domain.models import Observation
from plant_id.infrastructure.identification.classical_ml import ClassicalMlIdentificationRepository
from plant_id.infrastructure.identification.vlm_ollama import VlmOllamaIdentificationRepository
from plant_id.infrastructure.persistence.file_artifacts import FileArtifactRepository
from plant_id.interfaces.composition import build_identify_use_case


def test_build_vlm_use_case_wires_vlm_repository() -> None:
    use_case = build_identify_use_case("vlm")

    assert isinstance(use_case._identification_repo, VlmOllamaIdentificationRepository)
    assert isinstance(use_case._artifact_repo, FileArtifactRepository)


def test_build_classical_use_case_wires_classical_repository() -> None:
    use_case = build_identify_use_case("classical")

    assert isinstance(use_case._identification_repo, ClassicalMlIdentificationRepository)
    assert isinstance(use_case._artifact_repo, FileArtifactRepository)


def test_classical_backend_fails_gracefully() -> None:
    use_case = build_identify_use_case("classical")
    observation = Observation(observation_id="obs-classical", photo_paths=[Path("a.jpg")])

    with pytest.raises(IdentificationError, match="not implemented"):
        use_case.execute(observation)
