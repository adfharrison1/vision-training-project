"""Unit tests for describe-hybrid fusion."""

from __future__ import annotations

from pathlib import Path

from plant_id.domain.species_retrieval import SpeciesSheet
from plant_id.infrastructure.config.settings import Settings
from plant_id.infrastructure.retrieval.bm25_corpus import SheetBm25Index
from plant_id.infrastructure.retrieval.describe_hybrid_backend import (
    DescribeHybridRetrievalRepository,
)
from plant_id.infrastructure.retrieval.text_embedder import HashingTextEmbedder, embed_sheet_texts


def test_describe_hybrid_ranks_matching_sheet(monkeypatch, tmp_path: Path) -> None:
    sheets = {
        "alpha": SpeciesSheet(
            catalog_label="alpha",
            retrieval_text="deep violet bell shaped campanula flowers",
            context_block="alpha notes",
        ),
        "beta": SpeciesSheet(
            catalog_label="beta",
            retrieval_text="yellow composite daisy head",
            context_block="beta notes",
        ),
    }
    settings = Settings(
        retrieval_bm25_weight=1.0,
        retrieval_embed_weight=0.0,
        retrieval_text_embed_backend="hashing",
    )
    embedder = HashingTextEmbedder()
    repo = DescribeHybridRetrievalRepository(
        settings,
        sheets=sheets,
        bm25=SheetBm25Index(sheets),
        sheet_vectors=embed_sheet_texts(sheets, embedder),
    )
    photo = tmp_path / "photo.jpg"
    photo.write_bytes(b"x")
    monkeypatch.setattr(
        "plant_id.infrastructure.retrieval.describe_hybrid_backend.describe_flower_photos",
        lambda *_args, **_kwargs: "violet bell shaped campanula",
    )
    results = repo.retrieve((photo,), k=1)
    assert results[0].catalog_label == "alpha"
