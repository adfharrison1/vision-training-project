## Why

With `think=false`, qwen3-vl sometimes returns valid identification JSON in the `thinking` field while `message.content` stays empty (e.g. `image_03641` on `mixed16-v3-no-think`). Today we silently recover by parsing JSON from `thinking` when it starts with `{`, which hides a malformed channel layout and does not attempt to fix upstream behaviour. With `think=true`, empty `content` and non-JSON thinking loops still produce hard failures (`done_reason: length`). A small, bounded retry gives a runtime tuning lever before LoRA or classical ML — without per-species prompt rules.

## What Changes

- Add **detection** for “empty content but parseable JSON in `thinking`” and for **wholly empty / unparseable** model output after the first Ollama chat call.
- Add **one optional retry** per observation: resend the same images + prompt with a **short corrective user-message suffix** (not a new prompt version) asking for JSON in `content` only.
- After retry, **prefer `content`**; if still empty but `thinking` holds valid JSON, **keep today’s fallback extract** so behaviour does not regress on successes.
- Persist retry metadata in the identification artifact `raw` payload (e.g. retry attempted, retry reason, second response snippet or full second response).
- Add settings for enable/default and document in README / AGENTS.md (default: retry enabled, max 1 attempt).

## Depends on

- `uk-plant-id-poc` — VLM repository, structured JSON output, artifact persistence
- Recent `PLANT_ID_OLLAMA_THINK` / `--think` wiring — retry policy applies regardless of think flag unless design gates otherwise

## Decision gates (resolved in design.md)

- Retry is **infrastructure-only** (no prompt version bump); corrective text is a fixed runtime suffix.
- **Max one retry** per observation; no loops.
- Retry targets **channel / empty output** recovery, **not** wrong species labels.
- Default **on** for learning visibility; configurable via env if needed.

## Capabilities

### New Capabilities

_(none)_

### Modified Capabilities

- `local-vlm-inference`: malformed Ollama response detection and bounded retry before parse/fail

## Non-goals

- Fixing taxonomic confusion (e.g. primula vs canterbury bells) via retry or prompt hacks
- Multiple retries, exponential backoff, or Pl@ntNet-style retry policies
- Changing `prompt_version` or closed-set catalog rules per retry
- LoRA, classical ML, or RAG
- Forcing retry when first response already has JSON in `content` (happy path unchanged)

## Impact

- `src/plant_id/infrastructure/identification/vlm_ollama.py` — detect, retry, fallback, raw metadata
- `src/plant_id/infrastructure/config/settings.py` — optional `ollama_empty_content_retry` (or similar)
- `tests/unit/infrastructure/test_vlm_ollama.py` — mock client call count and parse paths
- `README.md`, `AGENTS.md` — brief retry behaviour note
- Eval reports unchanged in shape; artifacts may include retry fields under `raw`
