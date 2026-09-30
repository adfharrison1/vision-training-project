"""Build multi-prototype retrieval index artifacts from git sheets."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

from eval.oxford_train_prototypes import assert_not_test_split, train_image_paths_for_label
from eval.prototype_curation import load_prototype_curation, resolve_curated_train_paths
from plant_id.infrastructure.config.settings import Settings
from plant_id.infrastructure.retrieval.index_manifest import (
    IndexPoint,
    RetrievalIndexManifest,
    default_index_dir,
    save_manifest,
    save_vectors,
    stable_point_id,
)
from plant_id.infrastructure.retrieval.openrouter_embedder import (
    OpenRouterEmbeddingError,
    embed_image_path,
)
from plant_id.infrastructure.retrieval.openrouter_embedder import (
    embed_text as openrouter_embed_text,
)
from plant_id.infrastructure.species.file_catalog import FileSpeciesCatalog
from plant_id.infrastructure.species_sheets.loader import load_all_sheets


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build retrieval index artifacts.")
    parser.add_argument(
        "--max-prototypes",
        type=int,
        default=None,
        help="Max train image prototypes per species (default: settings)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output directory (default: artifacts/retrieval_index)",
    )
    return parser


def build_index(
    settings: Settings,
    *,
    max_prototypes: int,
    out_dir: Path,
) -> RetrievalIndexManifest:
    sheets = load_all_sheets(settings.species_sheets_dir)
    catalog = FileSpeciesCatalog(settings.species_catalog_path)
    class_names = catalog.list_class_names()
    curation = load_prototype_curation(settings.species_sheets_dir)
    points: list[IndexPoint] = []
    vectors: list[np.ndarray] = []

    for catalog_label, sheet in sorted(sheets.items()):
        text_id = "retrieval_text"
        point_id = stable_point_id(
            catalog_label=catalog_label,
            prototype_kind="text",
            prototype_id=text_id,
        )
        points.append(
            IndexPoint(
                point_id=point_id,
                catalog_label=catalog_label,
                prototype_kind="text",
                prototype_id=text_id,
                retrieval_text=sheet.retrieval_text,
                context_block=sheet.context_block,
            )
        )
        vectors.append(openrouter_embed_text(settings, sheet.retrieval_text))

        curated_names = curation.get(catalog_label)
        if curated_names:
            image_paths = resolve_curated_train_paths(
                catalog_label,
                curated_names,
                class_names=class_names,
            )
        else:
            image_paths = train_image_paths_for_label(
                catalog_label,
                class_names=class_names,
                max_images=max_prototypes,
            )
        for image_index, image_path in enumerate(image_paths):
            assert_not_test_split(image_path)
            if curated_names:
                prototype_id = f"curated-{Path(image_path.name).stem}"
            else:
                prototype_id = f"train-{image_index:02d}"
            point_id = stable_point_id(
                catalog_label=catalog_label,
                prototype_kind="image",
                prototype_id=prototype_id,
            )
            points.append(
                IndexPoint(
                    point_id=point_id,
                    catalog_label=catalog_label,
                    prototype_kind="image",
                    prototype_id=prototype_id,
                    retrieval_text=sheet.retrieval_text,
                    context_block=sheet.context_block,
                    source_image=str(image_path.resolve()),
                )
            )
            vectors.append(embed_image_path(settings, image_path))

    stacked = np.stack(vectors, axis=0)
    manifest = RetrievalIndexManifest(
        embed_provider="openrouter",
        embed_model=settings.retrieval_embed_model,
        collection_name=settings.qdrant_collection,
        embed_dim=int(stacked.shape[1]),
        points=tuple(points),
    )
    save_manifest(out_dir, manifest)
    save_vectors(out_dir, stacked)
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    settings = Settings()
    out_dir = args.out or default_index_dir()
    max_prototypes = args.max_prototypes or settings.retrieval_max_prototypes_per_species
    try:
        manifest = build_index(
            settings,
            max_prototypes=max_prototypes,
            out_dir=out_dir,
        )
    except OpenRouterEmbeddingError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(
        f"Wrote {len(manifest.points)} prototypes ({manifest.embed_dim}-dim, "
        f"{manifest.embed_provider}/{manifest.embed_model}) to {out_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
