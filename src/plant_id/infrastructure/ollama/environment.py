"""Ollama server and vision-model checks for local development."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass

import ollama

from plant_id.infrastructure.config.settings import Settings


@dataclass(frozen=True)
class VerifyEnvResult:
    ok: bool
    messages: tuple[str, ...]


def _parse_version(version: str) -> tuple[int, ...]:
    parts: list[int] = []
    for segment in version.split("."):
        digits = ""
        for char in segment:
            if char.isdigit():
                digits += char
            else:
                break
        parts.append(int(digits) if digits else 0)
    return tuple(parts)


def _version_at_least(actual: str, minimum: str) -> bool:
    return _parse_version(actual) >= _parse_version(minimum)


def _fetch_ollama_version(host: str) -> str:
    url = f"{host.rstrip('/')}/api/version"
    request = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(request, timeout=5) as response:
        payload = json.loads(response.read().decode("utf-8"))
    version = payload.get("version")
    if not isinstance(version, str) or not version:
        raise RuntimeError(f"Unexpected Ollama version response from {url}: {payload!r}")
    return version


def verify_environment(settings: Settings | None = None) -> VerifyEnvResult:
    settings = settings or Settings()
    messages: list[str] = []

    try:
        version = _fetch_ollama_version(settings.ollama_host)
    except (urllib.error.URLError, TimeoutError, RuntimeError) as exc:
        return VerifyEnvResult(
            ok=False,
            messages=(
                f"Ollama is unreachable at {settings.ollama_host}: {exc}",
                "Start Ollama (https://ollama.com/download) and retry.",
            ),
        )

    messages.append(f"Ollama server {version} reachable at {settings.ollama_host}")

    if not _version_at_least(version, settings.min_ollama_version):
        return VerifyEnvResult(
            ok=False,
            messages=(
                *messages,
                (
                    f"Ollama {version} is below required minimum "
                    f"{settings.min_ollama_version}."
                ),
            ),
        )

    client = ollama.Client(host=settings.ollama_host)
    try:
        listed = client.list()
    except Exception as exc:  # noqa: BLE001 — surface connection errors to CLI user
        return VerifyEnvResult(
            ok=False,
            messages=(
                *messages,
                f"Failed to list Ollama models: {exc}",
            ),
        )

    model_names = {
        model.model
        for model in listed.models
        if getattr(model, "model", None)
    }
    if settings.vision_model not in model_names:
        return VerifyEnvResult(
            ok=False,
            messages=(
                *messages,
                f"Vision model '{settings.vision_model}' is not installed.",
                f"Pull it with: ollama pull {settings.vision_model}",
            ),
        )

    messages.append(f"Vision model '{settings.vision_model}' is available.")
    messages.append("Environment is ready for local plant identification.")
    return VerifyEnvResult(ok=True, messages=tuple(messages))
