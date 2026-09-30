"""In-memory vector store for unit tests."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from plant_id.infrastructure.retrieval.index_manifest import IndexPoint


@dataclass
class ScoredPoint:
    point: IndexPoint
    score: float


class InMemoryVectorStore:
    """Cosine similarity search over L2-normalized vectors."""

    def __init__(
        self,
        *,
        points: tuple[IndexPoint, ...],
        vectors: np.ndarray,
    ) -> None:
        if len(points) != vectors.shape[0]:
            raise ValueError("points and vectors row count must match.")
        self._points = points
        self._vectors = _l2_normalize(vectors)

    def search(self, query_vector: np.ndarray, limit: int) -> list[ScoredPoint]:
        if query_vector.ndim != 1:
            raise ValueError("query_vector must be 1-D.")
        query = _l2_normalize(query_vector.reshape(1, -1))[0]
        scores = self._vectors @ query
        order = np.argsort(-scores)[:limit]
        return [
            ScoredPoint(point=self._points[int(index)], score=float(scores[int(index)]))
            for index in order
        ]


def _l2_normalize(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1.0, norms)
    return matrix / norms
