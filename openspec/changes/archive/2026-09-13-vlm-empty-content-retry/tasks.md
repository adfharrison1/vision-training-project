## 1. Settings and detection helpers

- [x] 1.1 Add `ollama_content_retry_enabled` (default true) to `Settings`; verify unit test loads env override
- [x] 1.2 Add detection helpers for empty content + JSON-in-thinking and wholly empty response; verify unit tests on helper functions or via repo mocks

## 2. VLM repository retry loop

- [x] 2.1 Implement single-retry loop in `VlmOllamaIdentificationRepository` with fixed corrective suffix on user message; verify mock client receives two calls when first response has JSON only in `thinking`
- [x] 2.2 Preserve thinking-json fallback after failed retry; verify test where second call still empty but first thinking JSON parses
- [x] 2.3 Extend `raw` artifact with optional `retry` block; verify persisted JSON includes retry metadata when attempted
- [x] 2.4 Ensure happy path (JSON in `content` first call) still performs exactly one chat; verify existing test still passes

## 3. Observability

- [x] 3.1 When retry runs, attach `content_retry` / `content_retry_reason` to Opik identify span metadata if Opik enabled; verify unit test on tracing mock

## 4. Documentation

- [x] 4.1 Document retry behaviour and `PLANT_ID_OLLAMA_CONTENT_RETRY_ENABLED` in README and AGENTS.md; verify wording matches max-one-retry semantics

## 5. Manual verification (developer machine)

- [ ] 5.1 With Ollama up, ad-hoc identify on `image_03641.jpg` and confirm artifact shows retry block or single-call success; compare latency vs prior artifact
- [ ] 5.2 Re-run `mixed16` with new `--eval-run-id` and confirm no increase in empty-response errors (wrong-label rate may unchanged)
