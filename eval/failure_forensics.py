"""Persist model payload excerpts when eval identification fails."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

_REASONING_PREVIEW_CHARS = 8_000
_UNKNOWN_LABEL_PATTERN = re.compile(r"Unknown species_label: (.+)$")


def _message_from_openai_response(response: dict[str, Any]) -> dict[str, Any] | None:
    choices = response.get("choices")
    if not isinstance(choices, list) or not choices:
        return None
    first = choices[0]
    if not isinstance(first, dict):
        return None
    message = first.get("message")
    return message if isinstance(message, dict) else None


def _reasoning_from_message(message: dict[str, Any]) -> str | None:
    reasoning = message.get("reasoning_content")
    if isinstance(reasoning, str) and reasoning.strip():
        return reasoning
    return None


def extract_identification_forensics(raw: dict[str, Any] | None) -> dict[str, Any] | None:
    """Build a compact, log-safe view of the model reply for post-mortems."""
    if not raw:
        return None

    forensics: dict[str, Any] = {}
    response = raw.get("response")
    if isinstance(response, dict):
        message = _message_from_openai_response(response)
        if message is not None:
            content = message.get("content")
            if isinstance(content, str):
                forensics["message_content"] = content
            reasoning = _reasoning_from_message(message)
            if reasoning:
                if len(reasoning) > _REASONING_PREVIEW_CHARS:
                    forensics["reasoning_content_preview"] = (
                        reasoning[:_REASONING_PREVIEW_CHARS]
                        + f"\n… [{len(reasoning) - _REASONING_PREVIEW_CHARS} chars truncated]"
                    )
                    forensics["reasoning_content_chars"] = len(reasoning)
                else:
                    forensics["reasoning_content_preview"] = reasoning

    for retry_key in ("invalid_label_retry", "retry"):
        retry = raw.get(retry_key)
        if not isinstance(retry, dict):
            continue
        retry_response = retry.get("response")
        if isinstance(retry_response, dict):
            message = _message_from_openai_response(retry_response)
            if message is not None:
                content = message.get("content")
                if isinstance(content, str):
                    forensics[f"{retry_key}_message_content"] = content

    return forensics or None


def invalid_species_label_from_error(error: str | None) -> str | None:
    if not error:
        return None
    match = _UNKNOWN_LABEL_PATTERN.search(error.strip())
    if match is None:
        return None
    return match.group(1).strip()


def eval_failures_dir(
    eval_run_id: str,
    *,
    eval_runs_root: Path | None = None,
) -> Path:
    from eval.run_registry import eval_run_paths

    root = eval_runs_root or Path("eval_runs")
    return eval_run_paths(root, eval_run_id).failures_dir


def eval_failure_artifact_path(
    eval_run_id: str,
    image_name: str,
    *,
    eval_runs_root: Path | None = None,
) -> Path:
    stem = Path(image_name).stem
    return eval_failures_dir(eval_run_id, eval_runs_root=eval_runs_root) / f"{stem}.json"


def write_eval_failure_artifact(
    *,
    eval_run_id: str,
    image: str,
    ground_truth: str,
    observation_id: str,
    error: str,
    trace_id: str | None,
    identification_raw: dict[str, Any] | None,
    eval_runs_root: Path | None = None,
) -> Path:
    payload: dict[str, Any] = {
        "eval_run_id": eval_run_id,
        "image": image,
        "ground_truth": ground_truth,
        "observation_id": observation_id,
        "trace_id": trace_id,
        "error": error,
    }
    invalid_label = invalid_species_label_from_error(error)
    if invalid_label:
        payload["invalid_species_label"] = invalid_label
    forensics = extract_identification_forensics(identification_raw)
    if forensics:
        payload["model"] = forensics

    output_path = eval_failure_artifact_path(
        eval_run_id,
        image,
        eval_runs_root=eval_runs_root,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return output_path
