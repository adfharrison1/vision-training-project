## ADDED Requirements

### Requirement: Separate identify and eval artifact roots

Runtime identification artifacts and eval run bundles SHALL use distinct configurable directory roots.

#### Scenario: Identify and demo artifacts

- **WHEN** a developer runs `plant-id identify` or `plant-id demo`
- **THEN** the system SHALL write per-observation JSON under the configured identify artifacts directory (default `identify_artifacts/`) using the existing flat filename pattern

#### Scenario: Eval does not write identify root

- **WHEN** the Oxford eval runner identifies an observation
- **THEN** the system SHALL NOT write that observation JSON under the identify artifacts root

### Requirement: Eval run bundle layout

Each Oxford eval invocation with a given `eval_run_id` SHALL persist outputs under a single run directory.

#### Scenario: Run directory structure

- **WHEN** an eval run starts with `eval_run_id` `<id>`
- **THEN** the runner SHALL create or use `eval_runs/<id>/artifacts/` for per-observation identify JSON, `eval_runs/<id>/eval/report.json` for the aggregate report, and `eval_runs/<id>/eval/failures/` for parse-failure forensics when applicable

#### Scenario: Grouped per-observation artifacts

- **WHEN** the eval runner completes an observation through the identify use case
- **THEN** the corresponding artifact JSON SHALL be written under `eval_runs/<eval_run_id>/artifacts/`

### Requirement: Required eval run purpose

The eval runner SHALL require a non-empty human-readable purpose for every eval invocation.

#### Scenario: Missing purpose rejected

- **WHEN** a developer runs the eval runner without `--run-purpose` or with an empty string
- **THEN** the runner SHALL exit with a clear error before identifying any observation

#### Scenario: Purpose persisted

- **WHEN** an eval run completes
- **THEN** the JSON report SHALL include field `run_purpose` with the supplied text

### Requirement: Eval run JSON manifests

The eval runner SHALL maintain machine-readable catalogs of eval runs.

#### Scenario: Per-run manifest

- **WHEN** an eval run finishes (including partial runs stopped by duration budget)
- **THEN** the system SHALL write `eval_runs/<eval_run_id>/manifest.json` containing at minimum `eval_run_id`, `run_purpose`, profile, backend, model identifier, prompt version, start/finish timestamps, optional `git_commit`, relative paths to report and artifacts directories, and a summary of top-1 accuracy over all observations when computable

#### Scenario: Index catalog

- **WHEN** an eval run finishes
- **THEN** the system SHALL update `eval_runs/index.json` with an entry for that run including `eval_run_id`, `run_purpose`, profile, timestamps, relative path to the report, and summary metrics sufficient to sort runs without opening each report

### Requirement: Optional git commit on eval runs

When the eval runner can resolve the current git commit at run start, it SHALL record it in manifests and the report.

#### Scenario: Git commit captured

- **WHEN** the eval runner starts inside a git work tree with a resolvable HEAD
- **THEN** `manifest.json` and the eval report SHALL include `git_commit` with the abbreviated or full commit hash

#### Scenario: Git unavailable

- **WHEN** git is unavailable or the directory is not a repository
- **THEN** the eval run SHALL proceed and SHALL set `git_commit` to null in manifest and report

## MODIFIED Requirements

### Requirement: Eval report artifact

The eval runner SHALL persist a structured report summarising aggregate and per-class metrics.

#### Scenario: Report written after run

- **WHEN** an eval run completes successfully
- **THEN** the system SHALL write a JSON report to `eval_runs/<eval_run_id>/eval/report.json` including `eval_run_id`, `run_purpose`, profile name, model tag, backend id, split name, observation count, total duration, top-1 accuracy, top-3 accuracy, per-class breakdown, and split accuracy fields (`top1_accuracy_all`, `parse_failure_count`, `misclassification_count`) when computed

#### Scenario: Per-observation detail

- **WHEN** an eval run completes
- **THEN** the report SHALL include per-observation rows with image id, ground truth, top prediction, match flags, and duration in milliseconds

#### Scenario: Partial run failures

- **WHEN** one or more observations fail identification
- **THEN** the report SHALL record failure count, list failures separately, and SHALL still compute metrics over successful observations
