## 1. Local Opik stack and settings

- [ ] 1.1 Document self-hosted Opik Docker setup in README (local URL, no cloud account); verify UI reachable at default port
- [ ] 1.2 Add `opik_enabled`, `opik_base_url`, `opik_project_name` to `Settings`; default tracing off; verify load from env
- [ ] 1.3 Pin `opik` Python SDK in `pyproject.toml` / `uv.lock`; record version in `design.md`

## 2. Infrastructure tracing adapter

- [ ] 2.1 Add `infrastructure/observability/` module with Opik span helpers for Ollama chat (no-op when disabled)
- [ ] 2.2 Instrument `VlmOllamaIdentificationRepository.identify` — record model, tokens, durations, thinking when present
- [ ] 2.3 Verify import-linter: domain, application, interfaces CLI have no Opik imports

## 3. Verification and docs

- [ ] 3.1 Unit test: tracing disabled — identify path unchanged (mock Ollama, no Opik network)
- [ ] 3.2 Manual smoke: Opik running + `PLANT_ID_OPIK_ENABLED=true` + `plant-id identify` — trace visible in local Opik UI
- [ ] 3.3 Update `AGENTS.md` with observability toggle, local-only policy, and verify commands
- [ ] 3.4 Confirm identification still works when Opik is enabled but server is stopped (graceful degradation)
