"""Retrieval index manifest and vector artifact I/O (OpenRouter embeddings)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Literal

import numpy as np
from pydantic import BaseModel, ConfigDict

PrototypeKind = Literal["text", "image"]


class IndexPoint(BaseModel):
    model_config = ConfigDict(frozen=True)

    point_id: str
    catalog_label: str
    prototype_kind: PrototypeKind
    prototype_id: str
    retrieval_text: str | None = None
    context_block: str
    source_image: str | None = None


class RetrievalIndexManifest(BaseModel):
    model_config = ConfigDict(frozen=True)

    version: str = "retrieval-index-v2"
    embed_provider: str = "openrouter"
    embed_model: str = ""
    collection_name: str
    embed_dim: int
    points: tuple[IndexPoint, ...]


def default_index_dir(root: Path | None = None) -> Path:
    from plant_id.infrastructure.config.settings import _project_root

    base = root or _project_root()
    return base / "artifacts" / "retrieval_index"


def vectors_path(index_dir: Path) -> Path:
    return index_dir / "vectors.npy"


def manifest_path(index_dir: Path) -> Path:
    return index_dir / "manifest.json"


def stable_point_id(
    *,
    catalog_label: str,
    prototype_kind: str,
    prototype_id: str,
) -> str:
    digest = hashlib.sha256(
        f"{catalog_label}|{prototype_kind}|{prototype_id}".encode()
    ).hexdigest()
    return digest[:32]


def load_manifest(index_dir: Path) -> RetrievalIndexManifest:
    path = manifest_path(index_dir)
    if not path.is_file():
        raise FileNotFoundError(
            f"Retrieval index manifest not found at {path}. "
            "Run: uv run python -m eval.build_retrieval_index"
        )
    payload = json.loads(path.read_text(encoding="utf-8"))
    provider = payload.get("embed_provider", "openrouter")
    if provider != "openrouter":
        raise ValueError(
            f"Unsupported embed_provider {provider!r} in {path}. "
            "Rebuild the index with OpenRouter: uv run python -m eval.build_retrieval_index"
        )
    if not payload.get("embed_model"):
        raise ValueError(
            f"Retrieval index manifest at {path} is missing embed_model. "
            "Run: uv run python -m eval.build_retrieval_index"
        )
    return RetrievalIndexManifest.model_validate(payload)


def manifest_embed_model(manifest: RetrievalIndexManifest) -> str:
    if not manifest.embed_model:
        raise ValueError("Retrieval index manifest missing embed_model.")
    return manifest.embed_model


def save_manifest(index_dir: Path, manifest: RetrievalIndexManifest) -> Path:
    index_dir.mkdir(parents=True, exist_ok=True)
    path = manifest_path(index_dir)
    path.write_text(manifest.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return path


def load_vectors(index_dir: Path) -> np.ndarray:
    path = vectors_path(index_dir)
    if not path.is_file():
        raise FileNotFoundError(f"Retrieval vectors not found at {path}.")
    vectors = np.load(path)
    if vectors.ndim != 2:
        raise ValueError(f"Expected 2-D vectors array, got shape {vectors.shape}.")
    return vectors


def save_vectors(index_dir: Path, vectors: np.ndarray) -> Path:
    index_dir.mkdir(parents=True, exist_ok=True)
    path = vectors_path(index_dir)
    np.save(path, vectors.astype(np.float32))
    return path


def manifest_point_lookup(manifest: RetrievalIndexManifest) -> dict[str, IndexPoint]:
    return {point.point_id: point for point in manifest.points}


def point_id_to_qdrant_id(point_id: str) -> int:
    """Map stable hex id to unsigned int for Qdrant."""
    return int(point_id[:16], 16)
