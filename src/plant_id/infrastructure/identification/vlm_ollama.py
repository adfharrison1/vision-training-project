"""VLM identification via local Ollama."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ollama import Client

from plant_id.domain.application_events import log_stage, log_wait
from plant_id.domain.exceptions import IdentificationError
from plant_id.domain.models import Observation, ObservationResult
from plant_id.domain.repositories import SpeciesCatalogRepository
from plant_id.infrastructure.config.settings import Settings
from plant_id.infrastructure.identification.vlm_common import (
    INVALID_LABEL_RETRY_SUFFIX,
    build_vlm_prompt,
    is_unknown_species_label_error,
    parse_vlm_result,
)
from plant_id.infrastructure.observability.opik_tracing import (
    call_ollama_chat_traced,
    identify_trace,
    record_content_retry,
    record_identify_outcome,
)

CONTENT_RETRY_SUFFIX = (
    "Your previous response had empty content. Return ONLY the JSON object in the "
    "message content field (not in thinking). Same schema as before."
)


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
        prompt = build_vlm_prompt(self._species_catalog)
        log_stage(2, 4, f"Built prompt ({label_count} species labels)")

        ollama_message = (
            f"Calling Ollama ({self._settings.vision_model}) — "
            "this may take several minutes on first run..."
        )
        try:
            with log_wait(3, 4, ollama_message):
                response, retry_response, retry_info = self._call_with_optional_retry(
                    prompt, image_paths
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
                "think": self._settings.ollama_think,
            },
            "response": self._response_to_raw(response),
        }
        if retry_info is not None:
            raw["retry"] = retry_info

        content = self._resolve_content(response, retry_response)
        if not content:
            raise IdentificationError(
                f"Empty model response for observation {observation.observation_id}.",
                raw=raw,
            )

        try:
            parsed = json.loads(content)
            result = parse_vlm_result(
                observation,
                parsed,
                settings=self._settings,
                species_catalog=self._species_catalog,
                model_tag=self._settings.vision_model,
            )
        except (json.JSONDecodeError, ValueError, IdentificationError) as exc:
            if (
                isinstance(exc, IdentificationError)
                and self._settings.invalid_label_retry_enabled
                and is_unknown_species_label_error(exc)
            ):
                record_content_retry(self._settings, reason="unknown_species_label")
                retry_prompt = f"{prompt}\n\n{INVALID_LABEL_RETRY_SUFFIX}"
                retry_response = self._chat(retry_prompt, image_paths)
                raw["invalid_label_retry"] = {
                    "attempted": True,
                    "reason": "unknown_species_label",
                    "request_suffix": INVALID_LABEL_RETRY_SUFFIX,
                    "response": self._response_to_raw(retry_response),
                }
                retry_content = self._extract_message_content(retry_response)
                if not retry_content:
                    raise IdentificationError(str(exc), raw=raw) from exc
                try:
                    retry_parsed = json.loads(retry_content)
                    result = parse_vlm_result(
                        observation,
                        retry_parsed,
                        settings=self._settings,
                        species_catalog=self._species_catalog,
                        model_tag=self._settings.vision_model,
                    )
                except (json.JSONDecodeError, ValueError, IdentificationError) as retry_exc:
                    message = (
                        f"Invalid model JSON for observation {observation.observation_id}: "
                        f"{retry_exc}"
                    )
                    if isinstance(retry_exc, IdentificationError):
                        raise IdentificationError(str(retry_exc), raw=raw) from retry_exc
                    raise IdentificationError(message, raw=raw) from retry_exc
            else:
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

    def _call_with_optional_retry(
        self,
        prompt: str,
        image_paths: list[str],
    ) -> tuple[Any, Any | None, dict[str, Any] | None]:
        first_response = self._chat(prompt, image_paths)
        if not self._settings.ollama_content_retry_enabled:
            return first_response, None, None

        retry_reason = self._content_retry_reason(first_response)
        if retry_reason is None:
            return first_response, None, None

        retry_prompt = f"{prompt}\n\n{CONTENT_RETRY_SUFFIX}"
        retry_response = self._chat(retry_prompt, image_paths)
        record_content_retry(self._settings, reason=retry_reason)
        retry_info = {
            "attempted": True,
            "reason": retry_reason,
            "request_suffix": CONTENT_RETRY_SUFFIX,
            "response": self._response_to_raw(retry_response),
        }
        return first_response, retry_response, retry_info

    def _chat(self, prompt: str, image_paths: list[str]) -> Any:
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
            "think": self._settings.ollama_think,
            "options": {"temperature": 0},
        }
        return call_ollama_chat_traced(
            self._settings,
            lambda: self._client.chat(**request_payload),
            model=self._settings.vision_model,
            prompt_version=self._settings.prompt_version,
        )

    def _resolve_content(
        self,
        first_response: Any,
        retry_response: Any | None,
    ) -> str:
        if retry_response is None:
            return self._extract_message_content(first_response)

        content = self._extract_message_content(retry_response)
        if content:
            return content
        return self._extract_message_content(first_response)

    @staticmethod
    def _response_to_raw(response: Any) -> dict[str, Any]:
        if hasattr(response, "model_dump"):
            return response.model_dump(mode="json")
        if isinstance(response, dict):
            return response
        return dict(response)

    @staticmethod
    def _message_content_only(response: Any) -> str:
        message = response.message
        return (message.content or "").strip()

    @staticmethod
    def _message_thinking(response: Any) -> str:
        return (getattr(response.message, "thinking", None) or "").strip()

    @staticmethod
    def _thinking_has_parseable_predictions(text: str) -> bool:
        stripped = text.strip()
        if not stripped.startswith("{"):
            return False
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            return False
        predictions = payload.get("predictions") if isinstance(payload, dict) else None
        return isinstance(predictions, list) and bool(predictions)

    def _needs_content_channel_retry(self, response: Any) -> bool:
        if self._message_content_only(response):
            return False
        return self._thinking_has_parseable_predictions(self._message_thinking(response))

    def _needs_empty_response_retry(self, response: Any) -> bool:
        if self._message_content_only(response):
            return False
        if self._thinking_has_parseable_predictions(self._message_thinking(response)):
            return False
        done_reason = getattr(response, "done_reason", None)
        if done_reason == "length":
            return True
        return not self._message_thinking(response)

    def _content_retry_reason(self, response: Any) -> str | None:
        if self._needs_content_channel_retry(response):
            return "json_in_thinking"
        if self._needs_empty_response_retry(response):
            return "empty_response"
        return None

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
