# vlm-cloud-inference Specification

## Purpose
Provide hosted vision-language identification through a user-configured OpenAI-compatible API, using the same closed-set prompt and prediction schema as local Ollama, without calling third-party plant identification services.

## Requirements

### Requirement: Cloud VLM identification repository

The infrastructure layer SHALL provide a `vlm-cloud` implementation of `IdentificationRepository` that sends photographs and the closed-set prompt to a user-configured OpenAI-compatible chat completions endpoint with vision message content.

#### Scenario: Observation with multiple photos

- **WHEN** an identification is requested with two or three photographs of the same plant using backend `vlm-cloud`
- **THEN** the system SHALL include all supplied photographs in a single chat completion request

#### Scenario: Observation with single photo

- **WHEN** an identification is requested with one photograph using backend `vlm-cloud`
- **THEN** the system SHALL proceed with a single-image chat completion request

#### Scenario: Cloud request failure

- **WHEN** the configured endpoint is unreachable, returns an HTTP error, or times out
- **THEN** the system SHALL fail with an error that preserves the observation identifier

#### Scenario: Missing cloud configuration

- **WHEN** backend `vlm-cloud` is selected and required cloud settings (API key, base URL, or model) are absent
- **THEN** the system SHALL fail before calling the network with a clear configuration error

### Requirement: User-configurable cloud endpoint

Cloud inference SHALL be configured exclusively through application settings for base URL, API key, model identifier, and timeout. The application SHALL NOT read vendor-specific API key environment variables as implicit fallbacks.

#### Scenario: Canonical API key setting

- **WHEN** cloud identification runs
- **THEN** the system SHALL authenticate using the configured `PLANT_ID_VLM_CLOUD_API_KEY` value only

#### Scenario: Bring-your-own provider

- **WHEN** a developer sets `PLANT_ID_VLM_CLOUD_BASE_URL` and `PLANT_ID_VLM_CLOUD_MODEL` to a compatible provider
- **THEN** identification SHALL use that endpoint and model without code changes to the repository

### Requirement: Structured output parity with local VLM

The cloud repository SHALL use the same closed-set prediction schema, validation rules, top-k limits, uncertainty threshold behaviour, prompt version recording, and artifact persistence semantics as the local Ollama VLM repository.

#### Scenario: Valid structured response

- **WHEN** the model returns assistant content matching the prediction schema
- **THEN** the system SHALL parse and validate the response into the shared `ObservationResult` type

#### Scenario: Invalid or unparseable response

- **WHEN** the model returns content that does not validate against the prediction schema
- **THEN** the system SHALL fail the identification and record the raw model response for debugging

### Requirement: Deterministic cloud inference settings

Cloud identification SHALL use temperature fixed at 0 and document model and prompt version in persisted artifacts for reproducibility comparisons.

#### Scenario: Reproducible configuration

- **WHEN** two cloud identification runs use the same photos, configured model, and prompt version
- **THEN** the system SHALL use the same documented generation settings including temperature 0

### Requirement: Isolation from plant identification SaaS APIs

The cloud VLM repository SHALL NOT call Pl@ntNet, iNaturalist, or other third-party plant identification APIs.

#### Scenario: Hosted VLM only

- **WHEN** the `vlm-cloud` repository executes
- **THEN** it SHALL communicate only with the user-configured OpenAI-compatible inference endpoint and project prompt assets

### Requirement: Pipeline progress events

The cloud VLM repository SHALL emit numbered pipeline stage events via the domain `ApplicationEvents` helpers during identification when a handler is bound, analogous to the Ollama VLM repository.

#### Scenario: Stage events during inference

- **WHEN** an `ApplicationEvents` handler is bound and cloud identification runs
- **THEN** the repository SHALL emit stage events for validation, prompt build, cloud inference, and response parsing

#### Scenario: No presentation coupling in infrastructure

- **WHEN** the cloud repository emits progress events
- **THEN** it SHALL NOT import Rich or other terminal UI libraries

### Requirement: Backend identity for reporting

The cloud repository SHALL expose a stable `backend_id` that includes the configured model identifier so eval reports and artifacts distinguish cloud runs from local Ollama runs.

#### Scenario: Distinct backend id

- **WHEN** identification succeeds via `vlm-cloud`
- **THEN** persisted artifacts and eval reports SHALL record a backend id that identifies the cloud backend and configured model
