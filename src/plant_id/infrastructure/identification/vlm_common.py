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
- Provide 1 to 3 predictions ranked by confidence.
- species_label MUST match one allowed class name exactly (case and spelling).
- Prefer the most specific allowed name when several overlap in meaning.
- If two or more allowed names fit, list up to 3 distinct species_label values.
- confidence is a number from 0.0 to 1.0 for each prediction.
- Put only the JSON object in your reply — no markdown, commentary, or long reasoning.

Allowed class names:
{class_names}
"""


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
    predictions: list[Prediction] = []
    for item in raw_predictions[:3]:
        if not isinstance(item, dict):
            raise IdentificationError("Each prediction must be an object.")
        species_label = item.get("species_label")
        evidence = item.get("evidence")
        rank = item.get("rank")
        confidence = item.get("confidence")
        if not isinstance(species_label, str) or not species_label.strip():
            raise IdentificationError("Each prediction requires species_label.")
        if species_label not in allowed:
            raise IdentificationError(f"Unknown species_label: {species_label}")
        if not isinstance(evidence, str) or not evidence.strip():
            raise IdentificationError("Each prediction requires evidence.")
        if not isinstance(rank, int):
            raise IdentificationError("Each prediction requires integer rank.")
        parsed_confidence = None
        if confidence is not None:
            if not isinstance(confidence, (int, float)):
                raise IdentificationError("Prediction confidence must be numeric.")
            parsed_confidence = float(confidence)
        predictions.append(
            Prediction(
                rank=rank,
                species_label=species_label,
                evidence=evidence.strip(),
                confidence=parsed_confidence,
            )
        )

    predictions.sort(key=lambda prediction: prediction.rank)
    top_confidence = predictions[0].confidence
    uncertain = top_confidence is None or top_confidence < settings.uncertainty_threshold

    return ObservationResult(
        observation_id=observation.observation_id,
        predictions=tuple(predictions),
        model_tag=model_tag,
        prompt_version=settings.prompt_version,
        uncertain=uncertain,
    )
