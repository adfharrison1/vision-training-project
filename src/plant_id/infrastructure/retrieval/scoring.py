"""Aggregate prototype hits into species-level retrieval results."""

from __future__ import annotations

from collections.abc import Iterable

from plant_id.domain.species_retrieval import RetrievedSpeciesContext


def aggregate_max_per_label(
    hits: Iterable[tuple[dict, float]],
    *,
    k: int,
) -> tuple[RetrievedSpeciesContext, ...]:
    best: dict[str, tuple[float, dict]] = {}
    for payload, score in hits:
        label = str(payload.get("catalog_label", ""))
        if not label:
            continue
        current = best.get(label)
        if current is None or score > current[0]:
            best[label] = (score, payload)
    ranked = sorted(best.items(), key=lambda item: item[1][0], reverse=True)[:k]
    results: list[RetrievedSpeciesContext] = []
    for label, (score, payload) in ranked:
        context_block = str(payload.get("context_block", ""))
        retrieval_text = payload.get("retrieval_text")
        results.append(
            RetrievedSpeciesContext(
                catalog_label=label,
                score=score,
                context_block=context_block,
                retrieval_text=str(retrieval_text) if retrieval_text else None,
            )
        )
    return tuple(results)
