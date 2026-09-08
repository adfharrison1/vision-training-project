"""Environment verification CLI command."""

from __future__ import annotations

import sys

from plant_id.interfaces.composition import Settings, load_settings, verify_environment


def run_verify_env(settings: Settings | None = None) -> int:
    settings = settings or load_settings()
    result = verify_environment(settings)
    for message in result.messages:
        print(message, file=sys.stderr if not result.ok else sys.stdout)
    return 0 if result.ok else 1
