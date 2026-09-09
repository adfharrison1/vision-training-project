## Why

Developers need **real-time visibility** into Ollama VLM calls (latency, tokens, prompts, responses, thinking text) while iterating on identification — beyond CLI stage spinners and post-hoc JSON artifacts. This supports prompt tuning and prepares for the Oxford 102 eval change.

**Decision (2026-09-09):** use **Opik self-hosted** (not Torrix, not OpenLLM Monitor). Observability data MUST remain **local-only** — no Comet cloud, no third-party trace backends.

## Depends on

- `uk-plant-id-poc` — VLM repository, `ApplicationEvents`, artifacts, layered architecture

## What Changes

- Self-hosted Opik stack (Docker) documented for local dev
- Opik Python SDK integration in **infrastructure** tracing Ollama `chat` calls
- Settings to enable/disable tracing and point at local Opik URL
- README / AGENTS.md observability section
- Does **not** replace `ApplicationEvents` CLI progress or file artifacts

## Runtime boundary (non-negotiable)

- Traces, prompts, and responses MUST be stored on the developer machine (self-hosted Opik)
- MUST NOT send observability data to Comet cloud or other external telemetry services
- MUST NOT change runtime identification behaviour when tracing is disabled
- Opik is **not** an identification backend — it does not implement `IdentificationRepository`

## Non-goals

- Torrix, OpenLLM Monitor, or other observability products
- Comet cloud / SaaS Opik
- Replacing `artifacts/*.json` persistence
- Rich terminal UI changes
- Eval runner metrics (deferred to `eval-dataset-baseline`; traces may be reused later)

## Impact

- New dev dependency: `opik` (pinned)
- Optional Docker service for Opik UI (documented, not required for unit tests)
- `VlmOllamaIdentificationRepository` gains tracing hooks in infrastructure layer
