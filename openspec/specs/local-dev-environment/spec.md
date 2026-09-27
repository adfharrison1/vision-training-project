# local-dev-environment Specification

## Purpose
Define a reproducible local development environment for UK plant identification using Python and Ollama on macOS.

## Requirements

### Requirement: Supported platform and runtime versions

The project SHALL document minimum platform requirements and pinned runtime versions needed to run the identifier locally.

#### Scenario: Developer reads environment prerequisites

- **WHEN** a developer opens the project setup documentation
- **THEN** they SHALL find documented requirements for macOS, Python 3.14.7, Node 24.13.1 (OpenSpec tooling only), Ollama 0.33.3+, and the pinned vision model tag

### Requirement: Pinned dependency versions

The project SHALL pin exact stable versions of Python, development tools, and runtime libraries in project metadata and the lockfile.

#### Scenario: Documented version pins

- **WHEN** a developer opens project setup documentation or `pyproject.toml`
- **THEN** they SHALL find exact pinned versions for Python 3.14.7, uv 0.12.10, ruff 0.16.6, pytest 9.1.1, import-linter 2.13, Pydantic 2.13.5, PyYAML 6.0.3, Pillow 12.3.0, ollama 0.6.2, and rich 14.3.2

### Requirement: Python dependency management

The project SHALL use a single Python toolchain with a lockfile so dependencies are installed reproducibly without global package pollution.

#### Scenario: Fresh clone dependency install

- **WHEN** a developer runs the documented install command on a clean clone
- **THEN** a project-local virtual environment SHALL be created and all Python dependencies SHALL install from the lockfile without requiring manual pip configuration

### Requirement: Ollama and model availability

The local development environment SHALL require a running Ollama instance with the configured vision model pulled locally.

#### Scenario: Model verification before identification

- **WHEN** a developer runs the documented environment verification command
- **THEN** the system SHALL confirm Ollama is reachable and the configured vision model is present in `ollama list`

#### Scenario: Missing model detected

- **WHEN** the configured vision model is not present locally
- **THEN** the verification command SHALL fail with an actionable message including the documented model pull command

### Requirement: Environment smoke verification

The project SHALL provide a single documented command that verifies the development environment is correctly configured.

#### Scenario: Successful environment verification

- **WHEN** a developer runs the environment verification command with Ollama running and the model available
- **THEN** the command SHALL exit successfully and report that the environment is ready

#### Scenario: Ollama unavailable

- **WHEN** a developer runs the environment verification command while Ollama is not running
- **THEN** the command SHALL fail with a clear message indicating Ollama is unreachable

### Requirement: Identification CLI commands

The project SHALL provide documented CLI commands for environment verification, identification, and a demo run.

#### Scenario: Identify from photo paths

- **WHEN** a developer runs `plant-id identify --backend vlm --photos path/to/photo.jpg`
- **THEN** the command SHALL print structured JSON to stdout and persist a run artifact

#### Scenario: Demo command

- **WHEN** a developer runs `plant-id demo --backend vlm` with the demo dataset present under `data/flowers/`
- **THEN** the command SHALL identify the bundled sample image using the configured species catalog

#### Scenario: Quiet mode

- **WHEN** a developer runs identify or demo with `--quiet`
- **THEN** the command SHALL suppress CLI progress output on stderr

### Requirement: Hardware baseline gate

The project SHALL document minimum hardware expectations and require a hardware validation step before committing to the default vision model.

#### Scenario: Documented hardware constraints

- **WHEN** a developer reviews setup documentation
- **THEN** they SHALL find documented minimum RAM and disk requirements for the default 8B-class vision model, including guidance for slower Intel hardware

### Requirement: No external identification services in runtime dependencies

The runtime application SHALL NOT require network access to third-party plant identification APIs. Backend `vlm` SHALL remain usable offline aside from localhost Ollama. Backend `vlm-cloud` SHALL require network access to the user-configured inference endpoint.

