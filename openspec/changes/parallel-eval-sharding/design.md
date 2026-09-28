## Context

See `proposal.md` — Why. Today `eval/run_oxford102.py` loops observations sequentially and every call uses `load_settings().ollama_host`. `execute_identify` already accepts a per-call `Settings` override, so eval can shard without changing domain, application, infrastructure repositories, or runtime CLI behaviour.

## Goals / Non-Goals

**Goals:**
- One `run_oxford102` invocation, optional `--workers N` (default `1`), optional `--ollama-hosts`
- Deterministic host assignment and manifest-order merged report via existing `build_report` / `compute_metrics`
- Opik on or off — no coupling to sharding mode
- Eval runs grouped in Opik Threads via `thread_id=eval_run_id` (sequential and sharded)
- Unit-testable host parsing, assignment, ordering, and merge logic without two live servers in CI

**Non-Goals:**
- Process manager for Ollama servers, Docker compose for Ollama, or cloud GPU routing
- Runtime CLI / `plant-id identify` parallelism
- Adding shard-specific top-level report fields (report path: `eval_runs/<id>/eval/report.json`; `run_purpose` / `git_commit` from eval-run-layout are OK)
- Pl@ntNet baseline under sharding (reject at CLI parse time)
- Guarantees of linear speedup on 16 GB Intel (document expectations only)

## Decisions

### 1. Concurrency model: in-process thread pool

Use `concurrent.futures.ThreadPoolExecutor(max_workers=N)` in `eval/run_oxford102.py`.

Each task calls the existing `_run_local_observation(..., settings=settings_with_host)` path. `execute_identify` → `VlmOllamaIdentificationRepository` constructs an Ollama `Client` per repository instance; passing distinct `settings.ollama_host` per task is sufficient.

**Alternatives considered:**
- **Multiple OS processes** — stronger isolation but harder Opik flush/shutdown and heavier memory; rejected for v1.
- **Same host, many threads** — does not use multiple servers; rejected.
- **External merge of two manual eval runs** — works today but not “single seamless report” in one command; rejected as primary UX.

### 2. Host assignment: round-robin by observation index

For observation at manifest index `i`:

```text
host = hosts[i % len(hosts)]
```

With `--workers 2` and two hosts, even/odd indices map to host A/B. Stable and easy to test.

Worker pool size = `--workers`. Host list length MUST be ≥ workers (validated up front). When `workers == 1`, host list defaults to `[PLANT_ID_OLLAMA_HOST]`.

### 3. CLI and environment

| Input | Default | Notes |
|---|---|---|
| `--workers` | `1` | Parallel worker count |
| `--ollama-hosts` | unset → `[settings.ollama_host]` | Comma-separated base URLs |
| `EVAL_OLLAMA_HOSTS` | unset | Optional env fallback if flag omitted |

Precedence: `--ollama-hosts` overrides env; env overrides single-host default.

Validation errors (exit code 1 before any identify):
- `workers < 1`
- `len(hosts) < workers`
- empty/duplicate-invalid URL after parse
- `--plantnet-baseline` with `workers > 1`

### 4. Merge and report

```text
  run_eval (parent)
      |
      +-- ThreadPool: task(i, image, host)
      |       -> _run_local_observation(... settings.copy with host)
      |       -> returns (i, ObservationResultRow)
      |
      +-- collect all rows, sort by i
      +-- compute_metrics(sorted_rows)
      +-- build_report(... duration_total_ms = wall_clock)
      +-- write_report(eval_runs/<eval_run_id>/eval/report.json)
```

- Reuse `eval/report.py` models; report path is `eval_runs/<eval_run_id>/eval/report.json`.
- `partial` / `--max-duration`: when budget exceeded, stop submitting new tasks; drain in-flight futures; mark `partial=True` with `stopped_reason` (same semantics as sequential).
- Stderr progress: log `[i/total] image_XXXXX.jpg` when each task **starts** or **completes** (pick one; document in implementation — prefer **complete** to reduce interleaved noise).

### 5. Opik behaviour: metadata + thread grouping

Each `_run_local_observation` already wraps `eval_trace_session`; sharded and sequential runs share one `eval_run_id`. Tracing remains controlled only by `PLANT_ID_OPIK_ENABLED`.

**Thread grouping (new):** In `identify_trace`, when `_eval_session` is set, call `opik_context.update_current_trace(thread_id=session.eval_run_id)` after the identify span starts (alongside existing metadata). This follows Opik's model: **one trace per observation**, many traces sharing one **Thread** for the eval run. Works for parallel workers because:

- `eval_trace_session` uses `ContextVar` — each worker thread gets an isolated session
- Each worker exports its own trace with the same `thread_id` and `eval_run_id` metadata
- Ad-hoc `plant-id identify` (no eval session) does not set `thread_id`

**Alternatives considered:**
- **Single parent trace for whole eval** — rejected; Opik guidance is one trace per workflow step; parallel workers would contend on one trace context
- **Metadata filter only** — already works via OQL but no unified Threads UI; insufficient for "unified view"

**Risk:** Opik SDK thread safety under concurrent `start_as_current_span` — mitigated by ContextVar isolation; validate in manual QA (task 6.2).

### 6. Settings override (eval-only)

Add a small helper in `eval/` (e.g. `eval/sharding.py`):

- `parse_ollama_hosts(text: str) -> tuple[str, ...]`
- `resolve_sharding_config(args, settings) -> ShardingConfig`
- `settings_for_host(settings, host) -> Settings` via `model_copy(update={"ollama_host": host})`

Do **not** add `ollama_hosts` to global `Settings` defaults — keeps runtime config surface unchanged.

### 7. Module layout

```text
eval/
  sharding.py          # parse hosts, config dataclass, settings_for_host
  run_oxford102.py     # branch: sequential if workers==1 else pool
src/plant_id/infrastructure/observability/
  opik_tracing.py      # thread_id=eval_run_id when eval session active
tests/unit/eval/
  test_sharding.py     # parse, assign, sort merge
  test_run_oxford102.py  # extend CLI validation tests (mock identify)
tests/unit/infrastructure/
  test_opik_eval_tracing.py  # extend: thread_id set under eval session
```

## Risks / Trade-offs

| Risk | Mitigation |
|---|---|
| 16 GB RAM exhausted by two model loads | Document Opik on/off choice; recommend Activity Monitor; default `--workers 1` |
| Opik SDK not thread-safe under concurrent spans | ContextVar per worker; manual QA with workers=2 + Opik on; unit test mocks `update_current_trace(thread_id=...)` |
| Uneven tail latencies (one 7 min image) | Expected; wall clock not halved; document Amdahl effect |
| `--max-duration` with parallel in-flight work | Stop scheduling; partial report; document behaviour |
| stderr progress interleaving | Single-line completion logs with index prefix |

## Migration Plan

1. Ship behind opt-in flags; default path unchanged.
2. Document second-server setup in `eval/README.md` and README eval section.
3. No migration of existing reports — schema identical.
4. Rollback: omit flags (behaviour reverts to sequential).

## Pinned versions

No new dependencies. Continues using existing pins (Python 3.14.7, ollama 0.6.2, Ollama server 0.33.3+).

## Open Questions

_(none blocking — worker/host validation rules and Pl@ntNet rejection are decided above)_
