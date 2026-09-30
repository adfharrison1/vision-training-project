# Agent slash commands

Canonical prompt templates for common plant-id developer workflows. Edit files here only — do not maintain separate copies per agent host.

| Command | File | Purpose |
|---|---|---|
| `/eval-run` | [eval-run.md](eval-run.md) | Start Oxford 102 eval (default: `quick` profile) |
| `/eval-triage` | [eval-triage.md](eval-triage.md) | Summarize eval failures and next steps |
| `/eval-debug` | [eval-debug.md](eval-debug.md) | Post-mortem parse vs misclass failures using forensics JSON |
| `/retrieval-run` | [retrieval-run.md](retrieval-run.md) | Start retrieval-only eval |
| `/retrieval-triage` | [retrieval-triage.md](retrieval-triage.md) | Summarize retrieval misses |
| `/retrieval-debug` | [retrieval-debug.md](retrieval-debug.md) | Inspect retrieval failure forensics |
| `/verify` | [verify.md](verify.md) | Post-change verify loop |
| `/opik-up` | [opik-up.md](opik-up.md) | Start local Opik Docker stack |
| `/identify` | [identify.md](identify.md) | Ad-hoc VLM identify on photo path(s) |
| `/demo` | [demo.md](demo.md) | Bundled sample identify |

OpenSpec planning commands (`/opsx-propose`, `/opsx-apply`, etc.) live separately under `.cursor/commands/` and are not duplicated here.

## Registering commands in your agent host

No single host is required. Point your tool at these files or copy/symlink them into your host's command directory.

**Symlink (recommended when your host reads a project commands folder)**

From the repository root:

```bash
ln -sf ../../agent/commands/eval-run.md .cursor/commands/eval-run.md
ln -sf ../../agent/commands/eval-triage.md .cursor/commands/eval-triage.md
ln -sf ../../agent/commands/eval-debug.md .cursor/commands/eval-debug.md
ln -sf ../../agent/commands/verify.md .cursor/commands/verify.md
ln -sf ../../agent/commands/opik-up.md .cursor/commands/opik-up.md
ln -sf ../../agent/commands/identify.md .cursor/commands/identify.md
ln -sf ../../agent/commands/demo.md .cursor/commands/demo.md
```

Adjust the target directory for your host (e.g. a custom commands folder in your agent config).

**Copy**

Copy the `.md` file contents into your host's slash-command or custom-prompt UI. Re-copy when the canonical file changes, or switch to symlinks/paths to avoid drift.

**Host config**

Some agents accept a file path or pasted prompt body in settings — register each command name (`/eval-run`, etc.) to the corresponding file under `agent/commands/`.

## Prompt format

Each file uses optional YAML frontmatter (`name`, `description`, `category`) followed by agent instructions. Prompt bodies are agent-agnostic: they do not assume a specific IDE or agent product.
