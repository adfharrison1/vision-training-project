## Purpose

Extend local development setup with optional self-hosted Opik for LLM observability.

## ADDED Requirements

### Requirement: Documented local Opik setup

The project SHALL document how to run self-hosted Opik alongside Ollama for development.

#### Scenario: Developer enables observability

- **WHEN** a developer follows README observability instructions
- **THEN** they SHALL be able to start local Opik, enable tracing via settings, run `plant-id identify`, and view the trace in the Opik UI at the documented local URL

#### Scenario: No cloud account required

- **WHEN** a developer sets up observability
- **THEN** they SHALL NOT be required to create a Comet cloud account or API key

### Requirement: Observability settings

Settings SHALL expose toggles for local Opik integration without affecting default identification behaviour.

#### Scenario: Default off

- **WHEN** a developer runs the project without observability env vars
- **THEN** `opik_enabled` SHALL default to false

#### Scenario: Enable via environment

- **WHEN** a developer sets `PLANT_ID_OPIK_ENABLED=true` and `PLANT_ID_OPIK_BASE_URL` to the local Opik API URL
- **THEN** VLM identification runs SHALL export traces to that URL
