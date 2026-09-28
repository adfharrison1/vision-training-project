"""Backfill eval/failures JSON from an existing report and identify artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from eval.failure_forensics import ensure_eval_failure_forensics
from eval.metrics import ObservationResultRow
from eval.run_registry import eval_run_paths
from plant_id.interfaces.composition import load_settings


def _rows_from_report(report_path: Path) -> list[ObservationResultRow]:
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    observations = payload.get("observations")
    if not isinstance(observations, list):
        raise ValueError(f"Report missing observations[]: {report_path}")

    rows: list[ObservationResultRow] = []
    for item in observations:
        if not isinstance(item, dict):
            continue
        rows.append(
            ObservationResultRow(
                image=str(item["image"]),
                ground_truth=str(item["ground_truth"]),
                predicted=item.get("predicted"),
                top1_match=bool(item.get("top1_match")),
                top3_match=bool(item.get("top3_match")),
                duration_ms=int(item.get("duration_ms", 0)),
                observation_id=str(item["observation_id"]),
                trace_id=item.get("trace_id"),
                error=item.get("error"),
                predictions=tuple(item.get("predictions") or ()),
            )
        )
    return rows


def sync_failure_forensics(
    eval_run_id: str,
    *,
    eval_runs_root: Path | None = None,
) -> int:
    root = eval_runs_root or load_settings().eval_runs_dir
    paths = eval_run_paths(root, eval_run_id)
    if not paths.report_path.is_file():
        print(f"Report not found: {paths.report_path}", file=sys.stderr)
        return 1

    rows = _rows_from_report(paths.report_path)
    ensure_eval_failure_forensics(
        eval_run_id=eval_run_id,
        rows=rows,
        artifacts_dir=paths.artifacts_dir,
        eval_runs_root=root,
    )
    failures_dir = paths.failures_dir
    count = len(list(failures_dir.glob("*.json"))) if failures_dir.is_dir() else 0
    print(f"Failure forensics: {failures_dir}/ ({count} files)", file=sys.stderr)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Backfill eval/failures JSON from report.json and identify artifacts.",
    )
    parser.add_argument("eval_run_id", help="Eval run slug under eval_runs/")
    parser.add_argument(
        "--eval-runs-root",
        type=Path,
        default=None,
        help="Override eval_runs root (default: settings eval_runs_dir)",
    )
    args = parser.parse_args(argv)
    return sync_failure_forensics(args.eval_run_id, eval_runs_root=args.eval_runs_root)


if __name__ == "__main__":
    raise SystemExit(main())
