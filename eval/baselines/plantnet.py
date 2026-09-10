"""Optional Pl@ntNet API baseline for eval-only comparison."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path

import httpx

PLANTNET_API_URL = "https://my-api.plantnet.org/v2/identify/all"
DEFAULT_MAX_RETRIES = 3
DEFAULT_BACKOFF_SECONDS = 1.0


@dataclass(frozen=True)
class PlantNetPrediction:
    labels: tuple[str, ...]
    raw_best_match: str | None = None


@dataclass(frozen=True)
class PlantNetResult:
    labels: tuple[str, ...]
    raw_best_match: str | None = None
    error: str | None = None


def plantnet_api_key() -> str | None:
    value = os.environ.get("PLANTNET_API_KEY", "").strip()
    return value or None


def _catalog_label_candidates(payload: dict, allowed: set[str]) -> tuple[str, ...]:
    labels: list[str] = []
    best_match = payload.get("bestMatch")
    if isinstance(best_match, str) and best_match in allowed:
        labels.append(best_match)

    results = payload.get("results")
    if isinstance(results, list):
        for item in results[:3]:
            if not isinstance(item, dict):
                continue
            species = item.get("species")
            if not isinstance(species, dict):
                continue
            common_names = species.get("commonNames")
            if isinstance(common_names, list):
                for name in common_names:
                    if isinstance(name, str) and name in allowed and name not in labels:
                        labels.append(name)
            scientific = species.get("scientificNameWithoutAuthor")
            if isinstance(scientific, str) and scientific in allowed and scientific not in labels:
                labels.append(scientific)
    return tuple(labels)


def identify_image(
    image_path: Path,
    *,
    class_names: list[str],
    api_key: str | None = None,
    client: httpx.Client | None = None,
    max_retries: int = DEFAULT_MAX_RETRIES,
    backoff_seconds: float = DEFAULT_BACKOFF_SECONDS,
) -> PlantNetResult:
    key = api_key or plantnet_api_key()
    if not key:
        return PlantNetResult(labels=(), error="PLANTNET_API_KEY is not configured.")

    allowed = set(class_names)
    owns_client = client is None
    http = client or httpx.Client(timeout=60.0)
    try:
        for attempt in range(max_retries):
            try:
                with image_path.open("rb") as image_file:
                    response = http.post(
                        PLANTNET_API_URL,
                        params={"api-key": key},
                        data={"organs": "flower"},
                        files={"images": (image_path.name, image_file, "image/jpeg")},
                    )
            except httpx.HTTPError as exc:
                if attempt + 1 >= max_retries:
                    return PlantNetResult(labels=(), error=f"Pl@ntNet request failed: {exc}")
                time.sleep(backoff_seconds * (2**attempt))
                continue

            if response.status_code in {429, 500, 502, 503, 504}:
                if attempt + 1 >= max_retries:
                    return PlantNetResult(
                        labels=(),
                        error=(
                            f"Pl@ntNet transient error after {max_retries} attempts: "
                            f"HTTP {response.status_code}"
                        ),
                    )
                time.sleep(backoff_seconds * (2**attempt))
                continue

            if response.status_code >= 400:
                return PlantNetResult(
                    labels=(),
                    error=f"Pl@ntNet HTTP {response.status_code}: {response.text[:200]}",
                )

            payload = response.json()
            labels = _catalog_label_candidates(payload, allowed)
            raw_best_match = payload.get("bestMatch") if isinstance(payload, dict) else None
            if not isinstance(raw_best_match, str):
                raw_best_match = None
            return PlantNetResult(labels=labels, raw_best_match=raw_best_match)
    finally:
        if owns_client:
            http.close()

    return PlantNetResult(labels=(), error="Pl@ntNet request failed.")
