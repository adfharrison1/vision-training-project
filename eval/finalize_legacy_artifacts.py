"""One-shot backfill: artifacts/ -> eval_runs/ + identify_artifacts/, then remove legacy tree."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

from eval.migrate_eval_runs import discover_report_files, migrate_run
from eval.run_registry import (
    EvalRunManifest,
    eval_run_paths,
    index_entry_from_manifest,
    utc_now_iso,
    write_manifest,
)
from plant_id.infrastructure.config.settings import Settings

_IMAGE_STEM_SUFFIX = re.compile(r"-image_\d+$", re.IGNORECASE)


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _legacy_root(root: Path) -> Path:
    return root / "artifacts"


def _legacy_eval_reports(root: Path) -> Path:
    return root / "artifacts" / "eval"


def infer_run_id_from_observation_id(observation_id: str) -> str | None:
    if not observation_id.startswith("eval-"):
        return None
    body = observation_id[5:]
    body = _IMAGE_STEM_SUFFIX.sub("", body)
    return body or None


def observation_id_to_run_id(
    observation_id: str,
    *,
    known_run_ids: list[str],
    report_observation_map: dict[str, str],
) -> str | None:
    if observation_id in report_observation_map:
        return report_observation_map[observation_id]
    rest = observation_id[5:] if observation_id.startswith("eval-") else observation_id
    matches = [rid for rid in known_run_ids if rest.startswith(rid + "-") or rest == rid]
    if matches:
        return max(matches, key=len)
    return infer_run_id_from_observation_id(observation_id)


def build_report_observation_map(eval_runs_root: Path) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for report_path in eval_runs_root.glob("*/eval/report.json"):
        run_id = report_path.parent.parent.name
        try:
            payload = json.loads(report_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        for row in payload.get("observations", []):
            if not isinstance(row, dict):
                continue
            obs_id = row.get("observation_id")
            if isinstance(obs_id, str):
                mapping[obs_id] = run_id
    return mapping


def ensure_orphan_run_bundle(
    *,
    eval_runs_root: Path,
    run_id: str,
    dry_run: bool,
) -> None:
    paths = eval_run_paths(eval_runs_root, run_id)
    if paths.report_path.is_file():
        return
    if dry_run:
        return
    paths.artifacts_dir.mkdir(parents=True, exist_ok=True)
    paths.eval_dir.mkdir(parents=True, exist_ok=True)
    manifest = EvalRunManifest(
        eval_run_id=run_id,
        run_purpose=f"Migrated eval artifacts without legacy report ({run_id})",
        profile="unknown",
        backend="unknown",
        model_tag="unknown",
        prompt_version="unknown",
        split="unknown",
        started_at=utc_now_iso(),
        finished_at=utc_now_iso(),
        git_commit=None,
        report_path=str(paths.report_path.relative_to(eval_runs_root)),
        artifacts_dir=str(paths.artifacts_dir.relative_to(eval_runs_root)),
        failures_dir=str(paths.failures_dir.relative_to(eval_runs_root)),
        observation_count=0,
        partial=True,
    )
    write_manifest(paths=paths, eval_runs_root=eval_runs_root, manifest=manifest)


def copy_eval_artifacts_from_legacy(
    *,
    root: Path,
    eval_runs_root: Path,
    dry_run: bool,
) -> tuple[int, list[str]]:
    legacy = _legacy_root(root)
    known_run_ids = sorted(
        {p.name for p in eval_runs_root.iterdir() if p.is_dir()}
        | set(discover_report_files(_legacy_eval_reports(root)).keys()),
        key=len,
        reverse=True,
    )
    report_obs_map = build_report_observation_map(eval_runs_root)
    copied = 0
    errors: list[str] = []

    for artifact in legacy.glob("*.json"):
        try:
            payload = json.loads(artifact.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            errors.append(f"{artifact.name}: invalid json ({exc})")
            continue
        observation_id = payload.get("observation_id")
        if not isinstance(observation_id, str) or not observation_id.startswith("eval-"):
            continue

        run_id = observation_id_to_run_id(
            observation_id,
            known_run_ids=known_run_ids,
            report_observation_map=report_obs_map,
        )
        if run_id is None:
            errors.append(f"{artifact.name}: could not infer eval_run_id from {observation_id!r}")
            continue

        ensure_orphan_run_bundle(eval_runs_root=eval_runs_root, run_id=run_id, dry_run=dry_run)
        dest = eval_run_paths(eval_runs_root, run_id).artifacts_dir / artifact.name
        if dest.exists():
            if not dry_run:
                artifact.unlink()
            continue
        if not dry_run:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(artifact), str(dest))
        copied += 1

    return copied, errors


def move_identify_artifacts(
    *,
    root: Path,
    identify_dir: Path,
    dry_run: bool,
) -> tuple[int, list[str]]:
    legacy = _legacy_root(root)
    moved = 0
    errors: list[str] = []

    for artifact in legacy.glob("*.json"):
        try:
            payload = json.loads(artifact.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            errors.append(f"{artifact.name}: invalid json ({exc})")
            continue
        observation_id = payload.get("observation_id")
        if isinstance(observation_id, str) and observation_id.startswith("eval-"):
            continue

        dest = identify_dir / artifact.name
        if dest.exists():
            if not dry_run:
                artifact.unlink()
            moved += 1
            continue
        if not dry_run:
            identify_dir.mkdir(parents=True, exist_ok=True)
            shutil.move(str(artifact), str(dest))
        moved += 1

    return moved, errors


def migrate_all_reports(*, root: Path, eval_runs_root: Path, dry_run: bool) -> int:
    reports = discover_report_files(_legacy_eval_reports(root))
    count = 0
    for run_id, report_path in sorted(reports.items()):
        paths = eval_run_paths(eval_runs_root, run_id)
        needs_report = not paths.report_path.is_file()
        if not needs_report and not dry_run:
            continue
        manifest = migrate_run(
            root=root,
            eval_runs_root=eval_runs_root,
            run_id=run_id,
            report_path=report_path,
            dry_run=dry_run,
        )
        if manifest is not None:
            count += 1
    return count


def rebuild_index(eval_runs_root: Path, dry_run: bool) -> int:
    entries: list = []
    for manifest_path in sorted(eval_runs_root.glob("*/manifest.json")):
        try:
            raw = manifest_path.read_text(encoding="utf-8")
            manifest = EvalRunManifest.model_validate_json(raw)
        except (json.JSONDecodeError, OSError, ValueError):
            continue
        entries.append(index_entry_from_manifest(manifest))
    if dry_run:
        return len(entries)
    index_path = eval_runs_root / "index.json"
    eval_runs_root.mkdir(parents=True, exist_ok=True)
    entries.sort(key=lambda e: e.finished_at, reverse=True)
    from eval.run_registry import EvalRunIndex

    payload = EvalRunIndex(runs=entries).model_dump_json(indent=2) + "\n"
    index_path.write_text(payload, encoding="utf-8")
    return len(entries)


def verify_legacy_empty(root: Path, identify_dir: Path) -> list[str]:
    problems: list[str] = []
    legacy = _legacy_root(root)
    if not legacy.is_dir():
        return problems

    for artifact in legacy.glob("*.json"):
        try:
            payload = json.loads(artifact.read_text(encoding="utf-8"))
            obs = payload.get("observation_id", "")
        except (json.JSONDecodeError, OSError):
            problems.append(f"unreadable json remains: {artifact.name}")
            continue
        if isinstance(obs, str) and obs.startswith("eval-"):
            problems.append(f"eval artifact remains in artifacts/: {artifact.name}")
        else:
            dest = identify_dir / artifact.name
            if not dest.is_file():
                problems.append(f"identify artifact not in identify_artifacts/: {artifact.name}")

    legacy_eval = _legacy_eval_reports(root)
    if legacy_eval.is_dir():
        problems.append("artifacts/eval/ still present after backfill")
    return problems


def remove_legacy_eval_tree(root: Path, dry_run: bool) -> None:
    legacy_eval = _legacy_eval_reports(root)
    if not legacy_eval.is_dir():
        return
    if dry_run:
        return
    shutil.rmtree(legacy_eval)


def remove_legacy_tree(root: Path, dry_run: bool) -> None:
    legacy = _legacy_root(root)
    if not legacy.is_dir():
        return
    if dry_run:
        return
    shutil.rmtree(legacy)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Backfill artifacts/ into eval_runs/ and identify_artifacts/, then remove artifacts/."
        ),
    )
    parser.add_argument("--dry-run", action="store_true", help="Plan only; do not move or delete")
    parser.add_argument("--dataset-root", type=Path, default=None, help="Project root")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.dataset_root or _project_root()
    settings = Settings()
    eval_runs_root = settings.eval_runs_dir
    identify_dir = settings.identify_artifacts_dir

    if not _legacy_root(root).is_dir():
        print("No artifacts/ directory — nothing to finalize.", file=sys.stderr)
        return 0

    report_migrations = migrate_all_reports(
        root=root,
        eval_runs_root=eval_runs_root,
        dry_run=args.dry_run,
    )
    eval_copied, eval_errors = copy_eval_artifacts_from_legacy(
        root=root,
        eval_runs_root=eval_runs_root,
        dry_run=args.dry_run,
    )
    identify_moved, identify_errors = move_identify_artifacts(
        root=root,
        identify_dir=identify_dir,
        dry_run=args.dry_run,
    )
    index_count = rebuild_index(eval_runs_root, dry_run=args.dry_run)

    all_errors = eval_errors + identify_errors
    if all_errors:
        print("Errors:", file=sys.stderr)
        for err in all_errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    if not args.dry_run:
        remove_legacy_eval_tree(root, dry_run=False)

    problems = verify_legacy_empty(root, identify_dir) if not args.dry_run else []
    if problems:
        for problem in problems:
            print(problem, file=sys.stderr)
        return 1

    if not args.dry_run:
        remove_legacy_tree(root, dry_run=False)

    prefix = "[dry-run] " if args.dry_run else ""
    print(
        f"{prefix}reports refreshed/added: {report_migrations}; "
        f"eval artifacts copied: {eval_copied}; "
        f"identify artifacts moved: {identify_moved}; "
        f"index entries: {index_count}"
    )
    if not args.dry_run:
        print(f"Removed {root / 'artifacts'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
