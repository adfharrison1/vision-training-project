"""VLM identification via user-configured OpenAI-compatible cloud endpoints."""

from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from openai import OpenAI

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
    call_openai_chat_traced,
    identify_trace,
    record_content_retry,
    record_identify_outcome,
)


def _image_data_uri(path: str) -> str:
    file_path = Path(path)
    suffix = file_path.suffix.lower()
    if suffix in {".jpg", ".jpeg"}:
        mime = "image/jpeg"
    elif suffix == ".png":
        mime = "image/png"
    else:
        mime = "image/jpeg"
    encoded = base64.standard_b64encode(file_path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


class VlmCloudIdentificationRepository:
    """Identify plants using a hosted OpenAI-compatible vision-language API."""

    def __init__(
        self,
        settings: Settings,
        species_catalog: SpeciesCatalogRepository,
        client: OpenAI | None = None,
    ) -> None:
        self._settings = settings
        self._species_catalog = species_catalog
        self._client = client

    @property
    def backend_id(self) -> str:
        return f"vlm-cloud:{self._settings.vlm_cloud_model}"

    def _openai_client(self) -> OpenAI:
        if self._client is not None:
            return self._client
        return OpenAI(
            base_url=self._settings.vlm_cloud_base_url,
            api_key=self._settings.vlm_cloud_api_key,
            timeout=self._settings.vlm_cloud_timeout_seconds,
        )

    def _validate_cloud_configuration(self) -> None:
        if not self._settings.vlm_cloud_api_key:
            raise IdentificationError(
                "Cloud VLM is not configured: set PLANT_ID_VLM_CLOUD_API_KEY."
            )
        if not self._settings.vlm_cloud_base_url.strip():
            raise IdentificationError(
                "Cloud VLM is not configured: set PLANT_ID_VLM_CLOUD_BASE_URL."
            )
        if not self._settings.vlm_cloud_model.strip():
            raise IdentificationError(
                "Cloud VLM is not configured: set PLANT_ID_VLM_CLOUD_MODEL."
            )

    def identify(self, observation: Observation) -> tuple[ObservationResult, dict]:
        photo_count = len(observation.photo_paths)
        trace_metadata: dict[str, Any] = {}
        if self._settings.vlm_cloud_vendor:
            trace_metadata["cloud_vendor"] = self._settings.vlm_cloud_vendor
        trace_metadata["cloud_base_url_host"] = urlparse(
            self._settings.vlm_cloud_base_url
        ).netloc

        with identify_trace(
            self._settings,
            observation_id=observation.observation_id,
            backend=self.backend_id,
            photo_count=photo_count,
            extra_metadata=trace_metadata,
        ):
            return self._identify_with_tracing(observation, photo_count)

    def _identify_with_tracing(
        self,
        observation: Observation,
        photo_count: int,
    ) -> tuple[ObservationResult, dict]:
        self._validate_cloud_configuration()
        image_paths = [str(path.resolve()) for path in observation.photo_paths]
        for image_path in image_paths:
            if not Path(image_path).is_file():
                raise IdentificationError(
                    f"Photo not found for observation {observation.observation_id}: "
                    f"{image_path}"
                )
        log_stage(1, 4, f"Validated {photo_count} photo(s)")

        label_count = len(self._species_catalog.list_class_names())
        prompt = build_vlm_prompt(self._species_catalog)
        log_stage(2, 4, f"Built prompt ({label_count} species labels)")

        content_parts: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
        for image_path in image_paths:
            content_parts.append(
                {
                    "type": "image_url",
                    "image_url": {"url": _image_data_uri(image_path)},
                }
            )

        cloud_message = (
            f"Calling cloud VLM ({self._settings.vlm_cloud_model}) — "
            "waiting for inference..."
        )
        try:
            with log_wait(3, 4, cloud_message):
                response = self._chat(content_parts)
        except Exception as exc:
            raise IdentificationError(
                f"Cloud VLM request failed for observation "
                f"{observation.observation_id}: {exc}"
            ) from exc

        raw: dict[str, Any] = {
            "request": {
                "model": self._settings.vlm_cloud_model,
                "prompt_version": self._settings.prompt_version,
                "photo_paths": image_paths,
                "temperature": 0,
                "reasoning_effort": self._settings.vlm_cloud_reasoning_effort,
                "base_url_host": urlparse(self._settings.vlm_cloud_base_url).netloc,
            },
            "response": response.model_dump(mode="json"),
        }

        try:
            result = self._result_from_response(observation, response, raw)
        except IdentificationError as exc:
            if not (
                self._settings.invalid_label_retry_enabled
                and is_unknown_species_label_error(exc)
            ):
                raise

            record_content_retry(self._settings, reason="unknown_species_label")
            retry_parts: list[dict[str, Any]] = [
                {"type": "text", "text": f"{prompt}\n\n{INVALID_LABEL_RETRY_SUFFIX}"},
                *content_parts[1:],
            ]
            try:
                retry_response = self._chat(retry_parts)
            except Exception as retry_exc:
                raise IdentificationError(
                    f"Cloud VLM label retry failed for observation "
                    f"{observation.observation_id}: {retry_exc}",
                    raw=raw,
                ) from retry_exc

            raw["invalid_label_retry"] = {
                "attempted": True,
                "reason": "unknown_species_label",
                "request_suffix": INVALID_LABEL_RETRY_SUFFIX,
                "response": retry_response.model_dump(mode="json"),
            }
            try:
                result = self._result_from_response(observation, retry_response, raw)
            except IdentificationError as retry_parse_exc:
                raise IdentificationError(str(retry_parse_exc), raw=raw) from retry_parse_exc

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

    def _result_from_response(
        self,
        observation: Observation,
        response: Any,
        raw: dict[str, Any],
    ) -> ObservationResult:
        content = (response.choices[0].message.content or "").strip()
        if not content:
            raise IdentificationError(
                f"Empty model response for observation {observation.observation_id}.",
                raw=raw,
            )
        try:
            parsed = json.loads(content)
            return parse_vlm_result(
                observation,
                parsed,
                settings=self._settings,
                species_catalog=self._species_catalog,
                model_tag=self._settings.vlm_cloud_model,
            )
        except (json.JSONDecodeError, ValueError, IdentificationError) as exc:
            message = (
                f"Invalid model JSON for observation {observation.observation_id}: {exc}"
            )
            if isinstance(exc, IdentificationError):
                raise IdentificationError(str(exc), raw=raw) from exc
            raise IdentificationError(message, raw=raw) from exc

    def _chat(self, content_parts: list[dict[str, Any]]) -> Any:
        def _create() -> Any:
            kwargs: dict[str, Any] = {
                "model": self._settings.vlm_cloud_model,
                "messages": [{"role": "user", "content": content_parts}],
                "temperature": 0,
            }
            effort = self._settings.vlm_cloud_reasoning_effort
            if effort is not None and effort.strip():
                kwargs["reasoning_effort"] = effort.strip()
            return self._openai_client().chat.completions.create(**kwargs)

        return call_openai_chat_traced(
            self._settings,
            _create,
            model=self._settings.vlm_cloud_model,
            prompt_version=self._settings.prompt_version,
            cloud_vendor=self._settings.vlm_cloud_vendor,
        )
