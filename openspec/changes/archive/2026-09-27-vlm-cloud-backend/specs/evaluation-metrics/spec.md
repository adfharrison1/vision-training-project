## ADDED Requirements

### Requirement: Eval runner default backend

The Oxford 102 eval runner SHALL default to identification backend `vlm-cloud` while continuing to support `vlm` and `classical` via an explicit flag.

#### Scenario: Default cloud backend

- **WHEN** a developer runs the eval runner without specifying `--backend`
- **THEN** the runner SHALL wire backend `vlm-cloud` through composition

#### Scenario: Local Ollama eval override

- **WHEN** a developer runs the eval runner with `--backend vlm`
- **THEN** the runner SHALL use local Ollama identification with unchanged metrics semantics

### Requirement: Inference metadata in eval reports

Eval reports SHALL record enough inference configuration to compare runs across local and cloud backends without persisting secrets.

#### Scenario: Report includes backend and model

- **WHEN** an eval run completes successfully
- **THEN** the JSON report SHALL include backend id, model identifier, and prompt version used for the run

#### Scenario: Cloud metadata without secrets

- **WHEN** the eval run used backend `vlm-cloud`
- **THEN** the report SHALL include optional cloud vendor label and base URL host only, and SHALL NOT include API keys or full authorization headers
