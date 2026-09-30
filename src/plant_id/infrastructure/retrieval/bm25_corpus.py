"""BM25 corpus over species sheet retrieval_text."""

from __future__ import annotations

from rank_bm25 import BM25Okapi

from plant_id.domain.species_retrieval import SpeciesSheet


class SheetBm25Index:
    def __init__(self, sheets: dict[str, SpeciesSheet]) -> None:
        self._labels = list(sheets.keys())
        tokenized = [_tokenize(sheets[label].retrieval_text) for label in self._labels]
        self._bm25 = BM25Okapi(tokenized)

    def scores(self, query: str) -> dict[str, float]:
        query_tokens = _tokenize(query)
        raw = self._bm25.get_scores(query_tokens)
        return {self._labels[index]: float(raw[index]) for index in range(len(self._labels))}


def _tokenize(text: str) -> list[str]:
    return [token for token in text.lower().split() if token.isalpha() or len(token) > 2]
