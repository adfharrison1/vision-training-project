"""Shared retrieval scoring for identify and retrieval-only eval runs."""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Protocol

from eval.retrieval_failure_forensics import write_retrieval_failure_artifact
from eval.retrieval_metrics import (
    RetrievalMetrics,
    RetrievalObservationRow,
    compute_retrieval_metrics,
    recall_at_k,
    reciprocal_rank,
)
from plant_id.domain.species_retrieval import RetrievedSpeciesContext


class _EvalImage(Protocol):
    image_path: Path
    ground_truth: str


class _RetrievalRepo(Protocol):
    backend_id: str

    def retrieve(
        self,
        photo_paths: tuple[Path, ...],
        top_k: int,
    ) -> tuple[RetrievedSpeciesContext, ...]: ...


def score_retrieval_observations(
    repo: _RetrievalRepo,
    images: Sequence[_EvalImage],
    *,
    top_k: int,
    k_values: tuple[int, ...] = (1, 3, 5),
    artifacts_dir: Path | None = None,
    failures_dir: Path | None = None,
) -> RetrievalMetrics:
    rows: list[RetrievalObservationRow] = []
    for image in images:
        try:
            contexts = repo.retrieve((image.image_path,), top_k)
            labels = tuple(ctx.catalog_label for ctx in contexts)
            scores = tuple(ctx.score for ctx in contexts)
            row = RetrievalObservationRow(
                image=str(image.image_path),
                ground_truth=image.ground_truth,
                retrieved_labels=labels,
                scores=scores,
                recall_at_k={k: recall_at_k(labels, image.ground_truth, k) for k in k_values},
                reciprocal_rank=reciprocal_rank(labels, image.ground_truth),
            )
            rows.append(row)
            if artifacts_dir is not None:
                artifact = {
                    "image": str(image.image_path),
                    "ground_truth": image.ground_truth,
                    "retrieval_backend": repo.backend_id,
                    "top_k": top_k,
                    "retrieved": [
                        {"catalog_label": ctx.catalog_label, "score": ctx.score}
                        for ctx in contexts
                    ],
                }
                artifact_path = artifacts_dir / f"{image.image_path.stem}.json"
                artifact_path.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
            if failures_dir is not None and not row.recall_at_k.get(top_k, False):
                write_retrieval_failure_artifact(
                    failures_dir,
                    image_path=image.image_path,
                    payload={
                        "image": str(image.image_path),
                        "ground_truth": image.ground_truth,
                        "retrieval_backend": repo.backend_id,
                        "top_k": top_k,
                        "retrieved": [
                            {"catalog_label": label, "score": score}
                            for label, score in zip(labels, scores, strict=False)
                        ],
                        "failure_reason": f"ground_truth not in top-{top_k}",
                    },
                )
        except Exception as exc:
            rows.append(
                RetrievalObservationRow(
                    image=str(image.image_path),
                    ground_truth=image.ground_truth,
                    retrieved_labels=(),
                    scores=(),
                    recall_at_k={k: False for k in k_values},
                    reciprocal_rank=0.0,
                    error=str(exc),
                )
            )
    return compute_retrieval_metrics(rows, k_values=k_values)
