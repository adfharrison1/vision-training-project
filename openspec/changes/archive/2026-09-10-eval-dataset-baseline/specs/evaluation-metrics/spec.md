## Purpose

Compute standard top-k accuracy and per-class breakdowns when comparing identification predictions to Oxford 102 ground truth.

## ADDED Requirements

### Requirement: Top-k accuracy metrics

The eval metrics module SHALL compute top-1 and top-3 accuracy over a list of (ground_truth, predictions) pairs where predictions are ordered by rank.

#### Scenario: Top-1 correct

- **WHEN** the highest-ranked prediction label equals the ground-truth label
- **THEN** top-1 accuracy SHALL count that observation as correct

#### Scenario: Top-3 correct

- **WHEN** the ground-truth label appears among the first three ranked predictions
- **THEN** top-3 accuracy SHALL count that observation as correct

#### Scenario: Label matching rule

- **WHEN** comparing a prediction to ground truth
- **THEN** labels SHALL match by exact string equality on canonical catalog labels (case-sensitive)

### Requirement: Per-class aggregation

The eval metrics module SHALL produce per-class counts suitable for identifying weak classes.

#### Scenario: Per-class summary

- **WHEN** metrics are computed over a completed eval run
- **THEN** the output SHALL include per ground-truth class: total count, top-1 correct count, and top-3 correct count

### Requirement: Eval profiles

The eval runner SHALL support named profiles with fixed default observation counts on the test split.

#### Scenario: Quick profile default

- **WHEN** a developer runs the eval runner without specifying a profile
- **THEN** the runner SHALL use profile `quick` with 8 test-split observations

#### Scenario: Smoke profile

- **WHEN** profile `smoke` is selected
- **THEN** the runner SHALL evaluate exactly 4 test-split observations

#### Scenario: Full profile opt-in

- **WHEN** profile `full` is selected
- **THEN** the runner SHALL evaluate all test-split observations (~6,149) and SHALL document that runtime is a long-running benchmark, not a daily improvement loop

#### Scenario: Duration budget

- **WHEN** `--max-duration` is set (e.g. `30m`)
- **THEN** the runner SHALL stop after the budget is exceeded and SHALL still write a partial report for completed observations

### Requirement: Eval report artifact

The eval runner SHALL persist a structured report summarising aggregate and per-class metrics.

#### Scenario: Report written after run

- **WHEN** an eval run completes successfully
- **THEN** the system SHALL write a JSON report under `artifacts/eval/` including `eval_run_id`, profile name, model tag, backend id, split name, observation count, total duration, top-1 accuracy, top-3 accuracy, and per-class breakdown

#### Scenario: Per-observation detail

- **WHEN** an eval run completes
- **THEN** the report SHALL include per-observation rows with image id, ground truth, top prediction, match flags, and duration in milliseconds

#### Scenario: Partial run failures

- **WHEN** one or more observations fail identification
- **THEN** the report SHALL record failure count, list failures separately, and SHALL still compute metrics over successful observations

### Requirement: Opik trace linkage in eval reports

When Opik tracing is enabled during an eval run, the eval report SHALL link failures to traces for diagnosis.

#### Scenario: Trace metadata on eval observations

- **WHEN** tracing is enabled and the eval runner identifies an observation
- **THEN** the corresponding Opik trace SHALL include metadata fields `eval_run_id`, `eval_profile`, and `observation_id`

#### Scenario: Trace id in report rows

- **WHEN** tracing is enabled and identification succeeds
- **THEN** the per-observation report row SHALL include the Opik `trace_id` when available

#### Scenario: Tracing disabled

- **WHEN** tracing is disabled
- **THEN** the eval runner SHALL complete and write reports without requiring Opik or `trace_id` fields

### Requirement: Metrics module stays in eval boundary

Accuracy computation SHALL live under `eval/` and SHALL NOT be imported by runtime identification layers.

#### Scenario: Shared schema only

- **WHEN** metrics consume identification results
- **THEN** they SHALL use the shared prediction schema without importing infrastructure repositories
