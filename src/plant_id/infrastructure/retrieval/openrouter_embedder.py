"""OpenRouter multimodal embeddings (Nemotron VL) — no local torch."""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Any

import httpx
import numpy as np

from plant_id.infrastructure.config.settings import Settings

DEFAULT_OPENROUTER_EMBED_MODEL = "nvidia/llama-nemotron-embed-vl-1b-v2:free"


class OpenRouterEmbeddingError(RuntimeError):
    """Raised when OpenRouter embedding requests fail."""


def _require_api_key(settings: Settings) -> str:
    key = settings.vlm_openrouter_api_key
    if not key:
        raise OpenRouterEmbeddingError(
            "OpenRouter embeddings require PLANT_ID_VLM_OPENROUTER_API_KEY."
        )
    return key


def _headers(settings: Settings) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {_require_api_key(settings)}",
        "Content-Type": "application/json",
        "HTTP-Referer": settings.openrouter_http_referer,
        "X-Title": settings.openrouter_app_title,
    }


def _embeddings_url(settings: Settings) -> str:
    return f"{settings.openrouter_base_url.rstrip('/')}/embeddings"


def _normalize(vector: np.ndarray) -> np.ndarray:
    norm = float(np.linalg.norm(vector))
    if norm == 0:
        return vector
    return vector / norm


def _parse_embedding(body: dict[str, Any]) -> np.ndarray:
    data = body.get("data")
    if not isinstance(data, list) or not data:
        raise OpenRouterEmbeddingError(f"Missing embedding data in response: {body!r}")
    row = data[0]
    if not isinstance(row, dict) or "embedding" not in row:
        raise OpenRouterEmbeddingError(f"Invalid embedding row: {row!r}")
    values = row["embedding"]
    if not isinstance(values, list):
        raise OpenRouterEmbeddingError("Embedding vector must be a list of floats.")
    return _normalize(np.asarray(values, dtype=np.float32))


def embed_text(
    settings: Settings,
    text: str,
    *,
    client: httpx.Client | None = None,
) -> np.ndarray:
    model = settings.retrieval_embed_model
    payload = {
        "model": model,
        "input": text,
        "encoding_format": "float",
    }
    return _post(settings, payload, client=client)


def embed_image_path(
    settings: Settings,
    path: Path,
    *,
    client: httpx.Client | None = None,
) -> np.ndarray:
    file_path = path.resolve()
    if not file_path.is_file():
        raise FileNotFoundError(f"Image not found: {file_path}")
    suffix = file_path.suffix.lower()
    mime = "image/jpeg" if suffix in {".jpg", ".jpeg", ""} else "image/png"
    encoded = base64.standard_b64encode(file_path.read_bytes()).decode("ascii")
    data_uri = f"data:{mime};base64,{encoded}"
    payload = {
        "model": settings.retrieval_embed_model,
        "input": [
            {
                "content": [
                    {"type": "image_url", "image_url": {"url": data_uri}},
                ]
            }
        ],
        "encoding_format": "float",
    }
    return _post(settings, payload, client=client)


def _post(
    settings: Settings,
    payload: dict[str, Any],
    *,
    client: httpx.Client | None,
) -> np.ndarray:
    url = _embeddings_url(settings)
    timeout = settings.openrouter_timeout_seconds
    if client is not None:
        response = client.post(url, headers=_headers(settings), json=payload, timeout=timeout)
    else:
        with httpx.Client(timeout=timeout) as session:
            response = session.post(url, headers=_headers(settings), json=payload)
    if response.status_code >= 400:
        raise OpenRouterEmbeddingError(
            f"OpenRouter embeddings failed ({response.status_code}): {response.text[:500]}"
        )
    return _parse_embedding(response.json())
