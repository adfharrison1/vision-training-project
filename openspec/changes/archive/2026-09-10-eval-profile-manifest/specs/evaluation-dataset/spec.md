## MODIFIED Requirements

### Requirement: Split filtering

The eval dataset loader SHALL expose split membership so callers can enumerate train, validation, or test images.

#### Scenario: Test split enumeration

- **WHEN** the eval runner requests the test split
- **THEN** the loader SHALL return only images whose `setid` value is `3`

#### Scenario: Test split size

- **WHEN** the full Oxford 102 dataset is loaded
- **THEN** the test split SHALL contain approximately 6,149 labelled images (10 train and 10 validation images per class; remainder is test)

#### Scenario: Profile-based subset

- **WHEN** the eval runner requests profile `smoke` or `quick`
- **THEN** the loader SHALL return observations from the configured profile manifest (`eval/profiles/quick.yaml` by default): first 4 rows for `smoke`, all 8 rows for `quick`, each row specifying one species and one image

#### Scenario: Full profile

- **WHEN** the eval runner requests profile `full`
- **THEN** the loader SHALL return all test-split images in stable sorted index order

#### Scenario: Split id mapping

- **WHEN** split names `train`, `validation`, or `test` are requested
- **THEN** the loader SHALL map them to setid values `1`, `2`, and `3` respectively

## ADDED Requirements

### Requirement: Profile manifest validation

The eval dataset loader SHALL validate profile manifest rows before running identification.

#### Scenario: Species and image consistency

- **WHEN** a manifest row lists a species and image filename
- **THEN** the loader SHALL verify the species is in the catalog and the image's Oxford ground truth matches the declared species

#### Scenario: Manifest override

- **WHEN** the eval runner is invoked with `--profile-manifest /path/to.yaml`
- **THEN** the loader SHALL use that file instead of the default manifest
