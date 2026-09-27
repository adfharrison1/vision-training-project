## 1. Dependencies and settings

- [ ] 1.1 Pin `openai==3.19.2` via `uv add` and verify `uv sync` succeeds
- [ ] 1.2 Add `vlm_cloud_*` fields to `Settings` with Fireworks-oriented defaults and verify `tests/unit/test_settings.py` covers env loading for API key, base URL, model, vendor, and timeout
- [ ] 1.3 Document Option A API key (`PLANT_ID_VLM_CLOUD_API_KEY` only) in `.env.example` and verify no code reads vendor key env vars

## 2. Shared VLM logic

- [ ] 2.1 Extract shared prompt template, prompt builder, and JSON parse/validate from `vlm_ollama.py` into `vlm_common.py` and verify existing `tests/unit/infrastructure/test_vlm_ollama.py` parse tests still pass unchanged
- [ ] 2.2 Refactor `VlmOllamaIdentificationRepository` to use shared module without behaviour change and verify Ollama unit tests pass

## 3. Cloud VLM repository

- [ ] 3.1 Implement `VlmCloudIdentificationRepository` (OpenAI SDK, base64 images, temperature 0, multi-photo) with injectable client for tests and verify unit tests with mocked completions cover success, API error, and schema failure
- [ ] 3.2 Wire `backend_id` as `vlm-cloud:{model}` and verify artifact `model_tag` uses configured cloud model

## 4. Composition and CLI

- [ ] 4.1 Extend `Backend` to include `vlm-cloud` in `build_identify_use_case` and verify `tests/unit/interfaces/composition/test_container.py` asserts correct repo type
- [ ] 4.2 Add `vlm-cloud` to `plant-id identify` and `demo` `--backend` choices (default remains `vlm`) and verify argparse/help text via unit test or snapshot

## 5. Eval runner

- [ ] 5.1 Change `run_oxford102` default `--backend` to `vlm-cloud` and verify argparse default in unit test
- [ ] 5.2 Extend eval JSON report with inference metadata (backend, model, prompt_version, optional vendor, base URL host) and verify report builder unit test

## 6. Observability

- [ ] 6.1 Add OpenAI-compatible traced chat helper and backend-aware LLM span metadata in `opik_tracing.py` and verify `tests/unit/infrastructure/test_opik_tracing.py` (or new tests) for cloud usage metadata
- [ ] 6.2 Call tracing helpers from cloud repo with `backend_id` on identify span and verify tracing disabled path unchanged

## 7. verify-env and documentation

- [ ] 7.1 Add `--backend vlm-cloud` (or equivalent) to verify-env for required settings and verify unit test for missing API key message
- [ ] 7.2 Update README and `eval/README.md` with Fireworks reference preset, eval default backend, and `--backend vlm` override; verify docs mention Pl@ntNet remains eval-only

## 8. Agent guidance and validation

- [ ] 8.1 Update `AGENTS.md` (backends, env vars, eval defaults, verify commands) and verify `/verify` commands listed remain accurate
- [ ] 8.2 Run `uv run ruff check .`, `uv run lint-imports`, and `uv run pytest` and verify all unit tests pass

## 9. Integration smoke (optional, manual)

- [ ] 9.1 With cloud env configured, run `uv run plant-id identify --backend vlm-cloud --photos <sample>` and verify structured result or clear config error without key in logs
- [ ] 9.2 Run `uv run python -m eval.run_oxford102 --profile smoke --eval-run-id cloud-smoke --backend vlm-cloud` and verify report written under `artifacts/eval/`
