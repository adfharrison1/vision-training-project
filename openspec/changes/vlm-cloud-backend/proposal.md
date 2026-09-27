## Why

Local Ollama vision inference on developer hardware is too slow for Oxford 102 eval and prompt-iteration loops (multi-minute per image). The project still needs the same closed-set `IdentificationRepository` contract and metrics, but with an optional **hosted VLM** path that developers configure via their own OpenAI-compatible endpoint (Fireworks by default in docs).

## What Changes

- Add a third runtime backend **`vlm-cloud`**: `VlmCloudIdentificationRepository` using the **OpenAI Python SDK** against user-configured `base_url`, API key, and model id.
- Keep **`vlm`** (local Ollama) as the default for `plant-id identify` and `plant-id demo`.
- Change **`run_oxford102`** default backend to **`vlm-cloud`**; retain `--backend vlm` for local parity runs.
- Introduce **`PLANT_ID_VLM_CLOUD_*`** settings with **Option A** auth: canonical **`PLANT_ID_VLM_CLOUD_API_KEY` only** (README may show exporting from vendor env vars; no fallback chain in code).
- Extract shared closed-set prompt build + JSON parse/validate used by Ollama and cloud repos.
- Extend composition `Backend` type and `--backend` choices on CLI and eval runner.
- Backend-scoped **`verify-env`** for cloud configuration (optional flag or subcommand pattern).
- Map Opik LLM spans to the **active backend** (`vlm` vs `vlm-cloud`); attach OpenAI `usage` and provider perf metadata when present.
- Record inference metadata in eval reports (backend id, model, optional vendor label, base URL host only).
- **Policy pivot (spec updates):** runtime may call **user-configured hosted VLM endpoints** via `vlm-cloud`; **Pl@ntNet and other third-party plant ID APIs remain eval-only** and MUST NOT implement `IdentificationRepository`.

## Capabilities

### New Capabilities

- `vlm-cloud-inference`: Hosted OpenAI-compatible VLM identification repository, settings, multi-photo requests, structured output parity with local VLM, and isolation from plant-ID SaaS APIs.

### Modified Capabilities

- `application-architecture`: Replace “runtime local-only VLM” with swappable local vs cloud VLM repos; add `vlm-cloud` composition wiring; keep eval adapter separation.
- `local-vlm-inference`: Scope requirements to **Ollama-only** (rename/clarify scenarios); remove requirement that runtime VLM talks only to Ollama.
- `local-dev-environment`: Document cloud env vars, network requirement for `vlm-cloud`, verify-env for cloud; clarify offline identify still works with `vlm`.
- `local-llm-observability`: Traces for both Ollama and cloud LLM calls; backend-aware span metadata; still self-hosted Opik only.
- `evaluation-metrics`: Eval runner default backend `vlm-cloud`; report fields for cloud inference metadata.

## Non-goals

- Native Anthropic, Bedrock, or other non–OpenAI-compatible SDKs (users may supply a compatible gateway URL).
- Vendor-specific code paths beyond optional `PLANT_ID_VLM_CLOUD_VENDOR` label for traces/reports.
- Replacing self-hosted Opik with Fireworks account metrics or Comet cloud telemetry.
- Changing Pl@ntNet baseline behaviour (remains optional eval comparison only).
- Auto-mapping `FIREWORKS_API_KEY` / `OPENAI_API_KEY` in application settings.
- Parallel eval sharding redesign (separate change).

## Depends on

- `uk-plant-id-poc` — layered architecture and `IdentificationRepository`.
- `eval-dataset-baseline` — Oxford 102 eval runner and report schema.
- `local-opik-observability` — infrastructure tracing patterns to extend.

## Decision gates (resolved)

- Backend name: **`vlm-cloud`** (not vendor-specific).
- Transport: **OpenAI SDK** + user `base_url` / API key / model.
- Eval default backend: **`vlm-cloud`**; interactive CLI default: **`vlm`**.
- API key: **`PLANT_ID_VLM_CLOUD_API_KEY` only** (Option A).
- Documented reference preset: Fireworks **`accounts/fireworks/models/qwen3-vl-8b-instruct`**.

## Impact

- **Code:** `interfaces/composition/container.py`, CLI `main.py`, `eval/run_oxford102.py`, new `vlm_cloud.py` (+ shared VLM module), `settings.py`, `opik_tracing.py`, `environment.py` or cloud verify helper, unit tests, `AGENTS.md`, README, `.env.example`.
- **Dependencies:** Pin `openai` Python package in `pyproject.toml` / `uv.lock`.
- **Specs:** Policy shift away from “no cloud LLM at runtime”; observability and Pl@ntNet eval boundaries unchanged in intent.
