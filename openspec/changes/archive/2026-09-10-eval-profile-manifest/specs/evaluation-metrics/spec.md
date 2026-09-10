## MODIFIED Requirements

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
