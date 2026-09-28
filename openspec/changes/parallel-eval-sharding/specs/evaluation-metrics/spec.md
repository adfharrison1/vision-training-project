## ADDED Requirements

### Requirement: Optional parallel Ollama sharding for eval runs

The eval runner SHALL support an opt-in mode that executes observations concurrently across multiple Ollama host URLs within a single eval invocation, while preserving today's default sequential behaviour.

#### Scenario: Default single worker unchanged

- **WHEN** a developer runs the eval runner without parallel sharding flags
- **THEN** the runner SHALL use one worker and `PLANT_ID_OLLAMA_HOST` exactly as today (sequential observations, one report)

#### Scenario: Enable sharded eval

- **WHEN** the eval runner is invoked with `--workers N` where `N > 1` and a host list of at least `N` distinct Ollama base URLs
- **THEN** the runner SHALL assign observations to workers, execute them concurrently, and produce **one** merged eval report for the run

#### Scenario: Host list configuration

- **WHEN** parallel sharding is enabled
- **THEN** the runner SHALL accept Ollama hosts via `--ollama-hosts` (comma-separated URLs) and/or a documented environment variable, and SHALL validate that the host count is at least the worker count before starting

#### Scenario: Invalid sharding configuration

- **WHEN** `--workers` exceeds the number of configured hosts, or hosts are empty/malformed
- **THEN** the runner SHALL fail fast with a clear error before identifying any observation

#### Scenario: Merged report shape unchanged

- **WHEN** a sharded eval run completes (successfully or with per-observation failures)
- **THEN** the runner SHALL write exactly one JSON report to `eval_runs/<eval_run_id>/eval/report.json` using the existing report schema (same observation row shape as non-sharded runs; MAY include `run_purpose` and `git_commit`)

#### Scenario: Observation order preserved

- **WHEN** a sharded eval run writes the merged report
- **THEN** `observations` and derived `failures` / `per_class` entries SHALL reflect the profile/manifest observation order, not worker completion order

#### Scenario: Wall-clock duration

- **WHEN** a sharded eval run completes
- **THEN** `duration_total_ms` in the report SHALL be the wall-clock elapsed time of the full run (not the sum of per-observation durations)

#### Scenario: Opik tracing optional with sharding

- **WHEN** `PLANT_ID_OPIK_ENABLED=true` during a sharded eval run
- **THEN** each observation SHALL still emit traces with the same `eval_run_id`, `eval_profile`, and `observation_id` metadata, and report rows SHALL include `trace_id` when available

#### Scenario: Opik thread groups eval run

- **WHEN** tracing is enabled and the eval runner identifies an observation inside `eval_trace_session`
- **THEN** the corresponding Opik trace SHALL use `thread_id` equal to `eval_run_id` so all observation traces from that run appear under one Opik Thread (sequential or sharded)

#### Scenario: Opik tracing disabled with sharding

- **WHEN** tracing is disabled during a sharded eval run
- **THEN** the runner SHALL complete and write the merged report without requiring Opik

#### Scenario: Pl@ntNet baseline incompatible with sharding

- **WHEN** `--plantnet-baseline` is combined with `--workers` greater than 1
- **THEN** the runner SHALL reject the invocation with a clear error explaining that Pl@ntNet baseline must run with the default single worker
