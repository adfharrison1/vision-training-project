"""Extract and aggregate LLM token usage from identification raw payloads."""

from __future__ import annotations

from typing import Any

from eval.report import InferenceTokenUsage


def _openai_usage_from_response(response: dict[str, Any]) -> dict[str, int] | None:
    usage = response.get("usage")
    if not isinstance(usage, dict):
        return None
    prompt = int(usage.get("prompt_tokens") or 0)
    completion = int(usage.get("completion_tokens") or 0)
    total = int(usage.get("total_tokens") or 0)
    if prompt == 0 and completion == 0 and total == 0:
        return None
    if total == 0:
        total = prompt + completion
    return {
        "prompt_tokens": prompt,
        "completion_tokens": completion,
        "total_tokens": total,
    }


def _ollama_usage_from_response(response: dict[str, Any]) -> dict[str, int] | None:
    eval_count = response.get("eval_count")
    prompt_eval_count = response.get("prompt_eval_count")
    if eval_count is None and prompt_eval_count is None:
        return None
    completion = int(eval_count or 0)
    prompt = int(prompt_eval_count or 0)
    return {
        "prompt_tokens": prompt,
        "completion_tokens": completion,
        "total_tokens": prompt + completion,
    }


def _usage_from_response_dict(response: dict[str, Any]) -> dict[str, int] | None:
    if "usage" in response:
        return _openai_usage_from_response(response)
    return _ollama_usage_from_response(response)


def _add_usage(totals: dict[str, int], addition: dict[str, int]) -> None:
    totals["prompt_tokens"] += addition["prompt_tokens"]
    totals["completion_tokens"] += addition["completion_tokens"]
    totals["total_tokens"] += addition["total_tokens"]


def usage_from_identification_raw(raw: dict | None) -> dict[str, int] | None:
    """Return token counts for one identify call, or None if the API omitted usage."""
    if not raw:
        return None

    totals = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    found = False

    response = raw.get("response")
    if isinstance(response, dict):
        piece = _usage_from_response_dict(response)
        if piece is not None:
            _add_usage(totals, piece)
            found = True

    retry = raw.get("retry")
    if isinstance(retry, dict):
        retry_response = retry.get("response")
        if isinstance(retry_response, dict):
            piece = _usage_from_response_dict(retry_response)
            if piece is not None:
                _add_usage(totals, piece)
                found = True

    return totals if found else None


def aggregate_token_usage(
    per_observation: list[dict[str, int] | None],
) -> InferenceTokenUsage | None:
    prompt = completion = total = 0
    with_usage = 0
    for usage in per_observation:
        if usage is None:
            continue
        with_usage += 1
        prompt += usage["prompt_tokens"]
        completion += usage["completion_tokens"]
        total += usage["total_tokens"]
    if with_usage == 0:
        return None
    return InferenceTokenUsage(
        prompt_tokens=prompt,
        completion_tokens=completion,
        total_tokens=total,
        observations_with_usage=with_usage,
    )
