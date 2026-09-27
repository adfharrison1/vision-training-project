## REMOVED Requirements

### Requirement: Runtime repository local-only

**Reason**: The project adds an opt-in `vlm-cloud` backend for hosted OpenAI-compatible VLM inference while keeping third-party plant ID APIs out of runtime repositories.

**Migration**: Use backend `vlm` for local Ollama (default on interactive CLI). Use backend `vlm-cloud` only when cloud settings are configured. Pl@ntNet remains eval-only.

## ADDED Requirements

### Requirement: Runtime repository boundaries

Runtime `IdentificationRepository` implementations SHALL NOT call third-party plant identification APIs (Pl@ntNet, iNaturalist, and similar species-ID services).

#### Scenario: No plant-ID SaaS in repositories

- **WHEN** any runtime identification repository executes
- **THEN** it SHALL NOT invoke external plant identification SaaS APIs

#### Scenario: Hosted VLM via vlm-cloud

- **WHEN** backend `vlm-cloud` is selected and configured
- **THEN** the repository SHALL call only the user-configured OpenAI-compatible vision chat endpoint and project prompt assets

#### Scenario: Local VLM via vlm

- **WHEN** backend `vlm` is selected
- **THEN** the repository SHALL communicate only with local Ollama and project prompt assets

## MODIFIED Requirements

### Requirement: Composition at the boundary

Backend selection and dependency wiring SHALL occur in `interfaces/composition`, not inside use cases or infrastructure. Species catalog implementations SHALL be injected into identification repositories at composition time, not passed to the use case directly.

#### Scenario: CLI backend flag

- **WHEN** a developer runs identify with `--backend vlm`
- **THEN** the CLI SHALL wire the local Ollama VLM repository implementation (with injected species catalog) into the use case before execution

#### Scenario: CLI cloud backend flag

- **WHEN** a developer runs identify with `--backend vlm-cloud`
- **THEN** the CLI SHALL wire the cloud VLM repository implementation (with injected species catalog) into the use case before execution
