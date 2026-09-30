"""Shared retrieval scoring for identify and retrieval-only eval runs."""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Protocol

from eval.retrieval_eval_debug import build_retrieval_eval_debug
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


class _EvalRetrievalRepo(_RetrievalRepo, Protocol):
    def retrieve_for_eval(
        self,
        photo_paths: tuple[Path, ...],
        k: int,
        *,
        raw_hit_cap: int = 10,
    ) -> tuple[tuple[RetrievedSpeciesContext, ...], list[tuple[dict, float]]]: ...


RAW_HIT_CAP = 10


def _serialize_hit_rows(rows: tuple) -> list[dict[str, Any]]:
    return [
        {
            "catalog_label": row.catalog_label,
            "prototype_kind": row.prototype_kind,
            "prototype_id": row.prototype_id,
            "source_image": row.source_image,
            "score": row.score,
        }
        for row in rows
    ]


def _retrieve_with_optional_debug(
    repo: _RetrievalRepo,
    photo_paths: tuple[Path, ...],
    top_k: int,
) -> tuple[tuple[RetrievedSpeciesContext, ...], dict[str, Any] | None]:
    retrieve_for_eval = getattr(repo, "retrieve_for_eval", None)
    if callable(retrieve_for_eval):
        contexts, raw_hits = retrieve_for_eval(photo_paths, top_k, raw_hit_cap=RAW_HIT_CAP)
        debug = build_retrieval_eval_debug(raw_hits, contexts, raw_hit_cap=RAW_HIT_CAP)
        return contexts, debug
    contexts = repo.retrieve(photo_paths, top_k)
    return contexts, None


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
            contexts, debug = _retrieve_with_optional_debug(
                repo,
                (image.image_path,),
                top_k,
            )
            labels = tuple(ctx.catalog_label for ctx in contexts)
            scores = tuple(ctx.score for ctx in contexts)
            winning: tuple = ()
            raw_hits: tuple = ()
            if debug is not None:
                winning = debug["winning_prototypes"]
                raw_hits = debug["raw_hits"]
            row = RetrievalObservationRow(
                image=str(image.image_path),
                ground_truth=image.ground_truth,
                retrieved_labels=labels,
                scores=scores,
                recall_at_k={k: recall_at_k(labels, image.ground_truth, k) for k in k_values},
                reciprocal_rank=reciprocal_rank(labels, image.ground_truth),
                winning_prototypes=winning,
                raw_hits=raw_hits,
            )
            rows.append(row)
            if artifacts_dir is not None:
                artifacts_dir.mkdir(parents=True, exist_ok=True)
                artifact: dict[str, Any] = {
                    "image": str(image.image_path),
                    "ground_truth": image.ground_truth,
                    "retrieval_backend": repo.backend_id,
                    "top_k": top_k,
                    "retrieved": [
                        {"catalog_label": ctx.catalog_label, "score": ctx.score}
                        for ctx in contexts
                    ],
                }
                if debug is not None:
                    artifact["winning_prototypes"] = _serialize_hit_rows(winning)
                    artifact["raw_hits"] = _serialize_hit_rows(raw_hits)
                artifact_path = artifacts_dir / f"{image.image_path.stem}.json"
                artifact_path.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
            if failures_dir is not None and not row.recall_at_k.get(top_k, False):
                failure_payload: dict[str, Any] = {
                    "image": str(image.image_path),
                    "ground_truth": image.ground_truth,
                    "retrieval_backend": repo.backend_id,
                    "top_k": top_k,
                    "retrieved": [
                        {"catalog_label": label, "score": score}
                        for label, score in zip(labels, scores, strict=False)
                    ],
                    "failure_reason": f"ground_truth not in top-{top_k}",
                }
                if debug is not None:
                    failure_payload["winning_prototypes"] = _serialize_hit_rows(winning)
                    failure_payload["raw_hits"] = _serialize_hit_rows(raw_hits)
                write_retrieval_failure_artifact(
                    failures_dir,
                    image_path=image.image_path,
                    payload=failure_payload,
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
