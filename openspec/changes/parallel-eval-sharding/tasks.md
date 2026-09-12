## 1. Sharding helpers

- [ ] 1.1 Add `eval/sharding.py` with host parsing, `ShardingConfig`, and `settings_for_host()`; verify `tests/unit/eval/test_sharding.py` covers comma-separated URLs, whitespace trim, and `workers > len(hosts)` validation errors

## 2. Opik eval thread grouping

- [ ] 2.1 In `identify_trace`, when `eval_trace_session` is active, call `opik_context.update_current_trace(thread_id=eval_run_id)`; verify `tests/unit/infrastructure/test_opik_eval_tracing.py` asserts thread_id is set for eval and omitted for ad-hoc identify

## 3. Eval runner integration

- [ ] 3.1 Extend `eval/run_oxford102.py` CLI with `--workers` (default 1) and `--ollama-hosts`, plus `EVAL_OLLAMA_HOSTS` env fallback; verify argparse tests reject `--plantnet-baseline` when `--workers > 1`
- [ ] 3.2 Implement threaded sharded execution path that collects `(index, row)` pairs, sorts by index, and calls existing `compute_metrics` + `build_report`; verify unit test mocks show manifest order preserved regardless of completion order
- [ ] 3.3 Keep sequential path when `--workers 1` and verify existing eval unit tests still pass unchanged

## 4. Duration and partial runs

- [ ] 4.1 Apply `--max-duration` to sharded scheduling (stop submitting new tasks, drain in-flight, set `partial`/`stopped_reason`); verify unit test simulates budget exceeded mid-run

## 5. Documentation

- [ ] 5.1 Update `eval/README.md` with sharded eval flags, second-server example, merged-report note, Opik Thread grouping by `eval_run_id`, and 16 GB Intel memory guidance; verify examples match CLI
- [ ] 5.2 Update root `README.md` eval section with a one-paragraph pointer to sharded eval and Opik Threads; verify link/command syntax
- [ ] 5.3 Update `AGENTS.md` eval commands table with optional `--workers` / `--ollama-hosts` note; verify wording distinguishes default single worker

## 6. Manual verification (developer machine)

- [ ] 6.1 Manual QA: start second Ollama on `:11435`, run `mixed16` with `--workers 2`, confirm one report JSON and wall clock improvement; Opik optional on/off smoke
- [ ] 6.2 Manual QA with Opik on: confirm all observation traces for one `--eval-run-id` share the same Opik Thread (thread_id) and remain searchable by `metadata.eval_run_id`

## 7. Agentic coding review

- [ ] 7.1 Review whether `agent/commands/eval-run.md` should mention optional sharding flags and Opik Thread grouping; update if it improves the improvement loop without duplicating README
