## Context

The POC records run artifacts to disk and shows CLI pipeline stages via `ApplicationEvents`. Neither gives a **live cross-run dashboard** for Ollama latency, token counts, or prompt/response inspection during development.

Alternatives considered:

| Option | Verdict |
|---|---|
| **Opik (self-hosted)** | **Selected** — Python SDK wraps `ollama.chat`; official Ollama integration; eval-friendly; Docker self-host |
| Torrix | Rejected — proxy-centric; awkward fit for native `ollama` client + vision `images` |
| OpenLLM Monitor | Rejected — Node/MongoDB stack; immature; poor Python integration |

## Architecture

```text
interfaces/cli          ApplicationEvents --> Rich (terminal progress, unchanged)
       |
       v
interfaces/composition  execute_identify (unchanged contract)
       |
       v
infrastructure/vlm      ollama.chat + Opik @track / spans (when enabled)
       |                        |
       v                        v
     Ollama                  Opik (local Docker, :5173)
```

**Layer rules:**

- Tracing code lives under `infrastructure/observability/` only
- Domain and application layers MUST NOT import Opik
- Interfaces MUST NOT import Opik (composition unchanged unless passing settings flag)
- When `Settings.opik_enabled` is false, tracing is a no-op (no network calls)

## Opik self-hosted setup

Run Opik via official Docker Compose (document exact compose file / version at implementation). Default local API base:

```text
http://127.0.0.1:5173/api
```

SDK configuration (local only — no cloud API key):

```text
OPIK_URL_OVERRIDE=http://127.0.0.1:5173/api
OPIK_PROJECT_NAME=plant-id   # or via Settings
```

Verify exact env var names against Opik docs at pin time. **Do not configure `OPIK_API_KEY` for cloud.**

## Instrumentation approach

Wrap the Ollama call path in `VlmOllamaIdentificationRepository.identify`:

1. Outer span: `identify` (observation_id, backend, photo count)
2. Inner span: `ollama.chat` with metadata from response:
   - `eval_duration`, `load_duration`, `prompt_eval_count`, `eval_count`
   - model tag, prompt_version
   - thinking text when present (qwen3-vl)

Use `@opik.track` or `opik.start_as_current_span` per Opik Ollama integration docs. Do not route traffic through a proxy.

## Settings (infrastructure/config)

| Field | Default | Description |
|---|---|---|
| `opik_enabled` | `false` | Enable trace export |
| `opik_base_url` | `http://127.0.0.1:5173/api` | Self-hosted Opik API |
| `opik_project_name` | `plant-id` | Opik project for traces |

Env prefix: `PLANT_ID_OPIK_*` mapped via pydantic-settings.

## Relationship to ApplicationEvents

| Concern | ApplicationEvents | Opik |
|---|---|---|
| Audience | Operator at terminal | Developer in browser UI |
| Scope | Current CLI session | All runs when enabled |
| Content | Stage labels | Full traces, tokens, prompts |
| Layer | Domain port + CLI handler | Infrastructure adapter |

Both may be active simultaneously; they are independent sinks.

## Pinned versions

Verify on implementation date:

| Component | Target |
|---|---|
| opik (Python) | latest stable — pin exact in `pyproject.toml` |
| Opik server (Docker) | pin image tag in docs / compose |

## Open questions (resolve during implementation)

- Exact Opik Docker Compose revision and health-check URL
- Whether eval scripts should opt into tracing in a follow-up task
- Performance impact of tracing on long VLM runs (acceptable for dev; default off in CI)
