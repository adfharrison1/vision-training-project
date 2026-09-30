"""Multimodal prototype retrieval via OpenRouter Nemotron embeddings."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from qdrant_client import QdrantClient

from plant_id.domain.species_retrieval import RetrievedSpeciesContext
from plant_id.infrastructure.config.settings import Settings
from plant_id.infrastructure.retrieval.in_memory_store import InMemoryVectorStore
from plant_id.infrastructure.retrieval.index_manifest import (
    IndexPoint,
    load_manifest,
    load_vectors,
    manifest_embed_model,
)
from plant_id.infrastructure.retrieval.openrouter_embedder import embed_image_path
from plant_id.infrastructure.retrieval.qdrant_store import QdrantSpeciesStore
from plant_id.infrastructure.retrieval.scoring import aggregate_max_per_label


class NemotronPrototypeRetrievalRepository:
    """Retrieve species sheets via OpenRouter image embeddings vs stored prototypes."""

    def __init__(
        self,
        settings: Settings,
        *,
        store: QdrantSpeciesStore | InMemoryVectorStore,
        embed_model: str,
    ) -> None:
        self._settings = settings
        self._store = store
        self._embed_model = embed_model

    @property
    def backend_id(self) -> str:
        return f"nemotron-prototype:{self._embed_model}"

    def retrieve(
        self,
        photo_paths: tuple[Path, ...],
        k: int,
    ) -> tuple[RetrievedSpeciesContext, ...]:
        if k < 1:
            raise ValueError("k must be at least 1.")
        limit = max(k * self._settings.retrieval_search_multiplier, k)
        best_hits: list[tuple[dict, float]] = []
        for path in photo_paths:
            query = embed_image_path(self._settings, path)
            best_hits.extend(self._search(query, limit))
        return aggregate_max_per_label(best_hits, k=k)

    def retrieve_for_eval(
        self,
        photo_paths: tuple[Path, ...],
        k: int,
        *,
        raw_hit_cap: int = 10,
    ) -> tuple[tuple[RetrievedSpeciesContext, ...], list[tuple[dict, float]]]:
        """Same as retrieve but also return merged raw hits for eval debug artifacts."""
        if k < 1:
            raise ValueError("k must be at least 1.")
        limit = max(k * self._settings.retrieval_search_multiplier, k)
        best_hits: list[tuple[dict, float]] = []
        for path in photo_paths:
            query = embed_image_path(self._settings, path)
            best_hits.extend(self._search(query, limit))
        contexts = aggregate_max_per_label(best_hits, k=k)
        return contexts, best_hits

    def _search(self, query_vector: np.ndarray, limit: int) -> list[tuple[dict, float]]:
        if isinstance(self._store, InMemoryVectorStore):
            scored = self._store.search(query_vector, limit)
            return [(payload_from_index_point(item.point), item.score) for item in scored]
        return self._store.search(query_vector, limit)


def payload_from_index_point(point: IndexPoint) -> dict:
    payload: dict = {
        "catalog_label": point.catalog_label,
        "prototype_kind": point.prototype_kind,
        "prototype_id": point.prototype_id,
        "context_block": point.context_block,
        "retrieval_text": point.retrieval_text,
    }
    if point.source_image is not None:
        payload["source_image"] = point.source_image
    return payload


def build_in_memory_nemotron_repo(settings: Settings) -> NemotronPrototypeRetrievalRepository:
    index_dir = settings.retrieval_index_dir
    manifest = load_manifest(index_dir)
    vectors = load_vectors(index_dir)
    store = InMemoryVectorStore(points=manifest.points, vectors=vectors)
    return NemotronPrototypeRetrievalRepository(
        settings,
        store=store,
        embed_model=manifest_embed_model(manifest),
    )


def build_qdrant_nemotron_repo(settings: Settings) -> NemotronPrototypeRetrievalRepository:
    client = QdrantClient(url=settings.qdrant_url, timeout=settings.qdrant_timeout_seconds)
    store = QdrantSpeciesStore(client, settings.qdrant_collection)
    manifest = load_manifest(settings.retrieval_index_dir)
    return NemotronPrototypeRetrievalRepository(
        settings,
        store=store,
        embed_model=manifest_embed_model(manifest),
    )
