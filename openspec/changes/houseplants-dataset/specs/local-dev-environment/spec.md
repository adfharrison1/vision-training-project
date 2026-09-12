## MODIFIED Requirements

### Requirement: Oxford 102 eval dataset documentation

The project SHALL document how to obtain and lay out Oxford 102 Flowers files for eval commands and how to merge houseplant extension data into the same dataset root.

#### Scenario: Dataset download instructions

- **WHEN** a developer reads setup or eval documentation
- **THEN** they SHALL find the Oxford 102 download URL and the expected layout under `data/flowers/` (`jpg/`, `imagelabels.mat`, `setid.mat`)

#### Scenario: Test split size documented

- **WHEN** a developer reads eval documentation
- **THEN** they SHALL find that the Oxford-only test split contains approximately 6,149 images, that profile `full` is a long-running benchmark, and that merged extension images increase the test count when present

#### Scenario: Eval without dataset

- **WHEN** Oxford 102 files are not present
- **THEN** documentation SHALL state that unit tests skip dataset-dependent cases and full eval commands require the download

### Requirement: Eval profiles and improvement loop documentation

The project SHALL document named eval profiles and the eval-to-Opik diagnosis workflow.

#### Scenario: Profile table documented

- **WHEN** a developer reads eval documentation
- **THEN** they SHALL find profiles `smoke` (4 images), `quick` (8 images, default), `houseplants-quick` (fixed extension manifest), and `full` (all test images) with expected runtime guidance for default `qwen3-vl:2b`

#### Scenario: Profile manifest documented

- **WHEN** a developer reads eval documentation
- **THEN** they SHALL find that smoke and quick use `eval/profiles/quick.yaml`, that houseplants-quick uses `eval/profiles/houseplants-quick.yaml`, that each row lists `species` and `image` independently, and that `--profile-manifest` overrides the default file

#### Scenario: Improvement loop documented

- **WHEN** a developer reads eval documentation
- **THEN** they SHALL find the workflow: run eval with `--eval-run-id` → read JSON report failures → inspect linked Opik traces → change one variable → re-run the same profile

## ADDED Requirements

### Requirement: Houseplant extension curation documentation

The project SHALL document how developers curate and merge the 50-class houseplant extension into the unified dataset.

#### Scenario: Catalog extension documented

- **WHEN** a developer reads dataset curation documentation
- **THEN** they SHALL find the 50 appended catalog labels (lines 103–152), the overlap rule (existing Oxford labels reuse class ids; no duplicate lines), and that `default.txt` grows from 102 to 152 classes

#### Scenario: Curation workflow documented

- **WHEN** a developer adds extension images
- **THEN** documentation SHALL describe: human-confirmed labels → CSV metadata → script-generated merged `imagelabels.mat` and `setid.mat` → continued `image_XXXXX.jpg` indexing from 8190

#### Scenario: Provenance documented

- **WHEN** a developer sources extension photos
- **THEN** documentation SHALL require open licenses with attribution recorded in a provenance file and SHALL state that copyrighted stock imagery must not be committed
