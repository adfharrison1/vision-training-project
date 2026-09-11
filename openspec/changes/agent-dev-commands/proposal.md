## Why

Developers already rely on coding agents for eval iteration, Opik diagnosis, and post-change verification, but those workflows are scattered across `AGENTS.md`, `eval/README.md`, and ad-hoc prompts. The project has OpenSpec slash commands (`/opsx-*`) but no domain-specific commands for the plant-id improvement loop. Standardizing a small, **agent-agnostic** command set reduces copy-paste errors, sets consistent defaults (profiles, tracing, verify steps), and works across agent hosts (Cursor, Claude Code, PI, etc.) without tying prompts to one product.

## What Changes

- Add project agent slash-command prompts under `agent/commands/` as the **canonical, host-neutral** source (markdown prompt templates).
- Document the command catalog and how to register commands in `AGENTS.md`, `agent/commands/README.md`, and README.
- Each command is a prompt template: no new Python CLI, no runtime behavior changes, no external API usage, no references to a specific agent product in command bodies.
- Initial command set (subject to design refinement):
  - **`/eval-run`** — start an Oxford 102 eval with sensible defaults and optional Opik tracing
  - **`/eval-triage`** — read the latest (or named) eval report and summarize failures with next diagnostic steps
  - **`/verify`** — run the post-change verification loop from `AGENTS.md`
  - **`/opik-up`** — start or check local Opik via `scripts/opik.sh`
  - **`/identify`** — identify one or more photos with the VLM backend
  - **`/demo`** — run the bundled demo identify path
- Keep commands concise; delegate deep Opik root-cause work to the existing `opik-diagnose` / `opik-explain` skills via references inside command prompts (no duplicate skill logic).

## Capabilities

### New Capabilities

- `agent-dev-commands`: Agent-agnostic slash-command prompts that encode repeatable workflows for verify, identify, eval runs, eval triage, and local Opik setup.

### Modified Capabilities

- `local-dev-environment`: Document the slash-command catalog, canonical file location, and when to use each command versus raw shell commands.

## Non-goals

- Replacing the `plant-id` CLI or adding new shell entrypoints
- Wrapping or reimplementing OpenSpec `/opsx-*` commands
- Requiring or documenting only one agent host (Cursor, Claude Code, PI, etc.)
- Cloud Opik, Comet cloud, or any external identification API
- Auto-committing, auto-archiving OpenSpec changes, or CI integration
- A command for every possible task — keep the initial set small and high-signal

## Depends on

- `uk-plant-id-poc` — CLI identify/demo/verify-env exists
- `local-opik-observability` — Opik tracing and `scripts/opik.sh`
- `eval-dataset-baseline` — eval runner, profiles, report artifacts
- `eval-profile-manifest` — smoke/quick manifest semantics

## Decision gates (resolve before implementation)

- Final command names and whether eval commands accept inline args (profile, eval-run-id) or prompt interactively when omitted
- Whether `/eval-run` runs in background by default (long-running) or blocks with progress monitoring
- Whether `/opik-up` should also set `PLANT_ID_OPIK_ENABLED=true` guidance or only manage Docker
- Whether to add `/ground-truth` for single-image Oxford checks or fold into `/identify`
- How each supported agent host discovers commands (copy, symlink, or host-specific config) without duplicating prompt bodies

## Impact

- **Files:** `agent/commands/*.md`, `agent/commands/README.md`, `AGENTS.md`, `README.md`
- **Runtime:** none — commands guide the agent only
- **Architecture:** no layer or repository changes; eval/runtime boundaries unchanged
- **Dependencies:** none added
