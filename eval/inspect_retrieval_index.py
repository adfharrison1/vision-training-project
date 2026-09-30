"""Inspect committed retrieval index manifest (and optional query similarity)."""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import yaml

from eval.dataset import EvalProfile, resolve_profile
from plant_id.infrastructure.config.settings import Settings
from plant_id.infrastructure.retrieval.index_manifest import (
    IndexPoint,
    load_manifest,
    load_vectors,
)
from plant_id.infrastructure.retrieval.openrouter_embedder import (
    OpenRouterEmbeddingError,
    embed_image_path,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Summarize retrieval index manifest.")
    parser.add_argument(
        "--index-dir",
        type=Path,
        default=None,
        help="Index directory (default: settings retrieval_index_dir)",
    )
    parser.add_argument(
        "--profile",
        choices=[profile.value for profile in EvalProfile],
        default=None,
        help="Only show labels present in this eval profile manifest",
    )
    parser.add_argument(
        "--query-image",
        type=Path,
        default=None,
        help="Embed a query photo via OpenRouter and print top prototype hits",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="Top hits for --query-image",
    )
    return parser


def _labels_for_profile(profile_name: str) -> set[str]:
    profile = resolve_profile(profile_name)
    manifest_path = Path(__file__).resolve().parent / "profiles" / f"{profile.value}.yaml"
    raw = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    labels: set[str] = set()
    for item in raw.get("observations", []):
        species = item.get("species")
        if isinstance(species, str):
            labels.add(species)
    return labels


def _cosine_scores(vectors: np.ndarray, query: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1.0, norms)
    normalized = vectors / norms
    q = query / (np.linalg.norm(query) or 1.0)
    return normalized @ q


def _print_point(point: IndexPoint, score: float | None = None) -> None:
    suffix = f" score={score:.4f}" if score is not None else ""
    source = f" src={point.source_image}" if point.source_image else ""
    print(
        f"  {point.catalog_label!r} kind={point.prototype_kind} "
        f"id={point.prototype_id}{source}{suffix}"
    )


def summarize_manifest(
    *,
    index_dir: Path,
    label_filter: set[str] | None,
) -> int:
    manifest = load_manifest(index_dir)
    points = manifest.points
    if label_filter is not None:
        points = tuple(p for p in points if p.catalog_label in label_filter)
    counts = Counter(p.catalog_label for p in points)
    print(
        f"Index {index_dir}: {len(points)} points "
        f"({manifest.embed_provider}/{manifest.embed_model}, dim={manifest.embed_dim})"
    )
    for label in sorted(counts):
        print(f"{label}: {counts[label]} prototype(s)")
        for point in points:
            if point.catalog_label == label:
                _print_point(point)
    return len(points)


def query_index(
    settings: Settings,
    *,
    index_dir: Path,
    query_image: Path,
    top: int,
    label_filter: set[str] | None,
) -> None:
    manifest = load_manifest(index_dir)
    vectors = load_vectors(index_dir)
    query = embed_image_path(settings, query_image)
    scores = _cosine_scores(vectors, query)
    order = np.argsort(-scores)
    print(f"\nQuery {query_image} (top {top}):")
    shown = 0
    for index in order:
        point = manifest.points[int(index)]
        if label_filter is not None and point.catalog_label not in label_filter:
            continue
        _print_point(point, float(scores[int(index)]))
        shown += 1
        if shown >= top:
            break


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = Settings()
    index_dir = args.index_dir or settings.retrieval_index_dir
    label_filter = _labels_for_profile(args.profile) if args.profile else None
    try:
        summarize_manifest(index_dir=index_dir, label_filter=label_filter)
        if args.query_image is not None:
            query_index(
                settings,
                index_dir=index_dir,
                query_image=args.query_image,
                top=args.top,
                label_filter=label_filter,
            )
    except (FileNotFoundError, OpenRouterEmbeddingError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
