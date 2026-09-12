"""VLM identification via local Ollama."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ollama import Client

from plant_id.domain.application_events import log_stage, log_wait
from plant_id.domain.exceptions import IdentificationError
from plant_id.domain.models import Observation, ObservationResult, Prediction
from plant_id.domain.repositories import SpeciesCatalogRepository
from plant_id.infrastructure.config.settings import Settings
from plant_id.infrastructure.observability.opik_tracing import (
    call_ollama_chat_traced,
    identify_trace,
    record_identify_outcome,
)

PROMPT_TEMPLATE = """Identify the flowering plant in the photograph(s).

Return ONLY valid JSON matching this schema:
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
- species_label MUST match one allowed class name exactly.
- confidence is a number from 0.0 to 1.0 for each prediction.
- Do not include markdown or commentary outside the JSON.
- Some allowed names overlap in wording but denote different classes (for example
  "english marigold" and "marigold" are not interchangeable). Read the full list;
  choose the single best exact match — do not use a shorter or generic name when a
  more specific allowed name fits the plant shown.
- When more than one allowed name seems plausible, return 3 predictions with
  distinct species_label values so the next-best alternatives appear in ranks 2 and 3.

Allowed class names:
{class_names}
"""


class VlmOllamaIdentificationRepository:
    """Identify plants using a local Ollama vision-language model."""

    def __init__(
        self,
        settings: Settings,
        species_catalog: SpeciesCatalogRepository,
        client: Client | None = None,
    ) -> None:
        self._settings = settings
        self._species_catalog = species_catalog
        self._client = client or Client(
            host=settings.ollama_host,
            timeout=settings.ollama_timeout_seconds,
        )

    @property
    def backend_id(self) -> str:
        return f"vlm:{self._settings.vision_model}"

    def identify(self, observation: Observation) -> tuple[ObservationResult, dict]:
        photo_count = len(observation.photo_paths)
        with identify_trace(
            self._settings,
            observation_id=observation.observation_id,
            backend=self.backend_id,
            photo_count=photo_count,
        ):
            return self._identify_with_tracing(observation, photo_count)

    def _identify_with_tracing(
        self,
        observation: Observation,
        photo_count: int,
    ) -> tuple[ObservationResult, dict]:
        image_paths = [str(path.resolve()) for path in observation.photo_paths]
        for image_path in image_paths:
            if not Path(image_path).is_file():
                raise IdentificationError(
                    f"Photo not found for observation {observation.observation_id}: {image_path}"
                )
        log_stage(1, 4, f"Validated {photo_count} photo(s)")

        label_count = len(self._species_catalog.list_class_names())
        prompt = self._build_prompt()
        log_stage(2, 4, f"Built prompt ({label_count} species labels)")
        request_payload = {
            "model": self._settings.vision_model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                    "images": image_paths,
                }
            ],
            "format": "json",
            "options": {"temperature": 0},
        }

        ollama_message = (
            f"Calling Ollama ({self._settings.vision_model}) — "
            "this may take several minutes on first run..."
        )
        try:
            with log_wait(3, 4, ollama_message):
                response = call_ollama_chat_traced(
                    self._settings,
                    lambda: self._client.chat(**request_payload),
                    model=self._settings.vision_model,
                    prompt_version=self._settings.prompt_version,
                )
        except Exception as exc:
            raise IdentificationError(
                f"Ollama request failed for observation {observation.observation_id}: {exc}"
            ) from exc

        raw = {
            "request": {
                "model": self._settings.vision_model,
                "prompt_version": self._settings.prompt_version,
                "photo_paths": image_paths,
                "temperature": 0,
            },
            "response": response.model_dump(mode="json")
            if hasattr(response, "model_dump")
            else dict(response),
        }

        content = self._extract_message_content(response)
        if not content:
            raise IdentificationError(
                f"Empty model response for observation {observation.observation_id}.",
                raw=raw,
            )

        try:
            parsed = json.loads(content)
            result = self._parse_result(observation, parsed)
        except (json.JSONDecodeError, ValueError, IdentificationError) as exc:
            message = (
                f"Invalid model JSON for observation {observation.observation_id}: {exc}"
            )
            if isinstance(exc, IdentificationError):
                raise IdentificationError(str(exc), raw=raw) from exc
            raise IdentificationError(message, raw=raw) from exc

        log_stage(4, 4, "Parsed model response")
        record_identify_outcome(
            self._settings,
            observation_id=observation.observation_id,
            result_summary={
                "top_species": result.predictions[0].species_label,
                "top_confidence": result.predictions[0].confidence,
                "prediction_count": len(result.predictions),
                "species_labels": [prediction.species_label for prediction in result.predictions],
                "uncertain": result.uncertain,
                "prompt_version": result.prompt_version,
                "model_tag": result.model_tag,
            },
        )
        return result, raw

    @staticmethod
    def _extract_message_content(response: Any) -> str:
        message = response.message
        content = (message.content or "").strip()
        if content:
            return content
        thinking = (getattr(message, "thinking", None) or "").strip()
        if thinking.startswith("{") or thinking.startswith("["):
            return thinking
        return ""

    def _build_prompt(self) -> str:
        class_names = "\n".join(f"- {name}" for name in self._species_catalog.list_class_names())
        return PROMPT_TEMPLATE.format(class_names=class_names)

    def _parse_result(self, observation: Observation, payload: Any) -> ObservationResult:
        if not isinstance(payload, dict):
            raise IdentificationError("Model JSON must be an object.")

        raw_predictions = payload.get("predictions")
        if not isinstance(raw_predictions, list) or not raw_predictions:
            raise IdentificationError("Model JSON must include a non-empty predictions list.")

        allowed = set(self._species_catalog.list_class_names())
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
        uncertain = top_confidence is None or top_confidence < self._settings.uncertainty_threshold

        return ObservationResult(
            observation_id=observation.observation_id,
            predictions=tuple(predictions),
            model_tag=self._settings.vision_model,
            prompt_version=self._settings.prompt_version,
            uncertain=uncertain,
        )
