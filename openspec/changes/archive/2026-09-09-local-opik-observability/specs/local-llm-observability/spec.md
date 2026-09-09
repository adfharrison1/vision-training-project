## Purpose

Provide local-only, real-time observability for Ollama VLM identification calls during development.

## ADDED Requirements

### Requirement: Local-only observability backend

The project SHALL use self-hosted Opik for LLM trace collection. Observability data MUST NOT be sent to Comet cloud or other external telemetry services.

#### Scenario: Tracing disabled by default

- **WHEN** no observability settings enable tracing
- **THEN** identification SHALL behave identically to the pre-observability implementation and SHALL NOT require a running Opik server

#### Scenario: Local Opik server

- **WHEN** tracing is enabled and Opik is running locally
- **THEN** each VLM identification call SHALL export a trace to the configured local Opik URL

#### Scenario: Opik unreachable

- **WHEN** tracing is enabled but the local Opik server is unreachable
- **THEN** identification SHALL still complete or fail based on Ollama alone and SHALL NOT block the user with observability errors

### Requirement: Infrastructure-layer instrumentation

Opik integration SHALL live in the infrastructure layer and SHALL NOT introduce Opik imports in domain, application, or interfaces CLI modules.

#### Scenario: VLM repository tracing

- **WHEN** tracing is enabled and `VlmOllamaIdentificationRepository.identify` runs
- **THEN** the system SHALL record an LLM span covering the Ollama `chat` request with model tag and token/timing metadata when available

#### Scenario: Layer independence preserved

- **WHEN** import-linter contracts are run
- **THEN** domain, application, and interfaces CLI modules SHALL remain free of Opik imports

### Requirement: Trace content for VLM debugging

Traces SHALL capture fields needed to debug closed-set identification prompts.

#### Scenario: Successful identification trace

- **WHEN** identification succeeds with tracing enabled
- **THEN** the trace SHALL include observation identifier, model tag, prompt version, and parsed prediction summary metadata

#### Scenario: Ollama timing metadata

- **WHEN** Ollama returns duration and token count fields
- **THEN** the trace SHALL record them on the LLM span

#### Scenario: Thinking output

- **WHEN** the model response includes thinking/reasoning content
- **THEN** the trace SHALL preserve that content in span metadata or output for inspection in Opik UI

### Requirement: Observability is not a runtime identification dependency

Opik SHALL NOT implement `IdentificationRepository` and SHALL NOT participate in species prediction logic.

#### Scenario: Identification without observability

- **WHEN** tracing is disabled
- **THEN** `IdentifyPlantUseCase` and repository contracts SHALL be unchanged

### Requirement: CLI progress unchanged

`ApplicationEvents` CLI progress SHALL remain the terminal feedback mechanism; Opik SHALL NOT replace Rich progress output.

#### Scenario: Concurrent progress and traces

- **WHEN** a user runs `plant-id identify` with tracing enabled
- **THEN** CLI stage progress SHALL still appear on stderr and Opik traces SHALL be written separately
