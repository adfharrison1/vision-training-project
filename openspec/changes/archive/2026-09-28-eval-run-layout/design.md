## Context

See `proposal.md`. Today: flat `artifacts/` mixes CLI identify JSON with eval per-image dumps; eval reports live under `artifacts/eval/` with timestamped filenames; failure forensics under `artifacts/eval/<run_id>/failures/`. Agents triage by mtime and filename slugs with no durable `run_purpose`.

## Goals / Non-Goals

**Goals:**

- One directory per eval run with report, grouped identify artifacts, and forensics
- Separate `identify_artifacts/` for CLI identify/demo (unchanged UX, no purpose field)
- Required `--run-purpose` on eval CLI; JSON `index.json` + per-run `manifest.json`
- Optional `git_commit` on eval runs
- Update agent commands and amend `parallel-eval-sharding` paths

**Non-Goals:**

- Purpose or grouping for identify/demo
- Markdown manifests; cloud storage; retention policies
- Changing Opik trace schema beyond existing eval metadata

## Decisions

### 1. Directory layout

```text
identify_artifacts/          # PLANT_ID_IDENTIFY_ARTIFACTS_DIR (rename from artifacts_dir default)
eval_runs/                   # PLANT_ID_EVAL_RUNS_DIR
  index.json
  {eval_run_id}/
    manifest.json
    artifacts/               # FileArtifactRepository root during eval
    eval/
      report.json            # fixed name (EvalReport JSON)
      failures/              # parse forensics
```

**Alternatives:** Single tree with `_type` field — rejected; eval bundles need isolation. Keep old `artifacts/` name for identify — rejected; user asked for clear separation.

### 2. Artifact routing via composition

Add optional `artifact_dir: Path | None` to `execute_identify()` and `build_identify_use_case()`. Eval runner passes `eval_runs/{id}/artifacts`; CLI passes `None` → settings identify dir. Use case unchanged; only repository root varies.

**Alternatives:** Thread-local context — rejected (implicit). Env var per subprocess — rejected (fragile for sharding).

### 3. Manifest writers in `eval/`

New module `eval/run_registry.py` (name TBD): `ensure_run_dirs`, `write_manifest`, `append_index_entry`, `capture_git_commit()`. Called from `run_oxford102` after report write. Pydantic models or typed dicts for manifest/index schema; unit tests on round-trip JSON.

### 4. Settings migration

- Rename field `artifacts_dir` → `identify_artifacts_dir` with env `PLANT_ID_IDENTIFY_ARTIFACTS_DIR` (keep alias `PLANT_ID_ARTIFACTS_DIR` one release? **Decision:** break with doc only — default path `identify_artifacts/`).
- Add `eval_runs_dir` / `PLANT_ID_EVAL_RUNS_DIR`.

### 5. Report path and `--output`

Default report: `eval_runs/{eval_run_id}/eval/report.json`. `--output` override still allowed for tests; default logic changes.

### 6. Retro migration (Phase 2)

Script `scripts/migrate_eval_artifacts.py` or `eval/migrate_runs.py`:

- Glob `artifacts/eval/*-{run_id}.json` → move to `eval_runs/{run_id}/eval/report.json`
- Glob `artifacts/*eval-{run_id}-*.json` → `eval_runs/{run_id}/artifacts/`
- Move `artifacts/eval/{run_id}/failures` → `eval_runs/{run_id}/eval/failures`
- Build index + manifests with best-effort `run_purpose` from conversation/heuristics + report fields
- Leave unmappable files in `identify_artifacts/_legacy/` or `eval_runs/_unmapped/`

### 7. parallel-eval-sharding alignment

Edit `openspec/changes/parallel-eval-sharding/proposal.md` and `design.md`:

- Replace `artifacts/eval/` report path with `eval_runs/{eval_run_id}/eval/report.json`
- Replace “No new required fields” with “May add `run_purpose` and `git_commit`; no shard-specific top-level fields”
- Sharded workers share same `artifact_dir` (thread-safe: unique observation_id per file)

## Risks / Trade-offs

- **[Risk] Breaking docs and muscle memory on `artifacts/eval/`** → Mitigation: migration script + README table; grep update agent commands
- **[Risk] Duplicate eval_run_id overwrites** → Mitigation: refuse to start if run dir exists unless `--force` (optional flag in tasks)
- **[Risk] index.json merge conflicts** → Mitigation: single-writer eval process; append-only array; document no parallel eval same id

## Migration Plan

1. Ship Phase 1 code (new runs only)
2. Run retro script locally (Phase 2)
3. Remove references to old paths in docs/commands
4. Optional symlink `artifacts` → `identify_artifacts` for one release — **defer** unless user wants it

## Open Questions

- Whether to add `--force` when `eval_runs/{id}` already exists (recommend: yes, default refuse)

## Pinned versions

No new runtime dependencies. Same stack as `pyproject.toml` at implementation time (Python 3.14.7, Pydantic 2.13.5, etc.).
