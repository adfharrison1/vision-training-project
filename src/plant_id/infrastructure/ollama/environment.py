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


def verify_cloud_vlm_environment(settings: Settings | None = None) -> VerifyEnvResult:
    settings = settings or Settings()
    messages: list[str] = []

    if not settings.vlm_cloud_api_key:
        return VerifyEnvResult(
            ok=False,
            messages=(
                "PLANT_ID_VLM_CLOUD_API_KEY is not set.",
                "Set it to your OpenAI-compatible inference API key (see README).",
            ),
        )

    if not settings.vlm_cloud_base_url.strip():
        return VerifyEnvResult(
            ok=False,
            messages=("PLANT_ID_VLM_CLOUD_BASE_URL must not be empty.",),
        )

    if not settings.vlm_cloud_model.strip():
        return VerifyEnvResult(
            ok=False,
            messages=("PLANT_ID_VLM_CLOUD_MODEL must not be empty.",),
        )

    from urllib.parse import urlparse

    host = urlparse(settings.vlm_cloud_base_url).netloc
    messages.append(f"Cloud VLM base URL host: {host or settings.vlm_cloud_base_url}")
    messages.append(f"Cloud VLM model: {settings.vlm_cloud_model}")
    if settings.vlm_cloud_vendor:
        messages.append(f"Cloud vendor label: {settings.vlm_cloud_vendor}")
    messages.append("Cloud VLM settings are configured for backend vlm-cloud.")
    return VerifyEnvResult(ok=True, messages=tuple(messages))


def verify_species_sheets_environment(settings: Settings | None = None) -> VerifyEnvResult:
    from plant_id.infrastructure.species.file_catalog import FileSpeciesCatalog
    from plant_id.infrastructure.species_sheets.loader import (
        list_sheet_paths,
        load_species_sheet,
        validate_sheet_catalog_membership,
    )

    settings = settings or Settings()
    paths = list_sheet_paths(settings.species_sheets_dir)
    if not paths:
        return VerifyEnvResult(
            ok=False,
            messages=(f"No species sheets under {settings.species_sheets_dir}.",),
        )
    catalog = FileSpeciesCatalog(settings.species_catalog_path)
    labels = set(catalog.list_class_names())
    issues: list[str] = []
    for path in paths:
        sheet = load_species_sheet(path)
        for issue in validate_sheet_catalog_membership(sheet, catalog_labels=labels):
            issues.append(f"{path.name}: {issue}")
    if issues:
        return VerifyEnvResult(ok=False, messages=tuple(issues))
    return VerifyEnvResult(
        ok=True,
        messages=(f"Validated {len(paths)} species sheet(s).",),
    )


def verify_retrieval_environment(settings: Settings | None = None) -> VerifyEnvResult:
    settings = settings or Settings()
    messages: list[str] = []
    try:
        from qdrant_client import QdrantClient

        client = QdrantClient(url=settings.qdrant_url, timeout=settings.qdrant_timeout_seconds)
        collections = client.get_collections()
        names = {item.name for item in collections.collections}
    except Exception as exc:  # noqa: BLE001
        return VerifyEnvResult(
            ok=False,
            messages=(
                f"Qdrant unreachable at {settings.qdrant_url}: {exc}",
                "Start local Qdrant: ./scripts/qdrant.sh up",
            ),
        )

    messages.append(f"Qdrant reachable at {settings.qdrant_url}")
    if settings.qdrant_collection not in names:
        return VerifyEnvResult(
            ok=False,
            messages=(
                *messages,
                f"Collection {settings.qdrant_collection!r} not found.",
                "Build and seed: uv run python -m eval.build_retrieval_index "
                "&& ./scripts/qdrant.sh seed",
            ),
        )
    messages.append(f"Collection {settings.qdrant_collection!r} is present.")
    index_manifest = settings.retrieval_index_dir / "manifest.json"
    if not index_manifest.is_file():
        messages.append(
            f"Note: index manifest missing at {index_manifest} (build before seed)."
        )
    else:
        messages.append(f"Index manifest present at {index_manifest}.")
    messages.append("Retrieval environment check passed.")
    return VerifyEnvResult(ok=True, messages=tuple(messages))
