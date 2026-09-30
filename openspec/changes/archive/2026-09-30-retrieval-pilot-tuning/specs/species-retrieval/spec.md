## ADDED Requirements

### Requirement: Optional curated train prototypes for index build

`eval/build_retrieval_index` SHALL support an optional curated list of prototype images per `catalog_label` (validated on Oxford **train** split, same rules as automatic train prototype selection) used instead of or merged with first-N train scan per species settings.

#### Scenario: Pilot campanula pair

- **WHEN** a maintainer lists curated train images for `bolero deep blue` and `canterbury bells`
- **THEN** built index manifest points SHALL reference those paths as `prototype_kind=image` with stable `prototype_id`s

#### Scenario: Test split rejected

- **WHEN** a curated path resolves to a test-split image
- **THEN** index build SHALL fail with an explicit error (no test leakage)

#### Scenario: Fallback

- **WHEN** no curation is configured for a species with a sheet
- **THEN** index build SHALL retain today’s first-N train behavior up to `retrieval_max_prototypes_per_species`
