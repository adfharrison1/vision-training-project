## ADDED Requirements

### Requirement: Local Qdrant development stack

The project SHALL document a local Qdrant stack (Docker Compose and helper script) and environment variables for URL and collection name, with a documented flow: build retrieval index artifacts, start Qdrant, seed collections.

#### Scenario: Developer bootstrap

- **WHEN** a developer follows README Qdrant setup
- **THEN** they SHALL be able to seed the vector store from project sheets and **OpenRouter-built** embedding artifacts without manual UI steps

#### Scenario: OpenRouter key for index build

- **WHEN** a developer runs the documented index build for prototype embeddings
- **THEN** `PLANT_ID_VLM_OPENROUTER_API_KEY` SHALL be required

### Requirement: Retrieval verify hook

When retrieval dependencies are configured, verify-env or a dedicated verify subcommand SHALL check Qdrant reachability and that the configured collection exists or document seed required.

#### Scenario: Qdrant not running

- **WHEN** verify runs and Qdrant is unreachable
- **THEN** the command SHALL exit non-zero with actionable guidance referencing the Qdrant helper script

### Requirement: README accuracy for RAG and retrieval setup

When this change introduces or modifies species sheets, Qdrant, retrieval eval, or RAG identify workflows, the project SHALL update all relevant README files in the same delivery increment so documented commands, environment variables, and directory layouts match behavior.

#### Scenario: Developer follows root README

- **WHEN** a developer sets up Qdrant, builds the retrieval index, or enables RAG identify using root README instructions
- **THEN** the documented steps SHALL succeed on a clean clone that satisfies stated prerequisites (Docker, dataset, API keys where noted)

#### Scenario: Eval maintainer follows eval README

- **WHEN** a maintainer runs retrieval eval or sheet synthesis per `eval/README.md`
- **THEN** CLI flags, output paths under `eval_runs/`, and triage pointers SHALL match the implemented eval harness
