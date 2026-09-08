## Purpose

Define a reproducible local development environment for UK plant identification using Python and Ollama on macOS.

## ADDED Requirements

### Requirement: Supported platform and runtime versions

The project SHALL document minimum platform requirements and pinned runtime versions needed to run the identifier locally.

#### Scenario: Developer reads environment prerequisites

- **WHEN** a developer opens the project setup documentation
- **THEN** they SHALL find documented requirements for macOS, Python 3.14.7, Node 24.13.1 (OpenSpec tooling only), Ollama 0.33.3+, and the pinned vision model tag

### Requirement: Pinned dependency versions

The project SHALL pin exact stable versions of Python, development tools, and runtime libraries in project metadata and the lockfile.

#### Scenario: Documented version pins

- **WHEN** a developer opens project setup documentation or `pyproject.toml`
- **THEN** they SHALL find exact pinned versions for Python 3.14.7, uv 0.12.10, ruff 0.16.6, pytest 9.1.1, import-linter 2.13, Pydantic 2.13.5, PyYAML 6.0.3, Pillow 12.3.0, and ollama 0.6.2

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

### Requirement: Hardware baseline gate

The project SHALL document minimum hardware expectations and require a hardware validation step before committing to the default vision model.

#### Scenario: Documented hardware constraints

- **WHEN** a developer reviews setup documentation
- **THEN** they SHALL find documented minimum RAM and disk requirements for the default 8B-class vision model, including guidance for slower Intel hardware

### Requirement: No external identification services in runtime dependencies

The runtime application SHALL NOT require network access to third-party plant identification APIs.

#### Scenario: Runtime works offline aside from Ollama

- **WHEN** a developer runs identify or demo commands with network disabled except localhost Ollama
- **THEN** identification SHALL complete without calling external identification APIs
