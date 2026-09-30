# species-identification Specification

## Purpose
Accept an observation of one plant (1–3 photos) and produce structured ranked species predictions suitable for comparison against Oxford 102 ground truth in later eval work.

## Requirements

### Requirement: Application use case entry point

Species identification SHALL be executed through an application-layer use case that depends on `IdentificationRepository`, not on a concrete VLM client.

#### Scenario: Use case uses repository port

- **WHEN** `IdentifyPlantUseCase` executes
- **THEN** it SHALL call `IdentificationRepository.identify` and SHALL NOT import Ollama or infrastructure modules directly

### Requirement: Observation input model

An observation SHALL contain an identifier and one to three photograph paths depicting the same plant.

#### Scenario: Valid observation with multiple photos

- **WHEN** an observation is constructed with two photograph paths
- **THEN** the domain model SHALL accept it as valid

#### Scenario: Too many photographs

- **WHEN** an observation is constructed with more than three photograph paths
- **THEN** validation SHALL reject it before the repository is invoked

#### Scenario: No photographs

- **WHEN** an observation is constructed with zero photograph paths
- **THEN** validation SHALL reject it before the repository is invoked

### Requirement: Configurable closed-set species catalog

Runtime identification SHALL constrain predictions to labels from a configurable species catalog file. Application and domain code SHALL NOT hard-code benchmark or dataset names.

#### Scenario: Default bundled catalog

- **WHEN** no custom catalog path is configured
- **THEN** the system SHALL load `resources/species_catalog/default.txt` (Oxford 102 vocabulary in the default setup)

#### Scenario: Demo uses configured catalog labels

- **WHEN** a developer runs the documented demo command
- **THEN** the prompt SHALL constrain predictions toward labels from the configured catalog

### Requirement: Prediction result structure

The identification result SHALL include observation id, ranked predictions, model metadata, and prompt version.

#### Scenario: Result fields present

- **WHEN** an identification completes successfully
- **THEN** the output SHALL include the observation id, an ordered list of predictions with rank and species label, the model tag, and the prompt version

### Requirement: Optional uncertainty flag

The system SHALL support marking an observation as uncertain when the top prediction lacks sufficient confidence, using a documented threshold.

#### Scenario: Low-confidence prediction

- **WHEN** the top prediction score or model-indicated confidence is below the documented threshold
- **THEN** the result SHALL include an explicit uncertain flag without calling external services

### Requirement: No checklist or aggregate pass rule

The system SHALL NOT implement property-level checklists, required-item lists, or PASS/FAIL aggregate rules.

#### Scenario: Single-plant identification only

- **WHEN** an identification is requested
- **THEN** the system SHALL produce species predictions for the plant shown only, not a survey of multiple target species

### Requirement: Optional RAG context injection

When species retrieval is enabled at composition time, the identification path SHALL append retrieved species `context_block` text to the VLM prompt in infrastructure, without changing `IdentifyPlantUseCase` inputs or domain rules.

#### Scenario: RAG disabled default

- **WHEN** RAG is not enabled in settings
- **THEN** identification behavior SHALL match the pre-RAG prompt and repository path

#### Scenario: RAG enabled

- **WHEN** RAG is enabled and retrieval returns top-K sheets
- **THEN** the VLM prompt SHALL include formatted context derived from those sheets while the model still selects `species_label` only from the allowed catalog list
