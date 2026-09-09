## 1. Local Opik stack and settings

- [x] 1.1 Document self-hosted Opik Docker setup in README (local URL, no cloud account); verify UI reachable at default port
- [x] 1.2 Add `opik_enabled`, `opik_base_url`, `opik_project_name` to `Settings`; default tracing off; verify load from env
- [x] 1.3 Pin `opik` Python SDK in `pyproject.toml` / `uv.lock`; record version in `design.md`

## 2. Infrastructure tracing adapter

- [x] 2.1 Add `infrastructure/observability/` module with Opik span helpers for Ollama chat (no-op when disabled)
- [x] 2.2 Instrument `VlmOllamaIdentificationRepository.identify` — record model, tokens, durations, thinking when present
- [x] 2.3 Verify import-linter: domain, application, interfaces CLI have no Opik imports

## 3. Verification and docs

- [x] 3.1 Unit test: tracing disabled — identify path unchanged (mock Ollama, no Opik network)
- [x] 3.2 Manual smoke: Opik running + `PLANT_ID_OPIK_ENABLED=true` + `plant-id identify` — trace visible in local Opik UI
- [x] 3.3 Update `AGENTS.md` with observability toggle, local-only policy, and verify commands
- [x] 3.4 Confirm identification still works when Opik is enabled but server is stopped (graceful degradation)
