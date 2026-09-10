## MODIFIED Requirements

### Requirement: Eval profiles and improvement loop documentation

The project SHALL document named eval profiles and the eval-to-Opik diagnosis workflow.

#### Scenario: Profile table documented

- **WHEN** a developer reads eval documentation
- **THEN** they SHALL find profiles `smoke` (4 images), `quick` (8 images, default), and `full` (all test images) with expected runtime guidance for default `qwen3-vl:2b`

#### Scenario: Profile manifest documented

- **WHEN** a developer reads eval documentation
- **THEN** they SHALL find that smoke and quick use `eval/profiles/quick.yaml`, that each row lists `species` and `image` independently, and that `--profile-manifest` overrides the default file

#### Scenario: Improvement loop documented

- **WHEN** a developer reads eval documentation
- **THEN** they SHALL find the workflow: run eval with `--eval-run-id` → read JSON report failures → inspect linked Opik traces → change one variable → re-run the same profile
