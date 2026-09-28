## Why

Oxford eval runs are sequential and wall-clock bound (~2–3 min/image on `qwen3-vl:2b`, with occasional 7+ min thinking tails). A developer on Intel macOS with two local Ollama servers wants optional parallelism to cut eval time without changing runtime identification or report consumers. Today there is no supported way to shard one eval run across hosts and still produce a single standard JSON report.

## What Changes

- Add an **opt-in** eval-runner mode that shards observations across multiple Ollama host URLs within **one** `run_oxford102` invocation (default remains **1 worker** on `PLANT_ID_OLLAMA_HOST` — current behaviour unchanged).
- Introduce CLI flags / env for **worker count** and **host list** (e.g. `--workers 2` and `--ollama-hosts http://127.0.0.1:11434,http://127.0.0.1:11435`).
- Run shard workers concurrently; assign observations deterministically (stable manifest order preserved in output).
- **Merge shard results in-process** and write **one** JSON report to `eval_runs/{eval_run_id}/eval/report.json` using the existing `EvalReport` schema (same observation row shape; may include `run_purpose` and `git_commit` from eval-run-layout).
- Keep Opik tracing **optional and independent**: when `PLANT_ID_OPIK_ENABLED=true`, each sharded observation still traces with the same `eval_run_id` metadata; when off, sharded runs work identically except `trace_id` is absent.
- When tracing is enabled during an eval run, set Opik **`thread_id` to `eval_run_id`** on each observation trace so sequential and parallel sharded runs appear as **one Thread** in the Opik UI (in addition to existing metadata filtering).
- Document how to start a second local Ollama server and recommended settings for 16 GB Intel Mac (including running with Opik on or off — developer's choice).

## Depends on

- `eval-dataset-baseline` — Oxford eval runner, profiles, report format, Opik eval metadata
- `local-opik-observability` — optional trace linkage in reports (unchanged contract)

## Decision gates (resolved in design.md)

- Default `--workers 1` preserves today's sequential runner.
- Host count MUST be ≥ worker count; workers round-robin across hosts.
- Report observation order MUST match profile/manifest order, not completion order.
- `duration_total_ms` in the merged report is **wall-clock** of the full sharded run.
- Report JSON MAY include `run_purpose` and `git_commit` (see `eval-run-layout`); sharding MUST NOT add shard-specific top-level fields.
- Runtime `IdentifyPlantUseCase` / CLI identify path unchanged (eval-only host override and eval artifact grouping).

## Capabilities

### New Capabilities

_(none)_

### Modified Capabilities

- `evaluation-metrics`: sharded eval execution, merged single report, worker/host CLI
- `local-llm-observability`: eval traces grouped in Opik via `thread_id=eval_run_id`
- `local-dev-environment`: docs for multi-Ollama eval setup and memory guidance

## Non-goals

- Changing runtime identification or default `PLANT_ID_OLLAMA_HOST` behaviour
- Auto-starting or managing Ollama server processes (developer starts servers manually)
- More than modest local parallelism (design targets **2 workers** on 16 GB Intel; higher counts undocumented)
- Separate per-shard report files as the primary output (merge is mandatory)
- Pl@ntNet baseline sharding in v1 (sequential or disabled when sharded — see design)
- Fixing VLM thinking-loop failures (prompt/model work remains separate)

## Impact

- `eval/run_oxford102.py` — worker pool, host assignment, merge before `write_report`
- `src/plant_id/infrastructure/observability/opik_tracing.py` — set `thread_id=eval_run_id` when `eval_trace_session` is active
- New small helpers under `eval/` (e.g. sharding / host parsing) — no imports from runtime layers
- `eval/README.md`, root `README.md`, `AGENTS.md` — optional sharded eval docs
- Unit tests for host parsing, ordering, and merged metrics; no integration test requiring two live servers in CI
