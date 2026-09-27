## MODIFIED Requirements

### Requirement: No external identification services in runtime dependencies

The runtime application SHALL NOT require network access to third-party plant identification APIs. Backend `vlm` SHALL remain usable offline aside from localhost Ollama. Backend `vlm-cloud` SHALL require network access to the user-configured inference endpoint.

#### Scenario: Runtime works offline aside from Ollama

- **WHEN** a developer runs identify or demo commands with `--backend vlm` and network disabled except localhost Ollama
- **THEN** identification SHALL complete without calling external plant identification APIs

#### Scenario: Cloud backend requires configured endpoint

- **WHEN** a developer runs identify or eval with `--backend vlm-cloud`
- **THEN** documentation SHALL state that network access to the configured base URL and a valid `PLANT_ID_VLM_CLOUD_API_KEY` are required

## ADDED Requirements

### Requirement: Cloud VLM configuration documentation

The project SHALL document how to configure backend `vlm-cloud` with OpenAI-compatible settings and a reference example for Fireworks AI.

#### Scenario: Environment variables documented

- **WHEN** a developer reads setup or eval documentation
- **THEN** they SHALL find `PLANT_ID_VLM_CLOUD_API_KEY`, `PLANT_ID_VLM_CLOUD_BASE_URL`, `PLANT_ID_VLM_CLOUD_MODEL`, optional `PLANT_ID_VLM_CLOUD_VENDOR`, and timeout settings

#### Scenario: API key canonical name

- **WHEN** documentation explains authentication
- **THEN** it SHALL state that only `PLANT_ID_VLM_CLOUD_API_KEY` is read by the application and MAY show exporting the same secret from a vendor env var in the shell without implying automatic fallback in code

#### Scenario: Fireworks reference preset

- **WHEN** a developer reads cloud setup documentation
- **THEN** they SHALL find an example base URL, model id `accounts/fireworks/models/qwen3-vl-8b-instruct`, and vendor label `fireworks` for the maintainer’s eval workflow

### Requirement: Backend-scoped environment verification

Environment verification SHALL support checking cloud VLM configuration separately from the default Ollama checks.

#### Scenario: Default verify remains Ollama-focused

- **WHEN** a developer runs the default environment verification command without cloud flags
- **THEN** the command SHALL continue to validate local Ollama and the configured Ollama vision model

#### Scenario: Cloud verify option

- **WHEN** a developer runs environment verification with the documented cloud backend option
- **THEN** the command SHALL confirm required cloud settings are present and SHALL report a clear error if the API key or base URL is missing

### Requirement: Eval default backend documentation

Eval documentation SHALL state that the Oxford 102 eval runner defaults to backend `vlm-cloud` and that `--backend vlm` selects local Ollama for parity runs.

#### Scenario: Eval backend default documented

- **WHEN** a developer reads eval documentation
- **THEN** they SHALL find that `run_oxford102` defaults to `vlm-cloud` and that local Ollama eval requires an explicit `--backend vlm`
