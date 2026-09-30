"""Move flat ``eval_runs/<id>/`` bundles into ``full_identify/`` or ``rag_retrieval_only/``."""

from __future__ import annotations

import argparse
import shutil
import sys

from eval.eval_run_roots import (
    FULL_IDENTIFY_SUBDIR,
    LAYOUT_SUBDIRS,
    RAG_RETRIEVAL_ONLY_SUBDIR,
    classify_eval_run_dir,
    full_identify_eval_runs_root,
    rag_retrieval_only_eval_runs_root,
)
from eval.run_registry import rebuild_eval_run_index
from plant_id.interfaces.composition import load_settings


def reorganize_eval_runs(*, dry_run: bool = False) -> tuple[int, int]:
    settings = load_settings()
    eval_root = settings.eval_runs_dir
    targets = {
        FULL_IDENTIFY_SUBDIR: full_identify_eval_runs_root(settings),
        RAG_RETRIEVAL_ONLY_SUBDIR: rag_retrieval_only_eval_runs_root(settings),
    }
    for path in targets.values():
        if not dry_run:
            path.mkdir(parents=True, exist_ok=True)

    moved = 0
    for child in sorted(eval_root.iterdir()):
        if not child.is_dir() or child.name in LAYOUT_SUBDIRS:
            continue
        kind = classify_eval_run_dir(child)
        dest_root = targets[kind]
        dest = dest_root / child.name
        if dest.exists():
            print(f"Skip (already present): {dest}", file=sys.stderr)
            continue
        print(f"{'Would move' if dry_run else 'Move'} {child.name} -> {kind}/", file=sys.stderr)
        if not dry_run:
            shutil.move(str(child), str(dest))
        moved += 1

    root_index = eval_root / "index.json"
    if root_index.is_file():
        archive = eval_root / "_legacy_flat_index.json"
        print(
            f"{'Would archive' if dry_run else 'Archive'} {root_index.name} -> {archive.name}",
            file=sys.stderr,
        )
        if not dry_run:
            if archive.is_file():
                archive.unlink()
            shutil.move(str(root_index), str(archive))

    counts: dict[str, int] = {}
    for kind, root in targets.items():
        if dry_run:
            counts[kind] = len(list(root.glob("*/manifest.json")))
        else:
            counts[kind] = rebuild_eval_run_index(root)
        print(f"{kind}/ index: {counts[kind]} run(s)", file=sys.stderr)

    return moved, counts[FULL_IDENTIFY_SUBDIR] + counts[RAG_RETRIEVAL_ONLY_SUBDIR]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Split flat eval_runs/ bundles into full_identify/ and rag_retrieval_only/.",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    moved, indexed = reorganize_eval_runs(dry_run=args.dry_run)
    prefix = "[dry-run] " if args.dry_run else ""
    print(f"{prefix}Moved {moved} run dir(s); rebuilt indexes ({indexed} manifest entries).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
