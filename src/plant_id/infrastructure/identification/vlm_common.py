"""Shared closed-set VLM prompt and response parsing for local and cloud backends."""

from __future__ import annotations

from typing import Any

from plant_id.domain.exceptions import IdentificationError
from plant_id.domain.models import Observation, ObservationResult, Prediction
from plant_id.domain.repositories import SpeciesCatalogRepository
from plant_id.infrastructure.config.settings import Settings

PROMPT_TEMPLATE = """Identify the flowering plant in the photograph(s).

Return ONLY valid JSON: root object MUST be {{"predictions": [{{...}}, ...]}} — \
never a bare prediction object at the root.
Example shape:
{{
  "predictions": [
    {{
      "rank": 1,
      "species_label": "<exact class name>",
      "evidence": "<brief visual evidence>",
      "confidence": 0.0
    }}
  ]
}}

Rules:
- Provide 1 to 3 predictions ranked by confidence; use ranks 1, 2, and 3 \
consecutively with no gaps.
- species_label MUST match one allowed class name exactly (case and spelling), \
including cultivar or variety names when they appear in the list—never substitute \
a different common name that is not on the list.
- Do not choose species_label from colour or vague shape alone (e.g. "daisy-like", \
"bell-shaped"). In evidence, cite diagnostic structure: petal count or fusion, \
inflorescence type (single flower vs composite head), leaf arrangement, and \
distinctive parts (spur, hood, capsule, etc.).
- Prefer the allowed name best supported by visible diagnostic traits.
- When the allowed list contains both a general and a more specific name for the \
same plant type (e.g. marigold and english marigold), rank 1 must be the general \
name if the photo matches it; use the more specific allowed name at rank 1 only \
when evidence cites traits the general name would not cover. If both plausibly fit, \
list the general name first and the specific name at rank 2 with contrasting \
evidence.
- After you choose a broad species_label, scan the allowed list for narrower \
entries for the same flower type (cultivar, variety, or color or form in the \
name, often multi-word). If any plausibly match the photo, include at least one \
in your predictions at rank 2 or 3—even when rank 1 stays the broader name. \
Missing a matching allowed cultivar or qualified name is worse than listing it \
at rank 2 or 3 with lower confidence.
- If two or more allowed names share the same broad flower type, rank 1 is the \
label whose evidence cites the most specific visible trait; put the next-best \
label at rank 2 with evidence that contrasts why it is less likely. List up to \
3 distinct species_label values when multiple names plausibly fit.
- confidence is a number from 0.0 to 1.0 for each prediction.
- Put only the JSON object in your reply — no markdown, commentary, or long reasoning.

Allowed class names:
{class_names}
"""

INVALID_LABEL_RETRY_SUFFIX = (
    "Your previous JSON used a species_label that is NOT in the allowed list. "
    "Return ONLY valid JSON again. Every species_label MUST match one allowed "
    "class name exactly (case and spelling)."
)


def is_unknown_species_label_error(exc: BaseException) -> bool:
    return isinstance(exc, IdentificationError) and str(exc).startswith("Unknown species_label:")


def build_vlm_prompt(species_catalog: SpeciesCatalogRepository) -> str:
    class_names = "\n".join(f"- {name}" for name in species_catalog.list_class_names())
    return PROMPT_TEMPLATE.format(class_names=class_names)


def parse_vlm_result(
    observation: Observation,
    payload: Any,
    *,
    settings: Settings,
    species_catalog: SpeciesCatalogRepository,
    model_tag: str,
) -> ObservationResult:
    if not isinstance(payload, dict):
        raise IdentificationError("Model JSON must be an object.")

    raw_predictions = payload.get("predictions")
    if not isinstance(raw_predictions, list) or not raw_predictions:
        raise IdentificationError("Model JSON must include a non-empty predictions list.")

    allowed = set(species_catalog.list_class_names())
    parsed_items: list[dict[str, Any]] = []
    for item in raw_predictions[:3]:
        if not isinstance(item, dict):
            raise IdentificationError("Each prediction must be an object.")
        species_label = item.get("species_label")
        evidence = item.get("evidence")
        rank = item.get("rank")
        confidence = item.get("confidence")
        if not isinstance(species_label, str) or not species_label.strip():
            raise IdentificationError("Each prediction requires species_label.")
        if not isinstance(evidence, str) or not evidence.strip():
            raise IdentificationError("Each prediction requires evidence.")
        if not isinstance(rank, int):
            raise IdentificationError("Each prediction requires integer rank.")
        parsed_confidence = None
        if confidence is not None:
            if not isinstance(confidence, (int, float)):
                raise IdentificationError("Prediction confidence must be numeric.")
            parsed_confidence = float(confidence)
        parsed_items.append(
            {
                "rank": rank,
                "species_label": species_label.strip(),
                "evidence": evidence.strip(),
                "confidence": parsed_confidence,
            }
        )

    parsed_items.sort(key=lambda entry: entry["rank"])
    top_rank_label = parsed_items[0]["species_label"]
    if top_rank_label not in allowed:
        raise IdentificationError(f"Unknown species_label: {top_rank_label}")

    predictions: list[Prediction] = []
    next_rank = 1
    for entry in parsed_items:
        if entry["species_label"] not in allowed:
            continue
        predictions.append(
            Prediction(
                rank=next_rank,
                species_label=entry["species_label"],
                evidence=entry["evidence"],
                confidence=entry["confidence"],
            )
        )
        next_rank += 1

    if not predictions:
        raise IdentificationError(f"Unknown species_label: {top_rank_label}")
    top_confidence = predictions[0].confidence
    uncertain = top_confidence is None or top_confidence < settings.uncertainty_threshold

    return ObservationResult(
        observation_id=observation.observation_id,
        predictions=tuple(predictions),
        model_tag=model_tag,
        prompt_version=settings.prompt_version,
        uncertain=uncertain,
    )
