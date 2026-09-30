"""Describe + BM25 + text embedding hybrid retrieval — fallback only vs OpenRouter + Qdrant."""

from __future__ import annotations

from pathlib import Path

from plant_id.domain.species_retrieval import RetrievedSpeciesContext
from plant_id.infrastructure.config.settings import Settings
from plant_id.infrastructure.retrieval.bm25_corpus import SheetBm25Index
from plant_id.infrastructure.retrieval.describe_prompt import describe_flower_photos
from plant_id.infrastructure.retrieval.text_embedder import (
    build_text_embedder,
    cosine_similarity,
    embed_sheet_texts,
)
from plant_id.infrastructure.species_sheets.loader import load_all_sheets


class DescribeHybridRetrievalRepository:
    def __init__(
        self,
        settings: Settings,
        *,
        sheets=None,
        bm25: SheetBm25Index | None = None,
        sheet_vectors=None,
    ) -> None:
        self._settings = settings
        self._sheets = sheets or load_all_sheets(settings.species_sheets_dir)
        self._bm25 = bm25 or SheetBm25Index(self._sheets)
        embedder = build_text_embedder(settings)
        self._sheet_vectors = sheet_vectors or embed_sheet_texts(self._sheets, embedder)
        self._embedder = embedder

    @property
    def backend_id(self) -> str:
        return (
            f"describe-hybrid:bm25={self._settings.retrieval_bm25_weight}:"
            f"embed={self._settings.retrieval_embed_weight}"
        )

    def retrieve(
        self,
        photo_paths: tuple[Path, ...],
        k: int,
    ) -> tuple[RetrievedSpeciesContext, ...]:
        description = describe_flower_photos(self._settings, photo_paths)
        bm25_scores = self._bm25.scores(description)
        query_vector = self._embedder.embed(description)
        fused: list[tuple[str, float]] = []
        for label, sheet in self._sheets.items():
            bm25 = bm25_scores.get(label, 0.0)
            semantic = cosine_similarity(query_vector, self._sheet_vectors[label])
            score = (
                self._settings.retrieval_bm25_weight * _normalize_bm25(bm25, bm25_scores)
                + self._settings.retrieval_embed_weight * semantic
            )
            fused.append((label, score))
        fused.sort(key=lambda item: item[1], reverse=True)
        results: list[RetrievedSpeciesContext] = []
        for label, score in fused[:k]:
            sheet = self._sheets[label]
            results.append(
                RetrievedSpeciesContext(
                    catalog_label=label,
                    score=score,
                    context_block=sheet.context_block,
                    retrieval_text=sheet.retrieval_text,
                )
            )
        return tuple(results)


def _normalize_bm25(value: float, scores: dict[str, float]) -> float:
    max_score = max(scores.values()) if scores else 0.0
    min_score = min(scores.values()) if scores else 0.0
    if max_score == min_score:
        return 1.0 if value > 0 else 0.0
    return (value - min_score) / (max_score - min_score)
