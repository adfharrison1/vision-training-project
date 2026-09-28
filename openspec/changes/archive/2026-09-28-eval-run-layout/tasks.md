## Phase 1 — New layout (implementation)

- [x] 1.1 Add `eval_runs_dir` and rename/default `identify_artifacts_dir` in `Settings`; update `.env.example`, README, tests
- [x] 1.2 Add `artifact_dir` optional param to `execute_identify` / `build_identify_use_case`; wire `FileArtifactRepository` root
- [x] 1.3 Add `eval/run_registry.py` — run dir creation, `manifest.json`, `index.json` append, `git_commit` helper
- [x] 1.4 Add required `--run-purpose` to `eval.run_oxford102`; add `run_purpose` (+ optional `git_commit`) to `EvalReport`
- [x] 1.5 Write report to `eval_runs/{id}/eval/report.json`; route forensics to `eval_runs/{id}/eval/failures/`; pass grouped `artifact_dir` per observation
- [x] 1.6 Unit tests: CLI rejects empty purpose; manifest/index written; artifact paths under run dir
- [x] 1.7 Update `agent/commands` (`eval-run`, `eval-triage`, `eval-debug`), AGENTS.md, eval README for new paths and required purpose
- [x] 1.8 Amend `openspec/changes/parallel-eval-sharding/` proposal + design for `eval_runs/` layout and allowed report fields

## Phase 2 — Retrofill

- [x] 2.1 Add migration script to relocate `artifacts/eval/*.json` and `artifacts/*eval-*` into `eval_runs/{id}/`
- [x] 2.2 Backfill `index.json` and per-run `manifest.json` with best-effort `run_purpose` from report metadata and known run slugs
- [x] 2.3 Document running migration once locally; verify `/eval-triage` on a retro run

## Phase 3 — Cleanup

- [x] 3.1 Remove stale references to `artifacts/eval/` in specs after archive sync
- [x] 3.2 Agentic review: AGENTS.md improvement-loop paths point at `eval_runs/index.json`
- [x] 3.3 Run `/verify` after Phase 1+2

## Verification

- [x] V1 `uv run python -m eval.run_oxford102 --profile smoke --eval-run-id layout-smoke --run-purpose "smoke test new layout" --backend vlm-cloud` creates full tree under `eval_runs/layout-smoke/`
- [x] V2 `plant-id identify` still writes only under `identify_artifacts/`
