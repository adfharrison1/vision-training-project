"""Text embedding for describe-hybrid fallback (optional sentence-transformers)."""

from __future__ import annotations

import re

import numpy as np

from plant_id.domain.species_retrieval import SpeciesSheet


class TextEmbedder:
    def embed(self, text: str) -> np.ndarray: ...


class HashingTextEmbedder:
    """Deterministic bag-of-words hashing embedder (tests / platforms without torch)."""

    def __init__(self, *, dimensions: int = 256) -> None:
        self._dimensions = dimensions

    def embed(self, text: str) -> np.ndarray:
        vector = np.zeros(self._dimensions, dtype=np.float32)
        for token in _tokens(text):
            index = hash(token) % self._dimensions
            vector[index] += 1.0
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector /= norm
        return vector


class SentenceTransformerEmbedder:
    def __init__(self, model_name: str) -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "sentence-transformers is not installed. Use describe-hybrid on a platform "
                "with optional retrieval ML deps, or rely on BM25-only weights."
            ) from exc
        self._model = SentenceTransformer(model_name)

    def embed(self, text: str) -> np.ndarray:
        vector = self._model.encode(text, normalize_embeddings=True)
        return np.asarray(vector, dtype=np.float32)


def build_text_embedder(settings) -> TextEmbedder:
    model_name = settings.retrieval_text_embed_model
    if settings.retrieval_text_embed_backend == "hashing":
        return HashingTextEmbedder()
    return SentenceTransformerEmbedder(model_name)


def embed_sheet_texts(
    sheets: dict[str, SpeciesSheet],
    embedder: TextEmbedder,
) -> dict[str, np.ndarray]:
    return {label: embedder.embed(sheet.retrieval_text) for label, sheet in sheets.items()}


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b))


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z']+", text.lower())
