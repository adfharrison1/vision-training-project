"""Self-hosted Opik tracing for VLM identification calls."""

from __future__ import annotations

import logging
import os
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any, TypeVar

from plant_id.infrastructure.config.settings import Settings

logger = logging.getLogger(__name__)

T = TypeVar("T")

_opik_configured = False


@dataclass
class EvalTraceSession:
    eval_run_id: str
    eval_profile: str
    ground_truth: str | None = None
    trace_id: str | None = None


_eval_session: ContextVar[EvalTraceSession | None] = ContextVar("eval_trace_session", default=None)


@contextmanager
def eval_trace_session(
    eval_run_id: str,
    eval_profile: str,
    *,
    ground_truth: str | None = None,
) -> Iterator[EvalTraceSession]:
    session = EvalTraceSession(
        eval_run_id=eval_run_id,
        eval_profile=eval_profile,
        ground_truth=ground_truth,
    )
    token = _eval_session.set(session)
    try:
        yield session
    finally:
        _eval_session.reset(token)


def current_eval_trace_session() -> EvalTraceSession | None:
    return _eval_session.get()


def _eval_trace_metadata(session: EvalTraceSession) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "eval_run_id": session.eval_run_id,
        "eval_profile": session.eval_profile,
    }
    if session.ground_truth is not None:
        metadata["ground_truth"] = session.ground_truth
    return metadata


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


def _openai_span_usage(response: Any) -> dict[str, int] | None:
    usage = getattr(response, "usage", None)
    if usage is None:
        return None
    prompt = int(getattr(usage, "prompt_tokens", 0) or 0)
    completion = int(getattr(usage, "completion_tokens", 0) or 0)
    total = int(getattr(usage, "total_tokens", 0) or 0)
    if prompt == 0 and completion == 0 and total == 0:
        return None
    if total == 0:
        total = prompt + completion
    return {
        "prompt_tokens": prompt,
        "completion_tokens": completion,
        "total_tokens": total,
    }


def _openai_span_metadata(
    response: Any,
    *,
    model: str,
    prompt_version: str,
    cloud_vendor: str | None,
) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "model": model,
        "prompt_version": prompt_version,
        "inference_provider": "openai-compatible",
    }
    if cloud_vendor:
        metadata["cloud_vendor"] = cloud_vendor
    response_id = getattr(response, "id", None)
    if response_id:
        metadata["response_id"] = response_id
    return metadata


@contextmanager
def identify_trace(
    settings: Settings,
    *,
    observation_id: str,
    backend: str,
    photo_count: int,
    extra_metadata: dict[str, Any] | None = None,
) -> Iterator[None]:
    if not settings.opik_enabled:
        yield
        return

    session = _eval_session.get()
    metadata: dict[str, Any] = {
        "observation_id": observation_id,
        "backend": backend,
        "photo_count": photo_count,
    }
    if extra_metadata:
        metadata.update(extra_metadata)
    if session is not None:
        metadata.update(_eval_trace_metadata(session))

    try:
        _configure_opik(settings)
        from opik import opik_context, start_as_current_span
    except Exception as exc:
        logger.debug("Opik identify trace setup failed (non-fatal): %s", exc)
        yield
        return

    with start_as_current_span(
        name="identify",
        metadata=metadata,
        project_name=settings.opik_project_name,
    ):
        if session is not None:
            trace_data = opik_context.get_current_trace_data()
            if trace_data is not None:
                session.trace_id = trace_data.id
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
    except Exception as exc:
        logger.debug("Opik ollama.chat trace setup failed (non-fatal): %s", exc)
        return chat_fn()

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


def call_openai_chat_traced[T](
    settings: Settings,
    chat_fn: Callable[[], T],
    *,
    model: str,
    prompt_version: str,
    cloud_vendor: str | None = None,
) -> T:
    if not settings.opik_enabled:
        return chat_fn()

    try:
        _configure_opik(settings)
        from opik import opik_context, start_as_current_span
    except Exception as exc:
        logger.debug("Opik openai.chat trace setup failed (non-fatal): %s", exc)
        return chat_fn()

    span_metadata: dict[str, Any] = {
        "prompt_version": prompt_version,
        "inference_provider": "openai-compatible",
    }
    if cloud_vendor:
        span_metadata["cloud_vendor"] = cloud_vendor

    with start_as_current_span(
        name="openai.chat",
        type="llm",
        model=model,
        provider="openai-compatible",
        metadata=span_metadata,
        project_name=settings.opik_project_name,
        tags=["vlm-cloud", "plant-id"],
    ):
        response = chat_fn()
        opik_context.update_current_span(
            metadata=_openai_span_metadata(
                response,
                model=model,
                prompt_version=prompt_version,
                cloud_vendor=cloud_vendor,
            ),
            usage=_openai_span_usage(response),
        )
        return response


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

        metadata: dict[str, Any] = {
            "observation_id": observation_id,
            "prediction_summary": result_summary,
        }
        session = _eval_session.get()
        if session is not None:
            metadata.update(_eval_trace_metadata(session))
            top_species = result_summary.get("top_species")
            species_labels = result_summary.get("species_labels")
            if session.ground_truth and isinstance(top_species, str):
                metadata["match"] = top_species == session.ground_truth
                metadata["top1_match"] = top_species == session.ground_truth
            if session.ground_truth and isinstance(species_labels, list):
                metadata["top3_match"] = session.ground_truth in species_labels[:3]

        opik_context.update_current_span(metadata=metadata)
    except Exception as exc:
        logger.debug("Opik identify outcome update failed (non-fatal): %s", exc)


def record_content_retry(
    settings: Settings,
    *,
    reason: str,
) -> None:
    if not settings.opik_enabled:
        return

    try:
        from opik import opik_context

        opik_context.update_current_span(
            metadata={
                "content_retry": True,
                "content_retry_reason": reason,
            }
        )
    except Exception as exc:
        logger.debug("Opik content retry update failed (non-fatal): %s", exc)
