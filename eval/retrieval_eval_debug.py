"""Build eval-only retrieval debug payloads from raw prototype search hits."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from eval.retrieval_metrics import PrototypeHitRow
from plant_id.domain.species_retrieval import RetrievedSpeciesContext
from plant_id.infrastructure.retrieval.scoring import aggregate_max_per_label


def hit_to_row(payload: dict, score: float) -> PrototypeHitRow:
    return PrototypeHitRow(
        catalog_label=str(payload.get("catalog_label", "")),
        prototype_kind=_optional_str(payload.get("prototype_kind")),
        prototype_id=_optional_str(payload.get("prototype_id")),
        source_image=_optional_str(payload.get("source_image")),
        score=float(score),
    )


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text if text else None


def best_hit_per_label(hits: Iterable[tuple[dict, float]]) -> dict[str, tuple[dict, float]]:
    best: dict[str, tuple[dict, float]] = {}
    for payload, score in hits:
        label = str(payload.get("catalog_label", ""))
        if not label:
            continue
        current = best.get(label)
        if current is None or score > current[1]:
            best[label] = (payload, score)
    return best


def build_retrieval_eval_debug(
    raw_hits: list[tuple[dict, float]],
    aggregated: tuple[RetrievedSpeciesContext, ...],
    *,
    raw_hit_cap: int = 10,
) -> dict[str, Any]:
    sorted_hits = sorted(raw_hits, key=lambda item: item[1], reverse=True)[:raw_hit_cap]
    raw_rows = tuple(hit_to_row(payload, score) for payload, score in sorted_hits)
    winners_map = best_hit_per_label(raw_hits)
    winning: list[PrototypeHitRow] = []
    for ctx in aggregated:
        payload, score = winners_map.get(ctx.catalog_label, ({}, ctx.score))
        if payload:
            winning.append(hit_to_row(payload, score))
        else:
            winning.append(
                PrototypeHitRow(
                    catalog_label=ctx.catalog_label,
                    score=ctx.score,
                )
            )
    return {
        "raw_hits": raw_rows,
        "winning_prototypes": tuple(winning),
    }


def aggregate_from_hits(
    hits: list[tuple[dict, float]],
    *,
    k: int,
) -> tuple[RetrievedSpeciesContext, ...]:
    return aggregate_max_per_label(hits, k=k)
