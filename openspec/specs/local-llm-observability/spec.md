# local-llm-observability Specification

## Purpose
Provide local-only, real-time observability for Ollama VLM identification calls during development.

## Requirements

### Requirement: Local-only observability backend

The project SHALL use self-hosted Opik for LLM trace collection from all identification backends. Observability data MUST NOT be sent to Comet cloud or other external telemetry services. Inference traffic MAY use hosted VLM endpoints when backend `vlm-cloud` is selected; that SHALL NOT change the Opik export destination.

#### Scenario: Tracing disabled by default

- **WHEN** no observability settings enable tracing
- **THEN** identification SHALL behave identically to the pre-observability implementation and SHALL NOT require a running Opik server

#### Scenario: Local Opik server

- **WHEN** tracing is enabled and Opik is running locally
- **THEN** each identification call for backend `vlm` or `vlm-cloud` SHALL export a trace to the configured local Opik URL

#### Scenario: Opik unreachable

- **WHEN** tracing is enabled but the local Opik server is unreachable
- **THEN** identification SHALL still complete or fail based on the active inference backend alone and SHALL NOT block the user with observability errors

### Requirement: Infrastructure-layer instrumentation

Opik integration SHALL live in the infrastructure layer and SHALL NOT introduce Opik imports in domain, application, or interfaces CLI modules.

#### Scenario: VLM repository tracing

- **WHEN** tracing is enabled and backend `vlm` identification runs
- **THEN** the system SHALL record an LLM span covering the Ollama chat request with model tag and token or timing metadata when available

#### Scenario: Cloud VLM repository tracing

- **WHEN** tracing is enabled and `vlm-cloud` identification runs
- **THEN** the system SHALL record an LLM span covering the OpenAI-compatible chat completion with model id, provider metadata, and token usage when returned by the API

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

### Requirement: Backend-aware trace metadata

Traces SHALL identify which identification backend executed the run so eval diagnosis can filter Ollama versus cloud observations.

#### Scenario: Identify span backend field

- **WHEN** tracing is enabled for an identification
- **THEN** the root identify span metadata SHALL include the repository `backend_id` value for the active backend

#### Scenario: LLM span provider mapping

- **WHEN** tracing is enabled for backend `vlm`
- **THEN** the LLM child span SHALL use provider metadata indicating local Ollama

#### Scenario: Cloud LLM span provider mapping

- **WHEN** tracing is enabled for backend `vlm-cloud`
- **THEN** the LLM child span SHALL use provider metadata indicating OpenAI-compatible cloud inference and SHALL include optional vendor label when configured

#### Scenario: Cloud usage metadata

- **WHEN** the cloud API returns token usage fields on the completion response
- **THEN** the trace SHALL record them on the LLM span usage block

#### Scenario: Optional cloud performance metadata

- **WHEN** the cloud API returns documented performance or latency fields on the completion response
- **THEN** the trace MAY attach them to span metadata without requiring a separate external observability product

### Requirement: Trace content for cloud debugging

Cloud VLM traces SHALL capture the same identification debugging fields as Ollama traces except for Ollama-specific thinking-channel fields.

#### Scenario: Successful cloud identification trace

- **WHEN** cloud identification succeeds with tracing enabled
- **THEN** the trace SHALL include observation identifier, configured model id, prompt version, and parsed prediction summary metadata

#### Scenario: No full image payload in traces

- **WHEN** cloud identification runs with tracing enabled
- **THEN** traces SHALL NOT require storing full base64 image payloads in span metadata
