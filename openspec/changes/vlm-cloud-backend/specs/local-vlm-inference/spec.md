## MODIFIED Requirements

### Requirement: VLM identification repository

The infrastructure layer SHALL provide a local Ollama implementation of `IdentificationRepository` selected when runtime backend is `vlm`.

#### Scenario: Observation with multiple photos

- **WHEN** an identification is requested with two or three photographs of the same plant
- **THEN** the system SHALL include all supplied photographs in a single model request

#### Scenario: Observation with single photo

- **WHEN** an identification is requested with one photograph
- **THEN** the system SHALL proceed with a single-image model request

#### Scenario: Ollama request failure

- **WHEN** Ollama is unreachable or returns an error during inference
- **THEN** the system SHALL fail with an error that preserves the observation identifier

### Requirement: Runtime isolation from external identification APIs

The local Ollama inference module SHALL NOT call Pl@ntNet, iNaturalist, or other external plant identification services.

#### Scenario: Local-only inference path

- **WHEN** backend `vlm` executes the local VLM code path
- **THEN** it SHALL communicate only with the local Ollama service for model inference

#### Scenario: Ollama-only transport for vlm backend

- **WHEN** backend `vlm` executes the local VLM code path
- **THEN** it SHALL NOT call third-party plant identification APIs
