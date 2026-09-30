"""Optional Qdrant integration test for OpenRouter-built retrieval index."""

from __future__ import annotations

import pytest
from qdrant_client import QdrantClient

from plant_id.infrastructure.config.settings import Settings
from plant_id.infrastructure.retrieval.index_manifest import load_manifest
from plant_id.infrastructure.retrieval.qdrant_store import QdrantSpeciesStore


@pytest.mark.integration
def test_qdrant_collection_after_seed() -> None:
    settings = Settings()
    client = QdrantClient(url=settings.qdrant_url, timeout=settings.qdrant_timeout_seconds)
    store = QdrantSpeciesStore(client, settings.qdrant_collection)
    try:
        ready = store.collection_ready()
    except Exception:
        pytest.skip("Qdrant not reachable; run ./scripts/qdrant.sh up && seed")
    if not ready:
        pytest.skip("Qdrant collection not seeded; run ./scripts/qdrant.sh seed")
    manifest = load_manifest(settings.retrieval_index_dir)
    assert manifest.embed_dim > 0
