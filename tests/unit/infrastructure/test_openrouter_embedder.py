"""Unit tests for OpenRouter Nemotron embedding client."""

from __future__ import annotations

from unittest.mock import MagicMock

import numpy as np
import pytest

from plant_id.infrastructure.config.settings import Settings
from plant_id.infrastructure.retrieval.openrouter_embedder import (
    OpenRouterEmbeddingError,
    embed_text,
)


def test_embed_text_normalizes_vector() -> None:
    settings = Settings(
        vlm_openrouter_api_key="sk-test",
        retrieval_embed_model="nvidia/llama-nemotron-embed-vl-1b-v2:free",
    )
    client = MagicMock()
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {"data": [{"embedding": [3.0, 4.0]}]}
    client.post.return_value = response

    vector = embed_text(settings, "campanula bells", client=client)

    assert vector.shape == (2,)
    assert abs(float(np.linalg.norm(vector)) - 1.0) < 1e-5
    client.post.assert_called_once()
    payload = client.post.call_args.kwargs["json"]
    assert payload["model"] == settings.retrieval_embed_model
    assert payload["input"] == "campanula bells"


def test_embed_text_raises_on_http_error() -> None:
    settings = Settings(vlm_openrouter_api_key="sk-test")
    client = MagicMock()
    response = MagicMock()
    response.status_code = 401
    response.text = "Unauthorized"
    client.post.return_value = response

    with pytest.raises(OpenRouterEmbeddingError, match="401"):
        embed_text(settings, "x", client=client)


def test_embed_text_requires_api_key() -> None:
    settings = Settings(vlm_openrouter_api_key=None)
    with pytest.raises(OpenRouterEmbeddingError, match="PLANT_ID_VLM_OPENROUTER_API_KEY"):
        embed_text(settings, "x", client=MagicMock())
