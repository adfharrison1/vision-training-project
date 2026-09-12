## ADDED Requirements

### Requirement: Eval run thread grouping in Opik

When identification runs inside an eval trace session, the infrastructure observability layer SHALL group observation traces in Opik using a shared thread identifier.

#### Scenario: Thread id matches eval run

- **WHEN** tracing is enabled and `eval_trace_session` wraps an eval observation
- **THEN** the exported Opik trace SHALL set `thread_id` to the session's `eval_run_id`

#### Scenario: Non-eval identify unchanged

- **WHEN** tracing is enabled for ad-hoc `plant-id identify` (no eval trace session)
- **THEN** the system SHALL NOT set an eval `thread_id` and behaviour SHALL remain as today

#### Scenario: Parallel eval threads

- **WHEN** multiple eval observations run concurrently (for example sharded eval with `--workers` greater than 1) and tracing is enabled
- **THEN** each observation trace SHALL share the same `thread_id` (`eval_run_id`) without cross-talk between worker contexts