#### Scenario: Runtime works offline aside from Ollama

- **WHEN** a developer runs identify or demo commands with `--backend vlm` and network disabled except localhost Ollama
- **THEN** identification SHALL complete without calling external plant identification APIs

#### Scenario: Cloud backend requires configured endpoint

- **WHEN** a developer runs identify or eval with `--backend vlm-cloud`
- **THEN** documentation SHALL state that network access to the configured base URL and a valid `PLANT_ID_VLM_CLOUD_API_KEY` are required

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

### Requirement: Oxford 102 eval dataset documentation

The project SHALL document how to obtain and lay out Oxford 102 Flowers files for eval commands.

#### Scenario: Dataset download instructions

- **WHEN** a developer reads setup or eval documentation
- **THEN** they SHALL find the Oxford 102 download URL and the expected layout under `data/flowers/` (`jpg/`, `imagelabels.mat`, `setid.mat`)

#### Scenario: Test split size documented

- **WHEN** a developer reads eval documentation
- **THEN** they SHALL find that the Oxford 102 test split contains approximately 6,149 images and that profile `full` is a long-running benchmark

#### Scenario: Eval without dataset

- **WHEN** Oxford 102 files are not present
- **THEN** documentation SHALL state that unit tests skip dataset-dependent cases and full eval commands require the download

### Requirement: Eval profiles and improvement loop documentation

The project SHALL document named eval profiles and the eval-to-Opik diagnosis workflow.

#### Scenario: Profile table documented

- **WHEN** a developer reads eval documentation
- **THEN** they SHALL find profiles `smoke` (4 images), `quick` (8 images, default), and `full` (all test images) with expected runtime guidance for default `qwen3-vl:2b`

#### Scenario: Profile manifest documented

- **WHEN** a developer reads eval documentation
- **THEN** they SHALL find that smoke and quick use `eval/profiles/quick.yaml`, that each row lists `species` and `image` independently, and that `--profile-manifest` overrides the default file

#### Scenario: Improvement loop documented

- **WHEN** a developer reads eval documentation
- **THEN** they SHALL find the workflow: run eval with `--eval-run-id` → read JSON report failures → inspect linked Opik traces → change one variable → re-run the same profile

### Requirement: Default vision model for eval

The project SHALL document `qwen3-vl:2b` as the default vision model and how to override for comparison.

#### Scenario: Default model documented

- **WHEN** a developer reads setup or eval documentation
- **THEN** they SHALL find that `PLANT_ID_VISION_MODEL` defaults to `qwen3-vl:2b` and that `qwen3-vl:8b` may be used for accuracy comparison

### Requirement: Pl@ntNet eval baseline documentation

The project SHALL document optional Pl@ntNet baseline configuration for eval-only comparison.

#### Scenario: API key documented

- **WHEN** a developer reads eval baseline documentation
- **THEN** they SHALL find the required environment variable name for the Pl@ntNet API key and that the baseline is optional and eval-only

#### Scenario: Runtime boundary stated

- **WHEN** a developer reads Pl@ntNet documentation
- **THEN** it SHALL state that Pl@ntNet is never used by runtime `plant-id identify`

### Requirement: Agent slash commands documented for developers

The project SHALL document agent-agnostic slash commands alongside shell equivalents in developer-facing docs.

#### Scenario: README command index

- **WHEN** a developer reads the main README
- **THEN** they SHALL find a short section listing available agent slash commands, their canonical location under `agent/commands/`, and when to prefer them over typing raw `uv run` commands

#### Scenario: Distinction from OpenSpec commands

- **WHEN** slash command documentation is presented
- **THEN** it SHALL distinguish domain commands (`/eval-run`, `/verify`, etc.) from OpenSpec workflow commands (`/opsx-propose`, `/opsx-apply`, etc.) and SHALL NOT imply that domain commands require a specific agent host

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
