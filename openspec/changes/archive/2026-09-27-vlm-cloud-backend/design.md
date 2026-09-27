## Context

See `proposal.md`. Today `Backend` is `vlm` | `classical`; `VlmOllamaIdentificationRepository` owns prompt template, JSON parsing, Ollama chat, thinking-channel retry, and Opik via `call_ollama_chat_traced`. Composition wires backends in `container.py`. Eval defaults to `--backend vlm`. Standing specs previously required runtime VLM to use local Ollama only; this change adds `vlm-cloud` and updates those requirements.

## Goals / Non-Goals

**Goals:**

- Add `VlmCloudIdentificationRepository` using pinned OpenAI SDK against user `base_url`, `PLANT_ID_VLM_CLOUD_API_KEY`, and model id.
- Share closed-set prompt build and `_parse_result` logic between Ollama and cloud repos.
- Extend `Backend` literal and all `--backend` argparse choices; eval default `vlm-cloud`, CLI default `vlm`.
- Backend-scoped Opik spans (identify + LLM child) without Comet cloud telemetry.
- Document Fireworks reference env; Option A API key only in code.
- Eval report inference section (backend, model, vendor, host).

**Non-Goals:**

- Native Anthropic/Bedrock SDKs; users supply compatible gateways.
- Vendor env var fallback chains for API keys.
- Replacing Opik with Fireworks dashboards or MLflow.
- Pl@ntNet runtime wiring (unchanged eval-only).
- Ollama content-retry bug fix (separate work, but cloud path avoids thinking channel).

## Decisions

### 1. Third backend value `vlm-cloud`

**Choice:** `Backend = Literal["vlm", "vlm-cloud", "classical"]`.

**Alternatives:** Sub-flag `--vlm-provider cloud` under `vlm` (rejected — eval/CLI already use backend; clearer metrics).

### 2. OpenAI SDK + BYO base URL

**Choice:** `openai.OpenAI(base_url=settings.vlm_cloud_base_url, api_key=...)`. Chat completions with vision content parts; photos as base64 `data:image/jpeg;base64,...` via Pillow (reuse existing image paths).

**Alternatives:** Raw httpx (more boilerplate); Fireworks-only SDK (rejected — generic cloud goal).

### 3. Shared VLM module

**Choice:** Extract `PROMPT_TEMPLATE`, prompt builder, and parse/validate into `infrastructure/identification/vlm_common.py` (name as implemented). Ollama repo keeps retry/thinking/Ollama client; cloud repo calls shared parse after extracting assistant `content`.

**Alternatives:** Duplicate parse (rejected — drift risk).

### 4. Settings (Option A)

| Setting | Default (example) |
|---------|-------------------|
| `vlm_cloud_api_key` | unset (required for `vlm-cloud`) |
| `vlm_cloud_base_url` | `https://api.fireworks.ai/inference/v1` |
| `vlm_cloud_model` | `accounts/fireworks/models/qwen3-vl-8b-instruct` |
| `vlm_cloud_timeout_seconds` | e.g. `120.0` |
| `vlm_cloud_vendor` | optional, e.g. `fireworks` for traces/reports only |

Env prefix `PLANT_ID_` via existing `Settings`. README shows `export PLANT_ID_VLM_CLOUD_API_KEY="$FIREWORKS_API_KEY"` without code reading `FIREWORKS_API_KEY`.

### 5. Opik mapping

**Choice:** Keep manual spans (mirror Ollama): `identify_trace(..., backend=repo.backend_id)`; add `call_openai_chat_traced` (or generalized helper) with `provider` metadata `ollama` vs `openai-compatible`, attach `response.usage`, optional perf fields from response extensions when present. Do not use `opik.configure()` interactively.

**Alternatives:** `track_openai()` wrapper only (risk orphan spans under identify — test nesting if adopted).

Fireworks account metrics / Prometheus: **out of app scope**; document as optional operator tooling.

### 6. verify-env

**Choice:** Extend `plant-id verify-env` with `--backend vlm-cloud` (or document equivalent flag) checking key/base_url/model set; optional lightweight API reachability. Default path unchanged (Ollama).

### 7. Eval report shape

Add top-level or nested `inference` object: `backend`, `model`, `prompt_version`, optional `cloud_vendor`, `cloud_base_url_host`. Keep existing `backend_id` per observation if already present.

### 8. Future transport port (document only)

If non–OpenAI-compatible providers are needed later, introduce a small `CloudChatClient` protocol; v1 implements one OpenAI-compatible class inside infrastructure.

## Pinned versions (verified 2026-09-27)

| Component | Version | Notes |
|-----------|---------|--------|
| Python | 3.14.7 | existing pin |
| openai (new) | 3.19.2 | PyPI stable; OpenAI-compatible client for Fireworks |
| ollama | 0.6.2 | unchanged |
| httpx | 0.28.1 | transitive via openai; already in project |

Run `uv add openai==3.19.2` during implementation and refresh `uv.lock`.

## Risks / Trade-offs

- **[Risk] Token/context limits on serverless cloud model** → Mitigation: document closed-set prompt size; fail clearly on API 4xx; compare eval cost vs local.
- **[Risk] Cloud vs local model mismatch (2b Ollama vs 8B cloud)** → Mitigation: report records model/backend; do not interpret cross-backend eval as pure prompt wins.
- **[Risk] API keys in artifacts** → Mitigation: redact in raw persistence; never log Bearer tokens.
- **[Risk] Network flakiness** → Mitigation: configurable timeout; clear errors; eval partial reports unchanged.
- **[Trade-off] Eval default requires cloud config** → Mitigation: docs + verify-env cloud mode; one-flag `--backend vlm` escape hatch.

## Migration Plan

1. Ship code + docs; update `AGENTS.md` and `openspec/config.yaml` context on archive.
2. Developers running eval set `PLANT_ID_VLM_CLOUD_*` (Fireworks example in README).
3. Interactive identify unchanged default (`vlm`); no migration for demo workflows.
4. Rollback: use `--backend vlm` on eval or revert change.

## Open Questions

None blocking implementation — context window limits for specific providers are validated empirically on first cloud eval smoke run.
