# eval-baseline-plantnet Specification

## Purpose

Provide an optional Pl@ntNet API baseline for eval-only comparison against Oxford 102 ground truth, without affecting runtime identification.

## Requirements

### Requirement: Eval-only Pl@ntNet adapter

Pl@ntNet integration SHALL live under `eval/baselines/` and SHALL NOT implement `IdentificationRepository` or be wired into runtime composition.

#### Scenario: Not a runtime backend

- **WHEN** a developer runs `plant-id identify --backend vlm`
- **THEN** Pl@ntNet code SHALL NOT be invoked

#### Scenario: Explicit opt-in

- **WHEN** the eval runner is invoked without a Pl@ntNet baseline flag
- **THEN** no Pl@ntNet API calls SHALL be made

### Requirement: API key and graceful skip

The Pl@ntNet baseline SHALL require explicit configuration and SHALL skip cleanly when unavailable.

#### Scenario: Missing API key

- **WHEN** Pl@ntNet baseline is requested but no API key is configured
- **THEN** the eval runner SHALL skip Pl@ntNet comparison with a clear message and SHALL still produce local backend metrics

#### Scenario: Rate limit or API error

- **WHEN** Pl@ntNet returns rate-limit or transient API errors
- **THEN** the adapter SHALL apply backoff/retry up to a configured limit and SHALL record skipped observations rather than failing the entire local eval run

### Requirement: Pl@ntNet comparison output

When enabled, the Pl@ntNet baseline SHALL produce a separate comparison section in the eval report.

#### Scenario: Side-by-side baseline metrics

- **WHEN** Pl@ntNet baseline completes for some observations
- **THEN** the eval report SHALL include Pl@ntNet top-1/top-3 metrics computed with the same label-matching rule as local backends where a catalog label match exists

#### Scenario: Unmapped Pl@ntNet species names

- **WHEN** Pl@ntNet returns a species name that does not exactly match any catalog label
- **THEN** the report SHALL count that observation as incorrect for Pl@ntNet metrics and MAY record the raw returned name for inspection

### Requirement: Local eval remains primary

Local backend metrics SHALL always run regardless of Pl@ntNet availability.

#### Scenario: Pl@ntNet disabled

- **WHEN** Pl@ntNet baseline is not enabled
- **THEN** the eval runner SHALL complete local metrics and report writing without external API dependencies
