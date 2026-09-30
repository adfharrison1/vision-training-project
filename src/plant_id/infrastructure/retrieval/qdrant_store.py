"""Qdrant adapter for retrieval index points."""

from __future__ import annotations

from typing import Any

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from plant_id.infrastructure.retrieval.index_manifest import (
    RetrievalIndexManifest,
    load_manifest,
    load_vectors,
    point_id_to_qdrant_id,
)


class QdrantSpeciesStore:
    """Low-level upsert/search against a Qdrant collection."""

    def __init__(self, client: QdrantClient, collection_name: str) -> None:
        self._client = client
        self._collection_name = collection_name

    @property
    def collection_name(self) -> str:
        return self._collection_name

    def ensure_collection(self, *, vector_size: int) -> None:
        exists = self._client.collection_exists(self._collection_name)
        if exists:
            info = self._client.get_collection(self._collection_name)
            current = info.config.params.vectors.size  # type: ignore[union-attr]
            if current != vector_size:
                raise RuntimeError(
                    f"Collection {self._collection_name!r} has dim {current}, "
                    f"expected {vector_size}."
                )
            return
        self._client.create_collection(
            collection_name=self._collection_name,
            vectors_config=qmodels.VectorParams(size=vector_size, distance=qmodels.Distance.COSINE),
        )

    def upsert_manifest(self, manifest: RetrievalIndexManifest, vectors: np.ndarray) -> int:
        self.ensure_collection(vector_size=manifest.embed_dim)
        points: list[qmodels.PointStruct] = []
        for row_index, point in enumerate(manifest.points):
            payload: dict[str, Any] = {
                "catalog_label": point.catalog_label,
                "prototype_kind": point.prototype_kind,
                "prototype_id": point.prototype_id,
                "context_block": point.context_block,
            }
            if point.retrieval_text is not None:
                payload["retrieval_text"] = point.retrieval_text
            if point.source_image is not None:
                payload["source_image"] = point.source_image
            vector = vectors[row_index].tolist()
            points.append(
                qmodels.PointStruct(
                    id=point_id_to_qdrant_id(point.point_id),
                    vector=vector,
                    payload=payload,
                )
            )
        self._client.upsert(collection_name=self._collection_name, points=points)
        return len(points)

    def search(self, query_vector: np.ndarray, limit: int) -> list[tuple[dict[str, Any], float]]:
        response = self._client.query_points(
            collection_name=self._collection_name,
            query=query_vector.tolist(),
            limit=limit,
            with_payload=True,
        )
        hits: list[tuple[dict[str, Any], float]] = []
        for point in response.points:
            payload = dict(point.payload or {})
            hits.append((payload, float(point.score)))
        return hits

    def collection_ready(self) -> bool:
        if not self._client.collection_exists(self._collection_name):
            return False
        info = self._client.get_collection(self._collection_name)
        return info.points_count is not None and info.points_count > 0


def seed_from_index_dir(
    client: QdrantClient,
    *,
    index_dir,
    collection_name: str | None = None,
) -> int:
    from pathlib import Path

    directory = Path(index_dir)
    manifest = load_manifest(directory)
    vectors = load_vectors(directory)
    name = collection_name or manifest.collection_name
    store = QdrantSpeciesStore(client, name)
    return store.upsert_manifest(manifest, vectors)
