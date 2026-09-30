"""Unit tests for retrieval scoring debug payloads."""

from __future__ import annotations

import json
from pathlib import Path

from eval.retrieval_scoring import score_retrieval_observations

from plant_id.domain.species_retrieval import RetrievedSpeciesContext


class _EvalImage:
    def __init__(self, image_path: Path, ground_truth: str) -> None:
        self.image_path = image_path
        self.ground_truth = ground_truth


class _FakeEvalRepo:
    backend_id = "fake-eval"

    def retrieve_for_eval(self, photo_paths, k, *, raw_hit_cap=10):
        contexts = (
            RetrievedSpeciesContext(
                catalog_label="bolero deep blue",
                score=0.9,
                context_block="ctx",
            ),
        )
        hits = [
            (
                {
                    "catalog_label": "bolero deep blue",
                    "prototype_kind": "image",
                    "prototype_id": "curated-image_07100",
                    "source_image": "/data/image_07100.jpg",
                },
                0.9,
            ),
            (
                {
                    "catalog_label": "canterbury bells",
                    "prototype_kind": "text",
                    "prototype_id": "retrieval_text",
                },
                0.88,
            ),
        ]
        return contexts, hits

    def retrieve(self, photo_paths, k):
        return self.retrieve_for_eval(photo_paths, k)[0]


def test_score_retrieval_persists_prototype_debug(tmp_path: Path) -> None:
    image = tmp_path / "image_06613.jpg"
    image.write_bytes(b"")
    repo = _FakeEvalRepo()
    artifacts_dir = tmp_path / "artifacts"
    metrics = score_retrieval_observations(
        repo,
        [_EvalImage(image, "canterbury bells")],
        top_k=1,
        artifacts_dir=artifacts_dir,
    )
    assert metrics.observation_count == 1
    row = metrics.observations[0]
    assert row.winning_prototypes[0].prototype_kind == "image"
    assert row.raw_hits[0].catalog_label == "bolero deep blue"
    payload = json.loads((artifacts_dir / "image_06613.json").read_text())
    assert payload["winning_prototypes"][0]["prototype_id"] == "curated-image_07100"
    assert len(payload["raw_hits"]) == 2
