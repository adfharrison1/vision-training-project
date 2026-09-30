"""Write retrieval eval failure forensics."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_retrieval_failure_artifact(
    failures_dir: Path,
    *,
    image_path: Path,
    payload: dict[str, Any],
) -> Path:
    failures_dir.mkdir(parents=True, exist_ok=True)
    stem = image_path.stem
    out_path = failures_dir / f"{stem}.json"
    out_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return out_path
