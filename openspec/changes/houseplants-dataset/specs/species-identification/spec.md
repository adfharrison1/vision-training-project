## MODIFIED Requirements

### Requirement: Configurable closed-set species catalog

Runtime identification SHALL constrain predictions to labels from a configurable species catalog file. Application and domain code SHALL NOT hard-code benchmark or dataset names.

#### Scenario: Default bundled catalog

- **WHEN** no custom catalog path is configured
- **THEN** the system SHALL load `resources/species_catalog/default.txt` containing the unified 152-class vocabulary (102 Oxford labels plus 50 appended houseplant extension labels)

#### Scenario: Demo uses configured catalog labels

- **WHEN** a developer runs the documented demo command
- **THEN** the prompt SHALL constrain predictions toward labels from the configured catalog
