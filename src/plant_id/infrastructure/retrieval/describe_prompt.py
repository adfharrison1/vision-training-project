"""Neutral flower description for retrieval (no catalog labels)."""

from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any

from openai import OpenAI

from plant_id.domain.exceptions import IdentificationError
from plant_id.infrastructure.config.settings import Settings

DESCRIBE_PROMPT = """Describe the flowering plant visible in the photograph(s).

Return ONLY valid JSON:
{{"description": "<neutral botanical description>"}}

Rules:
- Do NOT identify the species or use cultivar names.
- Do NOT list candidate species names.
- Focus on flower shape, colour, inflorescence, and leaf traits visible.
"""


def _image_data_uri(path: str) -> str:
    file_path = Path(path)
    suffix = file_path.suffix.lower()
    mime = "image/jpeg" if suffix in {".jpg", ".jpeg", ""} else "image/png"
    encoded = base64.standard_b64encode(file_path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def describe_flower_photos(
    settings: Settings,
    photo_paths: tuple[Path, ...],
    *,
    client: OpenAI | None = None,
) -> str:
    if not settings.vlm_cloud_api_key:
        raise IdentificationError(
            "describe-hybrid requires PLANT_ID_VLM_CLOUD_API_KEY for neutral describe."
        )
    openai_client = client or OpenAI(
        base_url=settings.vlm_cloud_base_url,
        api_key=settings.vlm_cloud_api_key,
        timeout=settings.vlm_cloud_timeout_seconds,
    )
    content: list[dict[str, Any]] = [{"type": "text", "text": DESCRIBE_PROMPT}]
    for path in photo_paths:
        resolved = str(path.resolve())
        if not Path(resolved).is_file():
            raise IdentificationError(f"Photo not found: {resolved}")
        content.append(
            {"type": "image_url", "image_url": {"url": _image_data_uri(resolved)}}
        )
    response = openai_client.chat.completions.create(
        model=settings.vlm_cloud_model,
        messages=[{"role": "user", "content": content}],
        temperature=0,
    )
    text = response.choices[0].message.content or ""
    payload = json.loads(text)
    description = payload.get("description")
    if not isinstance(description, str) or not description.strip():
        raise IdentificationError("Describe model returned invalid JSON (missing description).")
    return description.strip()
