"""Relocate legacy eval artifacts into eval_runs/ bundles and rebuild index."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

from eval.run_registry import (
    EvalRunManifest,
    append_index_entry,
    eval_run_paths,
    index_entry_from_manifest,
    manifest_from_report,
    utc_now_iso,
    write_manifest,
)
from plant_id.infrastructure.config.settings import Settings

_REPORT_SUFFIX = re.compile(r"^(\d{8}T\d{6}Z)-(?P<run_id>.+)\.json$")

# Best-effort purposes for historical slugs (override with report field when present).
KNOWN_RUN_PURPOSES: dict[str, str] = {
    "smoke-check": "Smoke profile sanity check",
    "prompt-v1-baseline": "Baseline closed-set prompt comparison",
    "mixed16-cloud-opik": "Mixed 16 species cloud eval with Opik tracing",
    "yellow16-none-r3": "Yellow subset reasoning_effort=none iteration 3",
    "layout-smoke": "Smoke test new eval_runs layout",
}


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _legacy_eval_dir(root: Path) -> Path:
    return root / "artifacts" / "eval"


def _legacy_identify_dir(root: Path) -> Path:
    return root / "artifacts"


def discover_report_files(legacy_eval: Path) -> dict[str, Path]:
    """Map eval_run_id -> newest legacy report path."""
    by_run: dict[str, Path] = {}
    if not legacy_eval.is_dir():
        return by_run
    for path in legacy_eval.glob("*.json"):
        match = _REPORT_SUFFIX.match(path.name)
        if match is None:
            continue
        run_id = match.group("run_id")
        existing = by_run.get(run_id)
        if existing is None or path.stat().st_mtime >= existing.stat().st_mtime:
            by_run[run_id] = path
    return by_run


def infer_run_purpose(run_id: str, report_payload: dict) -> str:
    if isinstance(report_payload.get("run_purpose"), str):
        purpose = report_payload["run_purpose"].strip()
        if purpose:
            return purpose
    return KNOWN_RUN_PURPOSES.get(run_id, f"Migrated eval run {run_id}")


def migrate_run(
    *,
    root: Path,
    eval_runs_root: Path,
    run_id: str,
    report_path: Path,
    dry_run: bool,
) -> EvalRunManifest | None:
    paths = eval_run_paths(eval_runs_root, run_id)
    if paths.report_path.is_file() and not dry_run:
        return None

    report_payload = json.loads(report_path.read_text(encoding="utf-8"))
    run_purpose = infer_run_purpose(run_id, report_payload)
    git_commit = report_payload.get("git_commit")
    if git_commit is not None and not isinstance(git_commit, str):
        git_commit = None

    started_at = str(report_payload.get("generated_at") or utc_now_iso())
    finished_at = started_at

    if not dry_run:
        paths.artifacts_dir.mkdir(parents=True, exist_ok=True)
        paths.eval_dir.mkdir(parents=True, exist_ok=True)
        if not paths.report_path.is_file():
            shutil.copy2(report_path, paths.report_path)

        legacy_failures = _legacy_eval_dir(root) / run_id / "failures"
        if legacy_failures.is_dir():
            if paths.failures_dir.exists():
                shutil.rmtree(paths.failures_dir)
            shutil.copytree(legacy_failures, paths.failures_dir)

        identify_dir = _legacy_identify_dir(root)
        obs_prefix = f"eval-{run_id}-"
        for artifact in identify_dir.glob("*.json"):
            try:
                payload = json.loads(artifact.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            observation_id = payload.get("observation_id")
            if isinstance(observation_id, str) and observation_id.startswith(obs_prefix):
                dest = paths.artifacts_dir / artifact.name
                if not dest.exists():
                    shutil.copy2(artifact, dest)

    manifest = manifest_from_report(
        paths=paths,
        eval_runs_root=eval_runs_root,
        run_purpose=run_purpose,
        prompt_version=str(
            report_payload.get("inference", {}).get("prompt_version")
            or report_payload.get("prompt_version")
            or "unknown"
        ),
        started_at=started_at,
        finished_at=finished_at,
        git_commit=git_commit,
        report_payload=report_payload,
    )

    if not dry_run:
        write_manifest(paths=paths, eval_runs_root=eval_runs_root, manifest=manifest)
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Migrate legacy eval artifacts to eval_runs/.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned migrations without writing files",
    )
    parser.add_argument(
        "--dataset-root",
        type=Path,
        default=None,
        help="Project root (default: repository root)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.dataset_root or _project_root()
    settings = Settings()
    eval_runs_root = settings.eval_runs_dir
    legacy_eval = _legacy_eval_dir(root)

    reports = discover_report_files(legacy_eval)
    if not reports:
        print(f"No legacy reports found under {legacy_eval}", file=sys.stderr)
        return 0

    manifests: list[EvalRunManifest] = []
    for run_id, report_path in sorted(reports.items()):
        print(f"{'[dry-run] ' if args.dry_run else ''}migrate {run_id} <- {report_path}")
        manifest = migrate_run(
            root=root,
            eval_runs_root=eval_runs_root,
            run_id=run_id,
            report_path=report_path,
            dry_run=args.dry_run,
        )
        if manifest is not None:
            manifests.append(manifest)

    if args.dry_run:
        print(f"Would migrate {len(manifests)} run(s)")
        return 0

    for manifest in manifests:
        append_index_entry(eval_runs_root, index_entry_from_manifest(manifest))

    print(f"Migrated {len(manifests)} run(s); index at {eval_runs_root / 'index.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
