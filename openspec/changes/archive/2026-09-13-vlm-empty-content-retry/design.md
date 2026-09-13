## Context

`VlmOllamaIdentificationRepository` calls Ollama once, then `_extract_message_content`:

1. Use `message.content` if non-empty  
2. Else if `thinking` starts with `{` or `[`, use `thinking`  
3. Else empty → `IdentificationError`

On `mixed16-v3-no-think`, `image_03641` hit (2): JSON in `thinking`, empty `content` — identification **succeeded** but via a hidden fallback. The user asked whether we should **reprompt** instead of only accepting that layout.

**Answer for implementers:** yes, it is literally “check response → optionally one more `client.chat()` with an extra instruction” — not a separate agent, not RAG, not LoRA. It is **control-flow in the VLM repo** around the existing chat call.

## Goals / Non-Goals

**Goals:**

- Make channel misplacement **visible** (retry attempted, logged in raw + Opik span metadata if cheap)
- Nudge the model to put JSON in `content` on a second try
- Improve recovery for **wholly empty** first responses where retry may help (e.g. transient `length` with think on — optional gate in design below)
- Keep **max one retry**, default on, env-disable for A/B

**Non-goals:**

- Correct wrong species after JSON parses
- New prompt versions or catalog-specific rules
- Unlimited retries

## Decision: retry + fallback (not reject-only)

| Approach | Pros | Cons |
|---|---|---|
| **Reject only** (no thinking fallback) | Forces clean channel | Regresses 03641-style parses; still wrong label |
| **Fallback only** (today) | Simple, works | Opaque; no chance to fix channel |
| **Retry then fallback** (chosen) | Teaches runtime pattern; safe | 2× latency on edge cases |

Flow:

```text
1st chat
  → content has JSON?  → parse → done
  → thinking has JSON?  → retry once with corrective suffix
       → 2nd content has JSON? → parse → done
       → else thinking JSON? → parse fallback → done
       → else → IdentificationError
  → wholly empty / prose thinking?
       → optional: retry once if enabled (same suffix)
       → else → IdentificationError
```

**Corrective suffix** (fixed string in code, not prompt template version):

```text
Your previous response had empty content. Return ONLY the JSON object in the
message content field (not in thinking). Same schema as before.
```

Same images, same base prompt body, same `format: json`, same `think` setting unless design explicitly forces `think=false` on retry only when first call used `think=true` and failed with `done_reason=length` — **defer** that sub-gate to implementation task; v1 can use identical request payload + suffix only.

## Detection helpers

Add private methods on the repo (or small module in same file):

- `_extract_message_content(response)` — unchanged contract  
- `_thinking_has_parseable_predictions(text) -> bool` — strip, check starts with `{`, `json.loads`, has non-empty `predictions` list  
- `_needs_content_channel_retry(response) -> bool` — empty content AND thinking has parseable predictions JSON  
- `_needs_empty_response_retry(response) -> bool` — empty content AND NOT thinking JSON AND (optional) `done_reason == "length"` or both fields empty  

Retry if `_needs_content_channel_retry` OR (setting enabled AND `_needs_empty_response_retry`).

## Settings

```python
ollama_content_retry_enabled: bool = True  # PLANT_ID_OLLAMA_CONTENT_RETRY_ENABLED
ollama_content_retry_max: int = 1  # fixed at 1 in v1; field documents intent
```

No CLI flag in v1 unless tasks add `--no-content-retry` on identify — optional stretch.

## Raw artifact shape

Extend `raw` dict:

```json
{
  "request": { ... },
  "response": { ... },
  "retry": {
    "attempted": true,
    "reason": "json_in_thinking",
    "request_suffix": "...",
    "response": { ... }
  }
}
```

Omit `retry` key when not attempted.

## Opik

If retry occurs, add span metadata on identify span: `content_retry: true`, `content_retry_reason: json_in_thinking`. No new trace types.

## Testing

Unit tests with mocked `Client.chat`:

- First response: empty content + thinking JSON → **two** chat calls; second returns content JSON → result from second  
- First response: empty content + thinking JSON → second still bad → **fallback** to first thinking JSON → success  
- First response: content JSON → **one** chat call  
- Retry disabled via settings → one call, fallback only  

## Risks

- **Latency:** ~2× on affected images (~2–3 min each on 2b) — acceptable for learning; document  
- **Wrong label unchanged:** retry may still return canterbury bells — eval metric unchanged; lesson is infrastructure not accuracy  
- **Double Opik spans:** single identify span wrapping both calls preferred  

## Migration

Default retry enabled; disable with env for comparing to pure fallback. No report schema change.

## Pinned versions

No new dependencies. Same Ollama / qwen3-vl pins as project.
