"""Environment verification CLI command."""

from __future__ import annotations

import sys

from plant_id.infrastructure.config.settings import Settings
from plant_id.infrastructure.ollama.environment import verify_environment


def run_verify_env(settings: Settings | None = None) -> int:
    result = verify_environment(settings)
    for message in result.messages:
        print(message, file=sys.stderr if not result.ok else sys.stdout)
    return 0 if result.ok else 1
