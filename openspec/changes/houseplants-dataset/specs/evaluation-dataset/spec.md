## MODIFIED Requirements

### Requirement: Oxford 102 file layout

The eval dataset loader SHALL expect dataset files under a configurable root directory (default `data/flowers/`) with at minimum:

- `jpg/image_XXXXX.jpg` image files (1-based index in filename; Oxford indices 1–8189 plus extension indices from 8190 upward when present)
- `imagelabels.mat` per-image class ids (1-based indices into the unified species catalog)
- `setid.mat` per-image split ids (1=train, 2=validation, 3=test)

#### Scenario: Default paths resolve

- **WHEN** no custom dataset root is configured
- **THEN** the loader SHALL resolve `data/flowers/jpg/`, `imagelabels.mat`, and `setid.mat` relative to the project root

#### Scenario: Missing dataset files

- **WHEN** required dataset files are absent
- **THEN** the loader SHALL raise a clear error naming the missing path(s) and pointing to README download and curation instructions

#### Scenario: Extension images present

- **WHEN** merged `imagelabels.mat` contains more label rows than the Oxford-only baseline (8189)
- **THEN** the loader SHALL resolve ground truth for extension indices using the same filename and class-id rules as Oxford images

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

#### Scenario: Class id beyond catalog

- **WHEN** `imagelabels.mat` references a class id greater than the number of catalog lines
- **THEN** the loader SHALL reject it with a descriptive error naming the class id and catalog size

### Requirement: Split filtering

The eval dataset loader SHALL expose split membership so callers can enumerate train, validation, or test images.

#### Scenario: Test split enumeration

- **WHEN** the eval runner requests the test split
- **THEN** the loader SHALL return only images whose `setid` value is `3`

#### Scenario: Test split size

- **WHEN** the Oxford-only dataset is loaded without extension rows
- **THEN** the test split SHALL contain approximately 6,149 labelled images (10 train and 10 validation images per class; remainder is test)

#### Scenario: Profile-based subset

- **WHEN** the eval runner requests profile `smoke` or `quick`
- **THEN** the loader SHALL return observations from the configured profile manifest (`eval/profiles/quick.yaml` by default): first 4 rows for `smoke`, all 8 rows for `quick`, each row specifying one species and one image

#### Scenario: Houseplants profile subset

- **WHEN** the eval runner requests profile `houseplants-quick`
- **THEN** the loader SHALL return observations from `eval/profiles/houseplants-quick.yaml` using the same manifest row validation rules as smoke and quick

#### Scenario: Full profile

- **WHEN** the eval runner requests profile `full`
- **THEN** the loader SHALL return all test-split images in stable sorted index order, including extension test images when merged split files are present

#### Scenario: Split id mapping

- **WHEN** split names `train`, `validation`, or `test` are requested
- **THEN** the loader SHALL map them to setid values `1`, `2`, and `3` respectively

### Requirement: Profile manifest validation

The eval dataset loader SHALL validate profile manifest rows before running identification.

#### Scenario: Species and image consistency

- **WHEN** a manifest row lists a species and image filename
- **THEN** the loader SHALL verify the species is in the catalog and the image's ground truth from `imagelabels.mat` matches the declared species

#### Scenario: Manifest override

- **WHEN** the eval runner is invoked with `--profile-manifest /path/to.yaml`
- **THEN** the loader SHALL use that file instead of the default manifest for profiles that use fixed manifests

## ADDED Requirements

### Requirement: Unified catalog class ids

Extension houseplant classes SHALL occupy catalog lines 103–152 appended to the default bundled catalog without reordering existing Oxford labels.

#### Scenario: Extension class lookup

- **WHEN** an extension image has class id 103 in `imagelabels.mat`
- **THEN** the loader SHALL resolve ground truth to line 103 of the configured species catalog

#### Scenario: Overlap species use existing class ids

- **WHEN** a curated photo depicts a species whose label already exists in lines 1–102
- **THEN** the curation workflow SHALL assign that image an existing class id and SHALL NOT add a duplicate catalog line

### Requirement: Extension split assignment

Extension images SHALL participate in train, validation, and test splits using the same setid encoding as Oxford images.

#### Scenario: Per-class split targets

- **WHEN** extension images are added for a new class
- **THEN** the curation workflow SHALL assign setid values targeting approximately 10 train, 10 validation, and remainder test images per class as volume allows

#### Scenario: Bootstrap minimum

- **WHEN** fewer than 20 images exist for a new class during initial curation
- **THEN** the workflow SHALL still assign valid setid values and SHALL document the actual counts in curation metadata
