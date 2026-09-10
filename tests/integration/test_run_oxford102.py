from pathlib import Path

import pytest
from eval.run_oxford102 import main

from plant_id.infrastructure.config.settings import Settings
from plant_id.infrastructure.ollama.environment import verify_environment


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


@pytest.mark.integration
def test_run_oxford102_smoke_profile() -> None:
    env = verify_environment(Settings())
    if not env.ok:
        pytest.skip(env.messages[-1])

    dataset_root = _project_root() / "data" / "flowers"
    if not (dataset_root / "setid.mat").is_file():
        pytest.skip(f"Oxford dataset not found under {dataset_root}")

    exit_code = main(
        [
            "--profile",
            "smoke",
            "--eval-run-id",
            "integration-smoke",
            "--quiet",
        ]
    )
    assert exit_code == 0
