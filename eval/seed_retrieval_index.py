"""Seed local Qdrant from built retrieval index artifacts."""

from __future__ import annotations

import argparse
import sys

from qdrant_client import QdrantClient

from plant_id.infrastructure.config.settings import Settings
from plant_id.infrastructure.retrieval.index_manifest import default_index_dir, load_manifest
from plant_id.infrastructure.retrieval.qdrant_store import seed_from_index_dir


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Upsert retrieval index into Qdrant.")
    parser.add_argument(
        "--index-dir",
        type=str,
        default=None,
        help="Directory containing manifest.json and vectors.npy",
    )
    args = parser.parse_args(argv)
    settings = Settings()
    index_dir = default_index_dir() if args.index_dir is None else args.index_dir
    try:
        load_manifest(index_dir)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    client = QdrantClient(url=settings.qdrant_url, timeout=settings.qdrant_timeout_seconds)
    count = seed_from_index_dir(
        client,
        index_dir=index_dir,
        collection_name=settings.qdrant_collection,
    )
    print(f"Upserted {count} points into collection {settings.qdrant_collection!r}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
