## ADDED Requirements

### Requirement: Eval debug command

The project SHALL provide a `/eval-debug` slash command for structured post-mortem of eval failures using run manifests and forensics JSON.

#### Scenario: Debug by run id

- **WHEN** a developer invokes `/eval-debug` with an `eval_run_id`
- **THEN** the agent SHALL read `eval_runs/index.json` and `eval_runs/<id>/manifest.json`, open `eval_runs/<id>/eval/report.json`, classify parse failures vs misclassifications, and cite forensics files under `eval_runs/<id>/eval/failures/` when present

#### Scenario: Latest run default

- **WHEN** a developer invokes `/eval-debug` without arguments
- **THEN** the agent SHALL select the newest entry from `eval_runs/index.json` (or newest report by mtime if index is missing) and follow the same analysis steps

## MODIFIED Requirements

### Requirement: Eval run command

The project SHALL provide a `/eval-run` slash command that starts an Oxford 102 eval with project defaults.

#### Scenario: Default quick eval

- **WHEN** a developer invokes `/eval-run` without arguments
- **THEN** the agent SHALL obtain a non-empty `run_purpose` from the developer before starting, generate or confirm `--eval-run-id`, use profile `quick`, enable Opik tracing guidance when Opik is reachable, verify `data/flowers/` prerequisites, and run `uv run python -m eval.run_oxford102 --run-purpose "<purpose>"` as a background/long-running process with periodic status checks until completion

#### Scenario: Profile override

- **WHEN** a developer invokes `/eval-run smoke` or `/eval-run quick my-run-id`
- **THEN** the agent SHALL map the argument(s) to `--profile` and `--eval-run-id` accordingly, SHALL still require `run_purpose`, and SHALL refuse profile `full` without explicit confirmation because of runtime cost

#### Scenario: Missing dataset

- **WHEN** Oxford 102 files are absent
- **THEN** the agent SHALL stop before starting the eval and point to README dataset download instructions

### Requirement: Eval triage command

The project SHALL provide a `/eval-triage` slash command that summarizes eval failures and suggests diagnostic next steps.

#### Scenario: Latest report default

- **WHEN** a developer invokes `/eval-triage` without arguments
- **THEN** the agent SHALL locate the latest run via `eval_runs/index.json` or the newest `eval_runs/*/eval/report.json`, summarize split top-1/top-3 accuracy, list failed observations with ground truth vs prediction, cite `run_purpose` from manifest or report, and cite report paths

#### Scenario: Named run

- **WHEN** a developer invokes `/eval-triage prompt-v1-baseline`
- **THEN** the agent SHALL open `eval_runs/<eval_run_id>/eval/report.json` for that slug

#### Scenario: Opik follow-up

- **WHEN** failed observations include Opik `trace_id` values and Opik is available
- **THEN** the agent SHALL recommend inspecting those traces (Opik UI or connected Opik tooling), SHALL suggest `/eval-debug` for parse failures, and SHALL suggest changing one variable before re-running `/eval-run`

### Requirement: Command catalog documentation

Agent-facing documentation SHALL list domain slash commands separately from OpenSpec commands.

#### Scenario: AGENTS.md index

- **WHEN** a developer reads `AGENTS.md`
- **THEN** they SHALL find a concise table or list including `/eval-run`, `/eval-triage`, `/eval-debug`, `/verify`, `/opik-up`, `/identify`, and `/demo` with one-line purpose each and a pointer to `agent/commands/`

### Requirement: Canonical agent command files

The project SHALL ship domain slash-command prompts under `agent/commands/` as the single canonical source, distinct from OpenSpec `/opsx-*` planning commands.

#### Scenario: Command file layout

- **WHEN** a developer lists `agent/commands/`
- **THEN** they SHALL find one markdown file per domain command including `eval-run.md`, `eval-triage.md`, `eval-debug.md`, `verify.md`, `opik-up.md`, `identify.md`, and `demo.md` containing agent-executable instructions

#### Scenario: Agent-agnostic prompt bodies

- **WHEN** a developer reads any file under `agent/commands/`
- **THEN** the prompt body SHALL NOT require or reference a specific agent host, IDE, or proprietary slash-command system by name

#### Scenario: No runtime coupling

- **WHEN** agent commands are added or updated
- **THEN** runtime Python packages under `src/plant_id/` SHALL NOT import or depend on `agent/` assets
