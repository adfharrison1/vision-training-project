"""Unit tests for retrieval eval debug helpers."""

from __future__ import annotations

from eval.retrieval_eval_debug import build_retrieval_eval_debug

from plant_id.domain.species_retrieval import RetrievedSpeciesContext


def test_build_retrieval_eval_debug_winning_prototype() -> None:
    raw_hits = [
        (
            {
                "catalog_label": "a",
                "prototype_kind": "text",
                "prototype_id": "retrieval_text",
            },
            0.5,
        ),
        (
            {
                "catalog_label": "a",
                "prototype_kind": "image",
                "prototype_id": "train-00",
                "source_image": "/x.jpg",
            },
            0.9,
        ),
    ]
    aggregated = (
        RetrievedSpeciesContext(catalog_label="a", score=0.9, context_block="ctx"),
    )
    debug = build_retrieval_eval_debug(raw_hits, aggregated, raw_hit_cap=10)
    assert debug["winning_prototypes"][0].prototype_kind == "image"
    assert debug["winning_prototypes"][0].source_image == "/x.jpg"
    assert len(debug["raw_hits"]) == 2
