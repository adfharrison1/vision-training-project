## Purpose

Clarify how local LLM observability fits layered architecture without violating dependency rules.

## ADDED Requirements

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
