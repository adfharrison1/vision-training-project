## Why

Eval and ad-hoc identify output currently lands in a flat, gitignored `artifacts/` tree with timestamp soup and split writers (per-image JSON vs `artifacts/eval/` reports). Improvement-loop runs lack a durable record of **why** each eval was executed, so triage depends on chat history. We need a first-class eval run bundle (grouped artifacts, report, optional forensics) plus a machine-readable catalog agents and humans can search without inferring intent from filenames.

## What Changes

- Introduce **`eval_runs/`** as the root for Oxford eval bundles: `eval_runs/{eval_run_id}/artifacts/`, `eval_runs/{eval_run_id}/eval/report.json`, `eval_runs/{eval_run_id}/eval/failures/`.
- Introduce **`identify_artifacts/`** (rename from default `artifacts/`) for runtime **`plant-id identify`** and **`demo`** only — flat per-observation JSON, **no** required run purpose.
- Require **`--run-purpose`** (non-empty string) on **`eval.run_oxford102`**; persist on report and run manifest; optional **`git_commit`** captured at run start when available.
- Write **`eval_runs/index.json`** (catalog of runs) and **`eval_runs/{eval_run_id}/manifest.json`** (paths, env snapshot, purpose, summary metrics).
- Route eval per-observation identify artifacts into **`eval_runs/{eval_run_id}/artifacts/`** via composition (`artifact_dir` override on `execute_identify` for eval only).
- **BREAKING:** default report path moves from `artifacts/eval/{timestamp}-{id}.json` to `eval_runs/{id}/eval/report.json`; failure forensics move under the same run’s `eval/failures/`.
- Phase 2: migration script to relocate existing reports and `eval-*` identify JSON into run bundles; backfill `index.json` / `manifest.json` with best-effort `run_purpose` (no guarantee of historical accuracy).
- Update **`agent/commands`** (`eval-run`, `eval-triage`, `eval-debug`), README, AGENTS.md, and tests for new paths and required purpose.
- Amend in-flight change **`parallel-eval-sharding`** so merged reports and grouped artifacts use the same **`eval_runs/{eval_run_id}/`** layout (one bundle per eval invocation).

## Capabilities

### New Capabilities

_(none — layout and catalog requirements extend existing eval and agent specs)_

### Modified Capabilities

- `evaluation-metrics`: eval report location, required `run_purpose`, JSON manifests (`index.json`, per-run `manifest.json`), separate identify vs eval artifact roots, grouped per-run identify artifacts
- `agent-dev-commands`: `/eval-run` must collect `--run-purpose`; triage/debug commands locate reports and forensics under `eval_runs/`

## Depends on

- `eval-dataset-baseline` — Oxford runner, profiles, report schema, Opik linkage
- Recent eval observability work (split metrics, failure forensics) — paths will move under `eval_runs/`

## Decision gates (resolved in design.md)

- Eval-only required purpose; identify/demo unchanged (no purpose field).
- JSON manifests only (no markdown manifest files).
- Settings: `PLANT_ID_IDENTIFY_ARTIFACTS_DIR` + `PLANT_ID_EVAL_RUNS_DIR` (names finalized in design).
- Retro migration is best-effort; legacy files may remain under `_legacy/` if unmappable.

## Non-goals

- Requiring run purpose or grouping for **`plant-id identify`** / **`demo`**
- Cloud or remote artifact storage; remains local gitignored dirs
- Replacing Opik as the trace UI; manifests point to reports and optional `trace_id` in report rows
- Auto-deleting old runs or enforcing retention policy
- Changing domain/application use case contracts beyond optional `artifact_dir` on composition entrypoint

## Impact

- `eval/run_oxford102.py`, `eval/report.py`, `eval/failure_forensics.py`
- `src/plant_id/infrastructure/config/settings.py`, `file_artifacts.py`, `interfaces/composition/` (`execute_identify`, container)
- `.gitignore`, README, eval README, AGENTS.md, agent commands
- `openspec/changes/parallel-eval-sharding/` — proposal/design deltas for report paths and allowed report fields
- Unit tests for path layout, manifest writers, CLI validation of `--run-purpose`
