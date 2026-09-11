## Context

See `proposal.md` — Why. The repo has OpenSpec slash commands (currently under `.cursor/commands/opsx-*.md`) and agent guidance in `AGENTS.md`, but common eval/improvement-loop actions still require developers to paste shell snippets or write free-form prompts. New **domain** commands SHALL live in a host-neutral directory so the same prompt works in Cursor, Claude Code, PI, and other agents.

Agent slash commands are markdown prompt templates. They do not execute code themselves — whichever agent host loads them interprets the instructions. Prompt bodies MUST NOT name a specific agent product, IDE, or proprietary feature.

Existing conventions to mirror where applicable:
- Optional YAML frontmatter with neutral keys only (`name`, `description`, `category`) — no host-specific metadata required
- Category `Workflow` for multi-step agent flows; `Development` for verify/identify shortcuts
- Long-running eval runs: background shell + polling until completion (worded generically in prompts)
- Opik: `./scripts/opik.sh`, `PLANT_ID_OPIK_ENABLED=true`, never `opik.configure()` from plant-id

## Goals / Non-Goals

**Goals:**
- Six high-signal domain commands covering verify, identify, demo, eval run, eval triage, and Opik startup
- Single canonical source under `agent/commands/` — one file per command, agent-agnostic prose
- Consistent defaults aligned with `AGENTS.md` and `eval/README.md`
- Clear separation from `/opsx-*` (planning) vs domain commands (day-to-day dev)
- `agent/commands/README.md` explaining how to register commands per host without duplicating prompt text

**Non-Goals:**
- New Python packages, CLI subcommands, or npm dependencies
- Wrapping OpenSpec CLI inside new slash commands
- Replacing Comet `opik-diagnose` / `opik-explain` skills — `/eval-triage` points to them when deep trace analysis is needed
- Commands for classical ML training, RAG, or Pl@ntNet (future phases)
- Maintaining separate prompt copies per agent host

## Decisions

### 1. Canonical location (agent-agnostic)

All domain command prompts live under **`agent/commands/`**:
- `eval-run.md`, `eval-triage.md`, `verify.md`, `opik-up.md`, `identify.md`, `demo.md`
- `README.md` — host wiring notes (how to expose `/eval-run` etc. in each tool)

**Alternatives considered:**
- `.cursor/commands/` only — rejected; ties prompts to Cursor and blocks Claude Code / PI reuse.
- `docs/agent-commands/` — acceptable but `agent/commands/` aligns with `AGENTS.md` and keeps agent assets grouped.

### 2. Host registration (adapters, not forks)

Prompt bodies stay in `agent/commands/`. Host-specific wiring is documented, not embedded in prompts:

| Host | Registration approach (documented in `agent/commands/README.md`) |
|---|---|
| Cursor | Symlink or copy into `.cursor/commands/` (same pattern as existing `/opsx-*`) |
| Claude Code | Register as custom slash commands or skills pointing at repo files |
| PI / others | Paste prompt body or point host config at `agent/commands/<name>.md` |

Implementation MAY add symlinks from `.cursor/commands/` → `../../agent/commands/` for Cursor discoverability, but specs require only the canonical files.

### 3. Command catalog (initial ship set)

| Command | Category | Purpose | Default behavior |
|---|---|---|---|
| `/eval-run` | Workflow | Start Oxford 102 eval | profile `quick`, require/generate `--eval-run-id`, suggest Opik env, background run |
| `/eval-triage` | Workflow | Summarize eval report failures | latest `artifacts/eval/*.json`, improvement-loop next step |
| `/verify` | Development | Post-change quality gate | full AGENTS.md verify sequence |
| `/opik-up` | Development | Local Opik Docker stack | `./scripts/opik.sh up` + env var reminder |
| `/identify` | Development | Ad-hoc photo ID | `--backend vlm`, absolute paths |
| `/demo` | Development | Sample identify | `plant-id demo --backend vlm` |

**Alternatives considered:**
- Single `/eval-improve` combining run + triage — rejected; splitting run (long) from triage (read-only) matches how developers work.
- `/ground-truth` — deferred.
- Prefix all commands `/plant-*` — rejected; shorter names match `/opsx-*` ergonomics.

### 4. Prompt format (host-neutral)

Each file structure:
1. Optional minimal frontmatter (`name`, `description`, `category`) — parsers that ignore frontmatter still work
2. Body: imperative instructions to the agent (shell commands, guardrails, outputs)
3. No mentions of "Cursor", "Claude Code", "PI", MCP product names in the body except where referring to optional Opik MCP tooling generically as "Opik MCP if connected"

**Alternative:** Cursor-only frontmatter (`id`, palette fields) — rejected for canonical files; host adapters may add fields locally if needed without changing canonical source.

### 5. Argument passing

Commands accept optional trailing text (passed as user message continuation by most hosts):
- `/eval-run` → `[profile] [eval-run-id]`; default profile `quick`; generate slug if id omitted
- `/eval-triage` → `[eval-run-id]` optional; else newest report by mtime
- `/identify` → required absolute path(s); ask if missing
- Others: no args

### 6. Long-running eval execution

`/eval-run` instructs the agent to run eval as a **background/long-running process** and poll for completion, then report the artifact path. Wording avoids host-specific tool names (e.g. "background shell with periodic status checks").

### 7. Full profile guardrail

If profile is `full` (~6,149 images), prompt MUST require explicit user confirmation before starting.

### 8. Opik tracing defaults

`/eval-run` instructs agent to check Opik health, offer `/opik-up` if down, and set `PLANT_ID_OPIK_ENABLED=true` for traced runs when the user wants tracing. Does not auto-modify shell profile files.

### 9. Documentation placement

- `AGENTS.md`: **Agent commands** subsection (table: command → one line; pointer to `agent/commands/`)
- `agent/commands/README.md`: canonical location + per-host registration
- `README.md`: short **Agent shortcuts** bullet list linking to AGENTS.md

Avoid duplicating full command bodies in README.

## Pinned versions

No new dependencies. Commands reference existing pinned toolchain:

| Component | Version | Notes |
|---|---|---|
| Python | 3.14.7 | `.python-version` |
| uv | 0.12.10 | `uv run` invocations |
| Default VLM | qwen3-vl:2b | eval runtime guidance in command text |
| Opik UI | local Docker | `scripts/opik.sh`, port 5173 |

## Risks / Trade-offs

- **[Risk] Hosts discover commands differently** → Mitigation: `agent/commands/README.md` with explicit registration steps; canonical single source
- **[Risk] Command prompts drift from AGENTS.md** → Mitigation: `/verify` lists exact commands from AGENTS.md; tasks include cross-check step
- **[Risk] Developers confuse `/opsx-apply` with `/eval-run`** → Mitigation: docs separate planning vs eval workflows
- **[Risk] Agent runs full eval without confirmation** → Mitigation: hard guardrail in `/eval-run` prompt text
- **[Risk] Opik MCP vs SDK availability varies** → Mitigation: `/eval-triage` works from JSON alone; Opik steps optional

## Migration Plan

1. Add six files under `agent/commands/` + README
2. Optionally symlink into `.cursor/commands/` for Cursor users (documented, not required by spec)
3. Update `AGENTS.md` and README
4. Rollback: git revert; no runtime migration

## Open Questions

- Add `/ground-truth` in a follow-up once classical-ml eval comparisons need it?
- Should `/eval-run` accept `--plantnet-baseline` flag passthrough now or wait for baseline usage?
