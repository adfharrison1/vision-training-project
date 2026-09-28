# agent-dev-commands Specification

## Purpose

Provide repeatable, agent-agnostic slash-command prompts that encode common plant-id developer workflows so any coding agent can run the right shell commands, read the right artifacts, and follow project conventions without copying from scattered docs or depending on a specific agent product.

## Requirements

### Requirement: Canonical agent command files

The project SHALL ship domain slash-command prompts under `agent/commands/` as the single canonical source, distinct from OpenSpec `/opsx-*` planning commands.

#### Scenario: Command file layout

- **WHEN** a developer lists `agent/commands/`
- **THEN** they SHALL find one markdown file per domain command (`eval-run.md`, `eval-triage.md`, `verify.md`, `opik-up.md`, `identify.md`, `demo.md`) containing agent-executable instructions

#### Scenario: Agent-agnostic prompt bodies

- **WHEN** a developer reads any file under `agent/commands/`
- **THEN** the prompt body SHALL NOT require or reference a specific agent host, IDE, or proprietary slash-command system by name

#### Scenario: No runtime coupling

- **WHEN** agent commands are added or updated
- **THEN** runtime Python packages under `src/plant_id/` SHALL NOT import or depend on `agent/` assets

### Requirement: Host registration documentation

The project SHALL document how to register canonical commands in common agent hosts without duplicating prompt content.

#### Scenario: Registration README

- **WHEN** a developer reads `agent/commands/README.md`
- **THEN** they SHALL find instructions to expose the six domain commands in their agent host (e.g. copy, symlink, or host config pointing at `agent/commands/*.md`)

#### Scenario: Single source of truth

- **WHEN** a command prompt is updated
- **THEN** the change SHALL be made only in `agent/commands/` unless a host adapter adds host-specific metadata locally without altering the canonical instructions

### Requirement: Eval run command

The project SHALL provide a `/eval-run` slash command that starts an Oxford 102 eval with project defaults.

#### Scenario: Default quick eval

- **WHEN** a developer invokes `/eval-run` without arguments
- **THEN** the agent SHALL obtain a non-empty `--run-purpose` from the developer before starting, prompt for or generate an `--eval-run-id`, use profile `quick`, enable Opik tracing guidance when Opik is reachable, verify `data/flowers/` prerequisites, and run `uv run python -m eval.run_oxford102 --run-purpose "<purpose>"` as a background/long-running process with periodic status checks until completion

#### Scenario: Profile override

- **WHEN** a developer invokes `/eval-run smoke` or `/eval-run quick my-run-id`
- **THEN** the agent SHALL map the argument(s) to `--profile` and `--eval-run-id` accordingly and SHALL refuse profile `full` without explicit confirmation because of runtime cost

#### Scenario: Missing dataset

- **WHEN** Oxford 102 files are absent
- **THEN** the agent SHALL stop before starting the eval and point to README dataset download instructions

### Requirement: Eval triage command

The project SHALL provide a `/eval-triage` slash command that summarizes eval failures and suggests diagnostic next steps.

#### Scenario: Latest report default

- **WHEN** a developer invokes `/eval-triage` without arguments
- **THEN** the agent SHALL locate the latest run via `eval_runs/index.json` or the newest `eval_runs/*/eval/report.json`, summarize top-1/top-3 accuracy, list failed observations with ground truth vs prediction, cite `run_purpose`, and cite report paths

#### Scenario: Named run

- **WHEN** a developer invokes `/eval-triage prompt-v1-baseline`
- **THEN** the agent SHALL open `eval_runs/<eval_run_id>/eval/report.json` for that slug

#### Scenario: Opik follow-up

- **WHEN** failed observations include Opik `trace_id` values and Opik is available
- **THEN** the agent SHALL recommend inspecting those traces (Opik UI or connected Opik tooling) and SHALL suggest changing one variable before re-running `/eval-run`

### Requirement: Verify command

The project SHALL provide a `/verify` slash command that runs the post-change verification sequence documented for agents.

#### Scenario: Standard verify loop

- **WHEN** a developer invokes `/verify`
- **THEN** the agent SHALL run, in order: `uv sync`, `uv run plant-id verify-env`, `uv run ruff check .`, `uv run lint-imports`, and `uv run pytest` (unit tests), reporting pass/fail for each step

#### Scenario: Verify after code edits

- **WHEN** `/verify` is invoked after implementation work
- **THEN** the agent SHALL NOT skip failing steps silently and SHALL summarize remaining issues with file references

### Requirement: Opik up command

The project SHALL provide an `/opik-up` slash command for local Opik stack management.

#### Scenario: Start Opik

- **WHEN** a developer invokes `/opik-up`
- **THEN** the agent SHALL run `./scripts/opik.sh up`, confirm the UI URL (`http://localhost:5173`), and remind the developer to set `PLANT_ID_OPIK_ENABLED=true` for traced runs

#### Scenario: Opik already running

- **WHEN** Opik containers are already healthy
- **THEN** the agent SHALL report status without failing the workflow

### Requirement: Identify command

The project SHALL provide an `/identify` slash command for ad-hoc VLM identification.

#### Scenario: Single photo

- **WHEN** a developer invokes `/identify` with an absolute photo path
- **THEN** the agent SHALL run `uv run plant-id identify --backend vlm --photos <path>` and summarize top predictions from stdout or the saved artifact

#### Scenario: Missing path

- **WHEN** no photo path is provided
- **THEN** the agent SHALL ask for an absolute path before running identify

### Requirement: Demo command

The project SHALL provide a `/demo` slash command for the bundled sample identify path.

#### Scenario: Demo run

- **WHEN** a developer invokes `/demo`
- **THEN** the agent SHALL verify the sample image exists under `data/flowers/jpg/image_00001.jpg` (or document if missing) and run `uv run plant-id demo --backend vlm`

### Requirement: Command catalog documentation

Agent-facing documentation SHALL list domain slash commands separately from OpenSpec commands.

#### Scenario: AGENTS.md index

- **WHEN** a developer reads `AGENTS.md`
- **THEN** they SHALL find a concise table or list of `/eval-run`, `/eval-triage`, `/verify`, `/opik-up`, `/identify`, and `/demo` with one-line purpose each and a pointer to `agent/commands/`
