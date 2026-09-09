"""Run identification on the bundled demo sample image."""

from __future__ import annotations

import sys
from pathlib import Path

from plant_id.interfaces.cli.commands.identify import run_identify
from plant_id.interfaces.composition import Backend, Settings, load_settings


def _project_root() -> Path:
    return Path(__file__).resolve().parents[5]


def default_demo_image() -> Path:
    return _project_root() / "data" / "flowers" / "jpg" / "image_00001.jpg"


def run_demo(
    backend: Backend,
    settings: Settings | None = None,
    quiet: bool = False,
) -> int:
    settings = settings or load_settings()
    sample_image = default_demo_image()
    if not sample_image.is_file():
        print(f"Demo image not found: {sample_image}", file=sys.stderr)
        print("Download dataset images to data/flowers/ (see README).", file=sys.stderr)
        return 1

    return run_identify(
        backend=backend,
        photos=str(sample_image),
        observation_id="demo",
        settings=settings,
        quiet=quiet,
    )
