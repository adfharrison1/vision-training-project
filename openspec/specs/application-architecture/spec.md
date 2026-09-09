# application-architecture Specification

## Purpose
Define layered application structure with repository interfaces so identification backends (VLM, classical ML) swap without changing domain models or use cases.

## Requirements

### Requirement: Layer boundaries

The codebase SHALL be organised into domain, application, infrastructure, and interfaces layers with strict inward dependency direction.

#### Scenario: Domain independence

- **WHEN** a developer inspects the domain layer
- **THEN** it SHALL contain models and repository interfaces only and SHALL NOT import from application, infrastructure, or interfaces layers

#### Scenario: Application depends on domain abstractions

- **WHEN** a developer inspects application use cases
- **THEN** they SHALL depend on domain models and repository interfaces only, not concrete infrastructure implementations

#### Scenario: Infrastructure independence

- **WHEN** a developer inspects infrastructure repository implementations
- **THEN** they SHALL depend on domain ports and third-party libraries only and SHALL NOT import from application or interfaces layers

#### Scenario: CLI commands use composition for wiring

- **WHEN** a developer inspects CLI command modules under `interfaces/cli`
- **THEN** they SHALL NOT import infrastructure or domain directly and SHALL call shared orchestration in `interfaces/composition`

### Requirement: Identification repository port

The domain layer SHALL define an `IdentificationRepository` interface (protocol) that accepts an `Observation` and returns an `ObservationResult`.

#### Scenario: Swappable backend contract

- **WHEN** a new identification backend is added
- **THEN** it SHALL implement `IdentificationRepository` without modifying the `IdentifyPlantUseCase` application logic

### Requirement: Composition at the boundary

Backend selection and dependency wiring SHALL occur in `interfaces/composition`, not inside use cases or infrastructure. Species catalog implementations SHALL be injected into identification repositories at composition time, not passed to the use case directly.

#### Scenario: CLI backend flag

- **WHEN** a developer runs identify with `--backend vlm`
- **THEN** the CLI SHALL wire the VLM repository implementation (with injected species catalog) into the use case before execution

### Requirement: Shared result model across backends

All identification repository implementations SHALL return the same `ObservationResult` domain model.

#### Scenario: Backend-agnostic output

- **WHEN** identification succeeds via any runtime backend
- **THEN** the result SHALL use the shared prediction schema suitable for Oxford 102 eval metrics

### Requirement: Runtime repository local-only

Runtime `IdentificationRepository` implementations SHALL NOT call external plant identification APIs.

#### Scenario: VLM repository isolation

- **WHEN** the VLM repository executes
- **THEN** it SHALL communicate only with local Ollama and project prompt/RAG assets

### Requirement: Eval adapters separate from repository port

External comparison services (e.g. Pl@ntNet API) SHALL live in eval/benchmark modules and SHALL NOT implement `IdentificationRepository`.

#### Scenario: Eval baseline separation

- **WHEN** an eval baseline adapter is added in a later change
- **THEN** it SHALL remain outside the runtime repository interface hierarchy

### Requirement: Application events port

Cross-cutting runtime observability (pipeline stages, diagnostic events) SHALL use a domain-level `ApplicationEvents` port with context-local binding. Lower layers SHALL call `log_event`, `log_stage`, or `log_wait` helpers and SHALL NOT import presentation libraries.

#### Scenario: Silent default outside CLI session

- **WHEN** code runs without a bound `ApplicationEvents` handler
- **THEN** event calls SHALL be no-ops

#### Scenario: CLI binds terminal handler

- **WHEN** a developer runs `identify` or `demo` without `--quiet`
- **THEN** the CLI SHALL bind a terminal presentation handler for the duration of the use case

#### Scenario: Infrastructure emits events without UI imports

- **WHEN** the VLM repository reports pipeline progress
- **THEN** it SHALL use domain event helpers only and SHALL NOT import Rich or write directly to stderr

### Requirement: Observability adapter in infrastructure

Cross-cutting LLM trace export SHALL be implemented as an infrastructure observability adapter, separate from domain `ApplicationEvents`.

#### Scenario: Two observability mechanisms

- **WHEN** a developer inspects runtime observability
- **THEN** terminal pipeline stages SHALL use domain `ApplicationEvents` and durable LLM traces SHALL use infrastructure Opik integration

#### Scenario: No observability in use case

- **WHEN** a developer inspects `IdentifyPlantUseCase`
- **THEN** it SHALL NOT depend on Opik or any trace exporter

### Requirement: Eval boundary unchanged

Eval modules MAY enable tracing for benchmark runs in future work but SHALL NOT require cloud observability services.

#### Scenario: Eval remains local

- **WHEN** eval code exports traces
- **THEN** it SHALL target the same self-hosted Opik instance or leave tracing disabled
