## Why

The initial eval runner selected smoke/quick images as the first N sorted test-split indices. On Oxford 102 that resolves to `image_00001`–`image_00008`, which are all the same species — useless for measuring accuracy. Improvement rounds need a fixed, diverse, deterministic set of eight species with independently editable image choices.

## What Changes

- Replace smoke/quick index slicing with a YAML **profile manifest** (`eval/profiles/quick.yaml`).
- Each row specifies `species` and `image` independently; ground truth is validated on load.
- `smoke` uses the first four manifest rows; `quick` uses all eight (one image per species).
- Add `--profile-manifest` CLI override; default manifest path documented.
- **`full`** profile unchanged (all test-split images).

## Depends on

- `eval-dataset-baseline` — eval runner, dataset loading, metrics, reports

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- `evaluation-dataset`: smoke/quick selection via manifest instead of first N test indices
- `evaluation-metrics`: quick/smoke profile semantics (8 / 4 distinct species from manifest)
- `local-dev-environment`: document manifest file and edit workflow

## Non-goals

- Random or shuffled profile selection
- Changing `full` profile behaviour
- Runtime identification changes
- New eval metrics or report schema fields

## Impact

- `eval/profile_manifest.py`, `eval/profiles/quick.yaml`
- `eval/dataset.py`, `eval/run_oxford102.py`
- `eval/README.md`, unit tests
- Main specs under `openspec/specs/`
