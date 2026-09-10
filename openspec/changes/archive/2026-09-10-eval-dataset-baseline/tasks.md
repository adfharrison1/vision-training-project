## 1. Dependencies and dataset module

- [x] 1.1 Promote `scipy==1.18.1` to main `[project] dependencies`, add pinned `httpx` for Pl@ntNet, run `uv lock` and verify `uv sync` succeeds
- [x] 1.2 Extend Oxford 102 loading with `setid.mat` split support and profile selection (`smoke`=4, `quick`=8, `full`=all test) in `eval/dataset.py`; verify unit tests pass for split filtering and profile sizes (skip when dataset absent)
- [x] 1.3 Add unit tests for invalid filenames, out-of-range indices, and test-split count sanity; verify `uv run pytest tests/unit/eval/` passes

## 2. Metrics and report

- [x] 2.1 Implement `eval/metrics.py` with top-1, top-3, and per-class aggregation using exact catalog label matching; verify unit tests with synthetic prediction fixtures
- [x] 2.2 Define eval report JSON schema (including `eval_run_id`, profile, model_tag, per-observation rows, failures list, durations) and writer to `artifacts/eval/`; verify writer creates directory and valid JSON in a unit test

## 3. Opik linkage

- [x] 3.1 Extend infrastructure observability to accept eval metadata (`eval_run_id`, `eval_profile`) and return `trace_id` to callers when tracing enabled; verify unit test with mocked Opik context
- [x] 3.2 Wire eval runner to pass observation ids `eval-{run_id}-{image_stem}` and record `trace_id` in report rows; verify report contains trace_id when `PLANT_ID_OPIK_ENABLED=true` on a smoke run

## 4. Eval runner (local backends)

- [x] 4.1 Implement `eval/run_oxford102.py` CLI (`--profile`, `--eval-run-id`, `--max-duration`, `--backend`, `--split`, `--limit`, `--quiet`, `--dataset-root`, `--output`) defaulting to profile `quick`; verify `--profile smoke` exits 0 with Ollama + dataset
- [x] 4.2 Wire runner to dataset + metrics + report writer; verify smoke report has 4 observations and quick report has 8 when dataset available
- [x] 4.3 Add `@pytest.mark.integration` test for `--profile smoke`; verify skipped when Ollama or dataset unavailable

## 5. Pl@ntNet baseline (optional)

- [x] 5.1 Implement `eval/baselines/plantnet.py` with env-gated API key, retry/backoff, and exact catalog label matching; verify unit tests with mocked HTTP responses
- [x] 5.2 Integrate `--plantnet-baseline` flag into runner and include Pl@ntNet section in report when enabled; verify runner skips cleanly with clear message when API key missing
- [x] 5.3 Verify local metrics still run when Pl@ntNet is disabled or fails mid-run

## 6. Documentation and boundaries

- [x] 6.1 Update `eval/README.md` and README with profiles, 6,149 test-split note, 2b default, eval→Opik MCP workflow, and Pl@ntNet opt-in; verify commands match implemented flags
- [x] 6.2 Confirm eval modules are not imported from `src/plant_id/` and `uv run lint-imports` still passes
- [x] 6.3 Update AGENTS.md eval section with `--profile quick` smoke/improvement-loop guidance; verify agent can run smoke eval from docs alone

## 7. Agentic coding (end of phase)

- [x] 7.1 Review whether eval profile conventions need Cursor rules or skills beyond AGENTS.md; verify any additions are concise and non-duplicative of OpenSpec
