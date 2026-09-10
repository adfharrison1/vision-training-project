## ADDED Requirements

### Requirement: Oxford 102 eval dataset documentation

The project SHALL document how to obtain and lay out Oxford 102 Flowers files for eval commands.

#### Scenario: Dataset download instructions

- **WHEN** a developer reads setup or eval documentation
- **THEN** they SHALL find the Oxford 102 download URL and the expected layout under `data/flowers/` (`jpg/`, `imagelabels.mat`, `setid.mat`)

#### Scenario: Test split size documented

- **WHEN** a developer reads eval documentation
- **THEN** they SHALL find that the Oxford 102 test split contains approximately 6,149 images and that profile `full` is a long-running benchmark

#### Scenario: Eval without dataset

- **WHEN** Oxford 102 files are not present
- **THEN** documentation SHALL state that unit tests skip dataset-dependent cases and full eval commands require the download

### Requirement: Eval profiles and improvement loop documentation

The project SHALL document named eval profiles and the eval-to-Opik diagnosis workflow.

#### Scenario: Profile table documented

- **WHEN** a developer reads eval documentation
- **THEN** they SHALL find profiles `smoke` (4 images), `quick` (8 images, default), and `full` (all test images) with expected runtime guidance for default `qwen3-vl:2b`

#### Scenario: Improvement loop documented

- **WHEN** a developer reads eval documentation
- **THEN** they SHALL find the workflow: run eval with `--eval-run-id` → read JSON report failures → inspect linked Opik traces → change one variable → re-run the same profile

### Requirement: Default vision model for eval

The project SHALL document `qwen3-vl:2b` as the default vision model and how to override for comparison.

#### Scenario: Default model documented

- **WHEN** a developer reads setup or eval documentation
- **THEN** they SHALL find that `PLANT_ID_VISION_MODEL` defaults to `qwen3-vl:2b` and that `qwen3-vl:8b` may be used for accuracy comparison

### Requirement: Pl@ntNet eval baseline documentation

The project SHALL document optional Pl@ntNet baseline configuration for eval-only comparison.

#### Scenario: API key documented

- **WHEN** a developer reads eval baseline documentation
- **THEN** they SHALL find the required environment variable name for the Pl@ntNet API key and that the baseline is optional and eval-only

#### Scenario: Runtime boundary stated

- **WHEN** a developer reads Pl@ntNet documentation
- **THEN** it SHALL state that Pl@ntNet is never used by runtime `plant-id identify`
