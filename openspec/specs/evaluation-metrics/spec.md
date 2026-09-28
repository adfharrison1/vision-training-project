# evaluation-metrics Specification

## Purpose

Compute standard top-k accuracy and per-class breakdowns when comparing identification predictions to Oxford 102 ground truth.

## Requirements

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
- **THEN** the runner SHALL use profile `quick` with 8 manifest observations spanning 8 distinct species

#### Scenario: Smoke profile

- **WHEN** profile `smoke` is selected
- **THEN** the runner SHALL evaluate exactly 4 manifest observations (the first four rows of the profile manifest)

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
- **THEN** the system SHALL write a JSON report to `eval_runs/<eval_run_id>/eval/report.json` including `eval_run_id`, `run_purpose`, profile name, model tag, backend id, split name, observation count, total duration, top-1 accuracy, top-3 accuracy, per-class breakdown, and split accuracy fields when computed

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

### Requirement: Eval runner default backend

The Oxford 102 eval runner SHALL default to identification backend `vlm-cloud` while continuing to support `vlm` and `classical` via an explicit flag.

#### Scenario: Default cloud backend

- **WHEN** a developer runs the eval runner without specifying `--backend`
- **THEN** the runner SHALL wire backend `vlm-cloud` through composition

#### Scenario: Local Ollama eval override

- **WHEN** a developer runs the eval runner with `--backend vlm`
- **THEN** the runner SHALL use local Ollama identification with unchanged metrics semantics

### Requirement: Inference metadata in eval reports

Eval reports SHALL record enough inference configuration to compare runs across local and cloud backends without persisting secrets.

#### Scenario: Report includes backend and model

- **WHEN** an eval run completes successfully
- **THEN** the JSON report SHALL include backend id, model identifier, and prompt version used for the run

#### Scenario: Cloud metadata without secrets

- **WHEN** the eval run used backend `vlm-cloud`
- **THEN** the report SHALL include optional cloud vendor label and base URL host only, and SHALL NOT include API keys or full authorization headers
