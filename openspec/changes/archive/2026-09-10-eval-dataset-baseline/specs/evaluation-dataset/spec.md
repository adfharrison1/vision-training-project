## Purpose

Load Oxford 102 Flowers images, ground-truth labels, and train/val/test splits for offline benchmark runs without coupling to runtime identification code.

## ADDED Requirements

### Requirement: Oxford 102 file layout

The eval dataset loader SHALL expect Oxford 102 files under a configurable root directory (default `data/flowers/`) with at minimum:

- `jpg/image_XXXXX.jpg` image files (1-based index in filename)
- `imagelabels.mat` per-image class ids
- `setid.mat` per-image split ids (1=train, 2=validation, 3=test)

#### Scenario: Default paths resolve

- **WHEN** no custom dataset root is configured
- **THEN** the loader SHALL resolve `data/flowers/jpg/`, `imagelabels.mat`, and `setid.mat` relative to the project root

#### Scenario: Missing dataset files

- **WHEN** required Oxford 102 files are absent
- **THEN** the loader SHALL raise a clear error naming the missing path(s) and pointing to README download instructions

### Requirement: Ground-truth label resolution

The eval dataset loader SHALL resolve each image's canonical species label using the same catalog vocabulary as runtime identification.

#### Scenario: Label from imagelabels and catalog

- **WHEN** an image path `image_00018.jpg` and species catalog are provided
- **THEN** the loader SHALL return the catalog label corresponding to that image's class id in `imagelabels.mat`

#### Scenario: Invalid image filename

- **WHEN** a photo filename does not match `image_XXXXX.jpg`
- **THEN** the loader SHALL reject it with a descriptive error

#### Scenario: Index out of range

- **WHEN** the parsed image index exceeds the label array length
- **THEN** the loader SHALL reject it with a descriptive error

### Requirement: Split filtering

The eval dataset loader SHALL expose split membership so callers can enumerate train, validation, or test images.

#### Scenario: Test split enumeration

- **WHEN** the eval runner requests the test split
- **THEN** the loader SHALL return only images whose `setid` value is `3`

#### Scenario: Test split size

- **WHEN** the full Oxford 102 dataset is loaded
- **THEN** the test split SHALL contain approximately 6,149 labelled images (10 train and 10 validation images per class; remainder is test)

#### Scenario: Profile-based subset

- **WHEN** the eval runner requests profile `smoke`, `quick`, or `full`
- **THEN** the loader SHALL return the first 4, first 8, or all test-split images respectively in stable deterministic order

#### Scenario: Split id mapping

- **WHEN** split names `train`, `validation`, or `test` are requested
- **THEN** the loader SHALL map them to setid values `1`, `2`, and `3` respectively

### Requirement: Eval dataset stays outside runtime layers

Oxford 102 loading code SHALL live under `eval/` and SHALL NOT be imported by domain, application, infrastructure repositories, or runtime CLI identify commands.

#### Scenario: Runtime independence

- **WHEN** a developer runs `plant-id identify`
- **THEN** runtime code SHALL NOT require Oxford 102 dataset files or eval dataset modules
