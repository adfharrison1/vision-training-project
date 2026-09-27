"""Environment verification CLI command."""

from __future__ import annotations

import sys

from plant_id.interfaces.composition import (
    Backend,
    Settings,
    load_settings,
    verify_cloud_vlm_environment,
    verify_environment,
)


def run_verify_env(
    settings: Settings | None = None,
    *,
    backend: Backend = "vlm",
) -> int:
    settings = settings or load_settings()
    if backend == "vlm-cloud":
        result = verify_cloud_vlm_environment(settings)
    else:
        result = verify_environment(settings)
    for message in result.messages:
        print(message, file=sys.stderr if not result.ok else sys.stdout)
    return 0 if result.ok else 1
