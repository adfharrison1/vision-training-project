"""Self-hosted Opik tracing for Ollama VLM calls."""

from __future__ import annotations

import logging
import os
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Any, TypeVar

from plant_id.infrastructure.config.settings import Settings

logger = logging.getLogger(__name__)

T = TypeVar("T")

_opik_configured = False


def _configure_opik(settings: Settings) -> None:
    """Point the Opik SDK at local self-hosted Opik without interactive setup.

    Do not call ``opik.configure()`` here — on first run it prompts to register
    the Opik MCP server in Cursor/VS Code and can block ``plant-id identify``.
    """
    global _opik_configured
    if _opik_configured:
        return

    import opik.config as opik_config

    os.environ.setdefault("OPIK_URL_OVERRIDE", settings.opik_base_url)
    os.environ.setdefault("OPIK_PROJECT_NAME", settings.opik_project_name)

    opik_config.update_session_config("url_override", settings.opik_base_url)
    opik_config.update_session_config("project_name", settings.opik_project_name)
    opik_config.update_session_config("workspace", opik_config.OPIK_WORKSPACE_DEFAULT_NAME)
    opik_config.update_session_config("api_key", None)

    _opik_configured = True


def _response_data(response: Any) -> dict[str, Any]:
    if hasattr(response, "model_dump"):
        return response.model_dump(mode="json")
    if isinstance(response, dict):
        return response
    return {}


def _extract_message_thinking(response: Any) -> str | None:
    message = getattr(response, "message", None)
    if message is None:
        message = _response_data(response).get("message")
    if message is None:
        return None
    thinking = getattr(message, "thinking", None)
    if thinking is None and isinstance(message, dict):
        thinking = message.get("thinking")
    if isinstance(thinking, str) and thinking.strip():
        return thinking.strip()
    return None


def _ollama_span_metadata(
    response: Any,
    *,
    model: str,
    prompt_version: str,
) -> dict[str, Any]:
    data = _response_data(response)
    metadata: dict[str, Any] = {
        "model": data.get("model", model),
        "prompt_version": prompt_version,
    }
    for key in (
        "eval_duration",
        "load_duration",
        "prompt_eval_duration",
        "prompt_eval_count",
        "eval_count",
        "done",
        "done_reason",
    ):
        if key in data:
            metadata[key] = data[key]
    thinking = _extract_message_thinking(response)
    if thinking:
        metadata["thinking"] = thinking
    return metadata


def _ollama_span_usage(response: Any) -> dict[str, int] | None:
    data = _response_data(response)
    eval_count = data.get("eval_count")
    prompt_eval_count = data.get("prompt_eval_count")
    if eval_count is None and prompt_eval_count is None:
        return None
    completion = int(eval_count or 0)
    prompt = int(prompt_eval_count or 0)
    return {
        "completion_tokens": completion,
        "prompt_tokens": prompt,
        "total_tokens": completion + prompt,
    }


@contextmanager
def identify_trace(
    settings: Settings,
    *,
    observation_id: str,
    backend: str,
    photo_count: int,
) -> Iterator[None]:
    if not settings.opik_enabled:
        yield
        return

    try:
        _configure_opik(settings)
        from opik import start_as_current_span

        with start_as_current_span(
            name="identify",
            metadata={
                "observation_id": observation_id,
                "backend": backend,
                "photo_count": photo_count,
            },
            project_name=settings.opik_project_name,
        ):
            yield
    except Exception as exc:
        logger.debug("Opik identify trace failed (non-fatal): %s", exc)
        yield


def call_ollama_chat_traced[T](
    settings: Settings,
    chat_fn: Callable[[], T],
    *,
    model: str,
    prompt_version: str,
) -> T:
    if not settings.opik_enabled:
        return chat_fn()

    try:
        _configure_opik(settings)
        from opik import opik_context, start_as_current_span

        with start_as_current_span(
            name="ollama.chat",
            type="llm",
            model=model,
            provider="ollama",
            metadata={"prompt_version": prompt_version},
            project_name=settings.opik_project_name,
            tags=["ollama", "plant-id"],
        ):
            response = chat_fn()
            opik_context.update_current_span(
                metadata=_ollama_span_metadata(
                    response,
                    model=model,
                    prompt_version=prompt_version,
                ),
                usage=_ollama_span_usage(response),
            )
            return response
    except Exception as exc:
        logger.debug("Opik ollama.chat trace failed (non-fatal): %s", exc)
        return chat_fn()


def record_identify_outcome(
    settings: Settings,
    *,
    observation_id: str,
    result_summary: dict[str, Any],
) -> None:
    if not settings.opik_enabled:
        return

    try:
        from opik import opik_context

        opik_context.update_current_span(
            metadata={
                "observation_id": observation_id,
                "prediction_summary": result_summary,
            }
        )
    except Exception as exc:
        logger.debug("Opik identify outcome update failed (non-fatal): %s", exc)
