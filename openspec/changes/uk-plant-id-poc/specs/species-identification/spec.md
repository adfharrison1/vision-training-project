## Purpose

Accept an observation of one plant (1–3 photos) and produce structured ranked species predictions suitable for comparison against Oxford 102 ground truth in later eval work.

## ADDED Requirements

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

### Requirement: Oxford 102 class vocabulary for demo

For this change, demo and smoke-test identifications SHALL target the Oxford 102 Flowers class vocabulary.

#### Scenario: Demo uses Oxford 102 labels

- **WHEN** a developer runs the documented demo command
- **THEN** the prompt SHALL constrain or guide predictions toward Oxford 102 class names

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
