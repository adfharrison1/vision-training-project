## 1. Canonical command files

- [x] 1.1 Create `agent/commands/` and add `eval-run.md` with agent-agnostic prompt for Oxford 102 eval (defaults: profile `quick`, background/long-running execution, full-profile confirmation, Opik env guidance); verify prompt body names no specific agent product
- [x] 1.2 Add `agent/commands/eval-triage.md` for latest or named eval report summarization and improvement-loop next steps; verify prompt references `artifacts/eval/` JSON structure
- [x] 1.3 Add `agent/commands/verify.md` mirroring AGENTS.md verify sequence; verify listed shell commands match AGENTS.md exactly
- [x] 1.4 Add `agent/commands/opik-up.md` using `./scripts/opik.sh up` and `PLANT_ID_OPIK_ENABLED` reminder; verify no `opik.configure()` guidance
- [x] 1.5 Add `agent/commands/identify.md` for `--backend vlm` with absolute photo paths; verify prompt requires path when omitted
- [x] 1.6 Add `agent/commands/demo.md` for `plant-id demo --backend vlm` with sample image prerequisite check; verify all six files use consistent optional frontmatter (`name`, `description`, `category`)

## 2. Host registration and documentation

- [x] 2.1 Add `agent/commands/README.md` documenting canonical location and how to register commands in common agent hosts (copy, symlink, or host config) without duplicating prompt bodies; verify no host is listed as required
- [x] 2.2 Add Agent commands table to `AGENTS.md` (domain vs `/opsx-*`, pointer to `agent/commands/`); verify all six commands listed with one-line descriptions
- [x] 2.3 Add short Agent shortcuts section to `README.md` linking to AGENTS.md; verify documentation does not state that commands work only in one IDE

## 3. Optional host adapters

- [x] 3.1 Add symlinks from `.cursor/commands/` to `../../agent/commands/` for the six domain commands (leave `/opsx-*` unchanged); verify symlinks resolve and canonical files remain the edit target

## 4. Validation

- [x] 4.1 Run `openspec validate agent-dev-commands` and fix any spec errors
- [x] 4.2 Read all command files and confirm zero references to Cursor, Claude Code, PI, or other agent product names in prompt bodies

## 5. Agentic coding

- [x] 5.1 Review whether additional agent rules files are needed beyond AGENTS.md; skip or add only if a gap remains, and note decision in archive summary — **skipped:** AGENTS.md table + `agent/commands/README.md` cover registration; no `.cursor/rules/` additions needed
