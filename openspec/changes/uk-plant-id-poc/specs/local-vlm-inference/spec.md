## Purpose

Send photographs of a single plant to a locally running vision-language model and receive structured, validated species predictions.

## ADDED Requirements

### Requirement: VLM identification repository

The infrastructure layer SHALL provide a VLM implementation of `IdentificationRepository` using local Ollama.

#### Scenario: Observation with multiple photos

- **WHEN** an identification is requested with two or three photographs of the same plant
- **THEN** the system SHALL include all supplied photographs in a single model request

#### Scenario: Observation with single photo

- **WHEN** an identification is requested with one photograph
- **THEN** the system SHALL proceed with a single-image model request

#### Scenario: Ollama request failure

- **WHEN** Ollama is unreachable or returns an error during inference
- **THEN** the system SHALL fail with an error that preserves the observation identifier

### Requirement: Structured species prediction output

The system SHALL require the vision model to return structured data containing a ranked list of species predictions with names and supporting evidence text.

#### Scenario: Valid structured response

- **WHEN** the model returns a response matching the prediction schema
- **THEN** the system SHALL parse and validate the response into a typed observation result

#### Scenario: Invalid or unparseable response

- **WHEN** the model returns content that does not validate against the prediction schema
- **THEN** the system SHALL fail the identification and record the raw model response for debugging

### Requirement: Top-k predictions

The structured output SHALL include up to three ranked species predictions unless fewer are confidently returned.

#### Scenario: Top-k prediction list

- **WHEN** identification succeeds
- **THEN** the result SHALL contain between one and three predictions each with rank, species label, and evidence description

### Requirement: Raw response persistence

The system SHALL persist complete model input and raw model output for each identification run.

#### Scenario: Identification artifact saved

- **WHEN** an identification completes or fails after receiving a model response
- **THEN** the system SHALL write a persisted record containing inputs, raw model output, parsed result or parse error, model tag, prompt version, and timestamp

### Requirement: Deterministic inference settings

Identification inference SHALL use fixed model and generation settings documented for reproducibility.

#### Scenario: Reproducible configuration

- **WHEN** two identification runs use the same photos, model, and prompt version
- **THEN** the system SHALL use the same documented inference configuration including temperature fixed at 0

### Requirement: Runtime isolation from external identification APIs

The inference module SHALL NOT call Pl@ntNet, iNaturalist, or other external identification services.

#### Scenario: Local-only inference path

- **WHEN** the runtime identification code path executes
- **THEN** it SHALL communicate only with the local Ollama service

### Requirement: Pipeline progress events

The VLM repository MAY emit numbered pipeline stage events via the domain `ApplicationEvents` helpers during identification.

#### Scenario: Stage events during inference

- **WHEN** an `ApplicationEvents` handler is bound and identification runs
- **THEN** the VLM repository SHALL emit stage events for validation, prompt build, Ollama inference, and response parsing

#### Scenario: No presentation coupling in infrastructure

- **WHEN** the VLM repository emits progress events
- **THEN** it SHALL NOT import Rich or other terminal UI libraries
