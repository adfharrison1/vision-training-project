## 1. Layered scaffold and dev environment

- [x] 1.1 Create `pyproject.toml`, `.python-version`, `uv.lock`, layer directories, and `resources/species_catalog/`; verify `uv sync` succeeds
- [x] 1.2 Add ruff 0.16.6, pytest 9.1.1, and import-linter 2.13; verify `uv run ruff check .` passes
- [x] 1.3 Write README: layers diagram, uv/Ollama setup, Oxford 102 download (optional for eval), bundled species catalog, `--backend vlm`, runtime-local-only policy
- [x] 1.4 Implement `Settings` in `infrastructure/config/` (including `species_catalog_path`, `uncertainty_threshold`, model tag); verify load from env/defaults
- [x] 1.5 Implement `plant-id verify-env` in interfaces CLI; verify Ollama 0.33.3+ and model tag
- [x] 1.6 **Hardware spike (manual, run when reaching this task):** install Ollama, pull candidate `qwen3-vl:8b`, run documented spike on one Oxford 102 sample (latency/RAM/quality); lock or document fallback model in settings/README before task 4.2
- [x] 1.7 Add `eval/README.md` (eval-only; Pl@ntNet optional later; not a repository implementation)

## 2. Domain layer

- [x] 2.1 Implement Pydantic domain models: `Observation`, `Prediction`, `ObservationResult`; verify 1–3 photo validation at construction
- [x] 2.2 Define `IdentificationRepository`, `ArtifactRepository`, `SpeciesCatalogRepository` Protocols in `domain/repositories.py`
- [x] 2.3 Add domain exceptions; verify unit tests for model validation

## 3. Application layer

- [x] 3.1 Implement `IdentifyPlantUseCase` depending only on `IdentificationRepository` and `ArtifactRepository` (not species catalog); verify unit test with fake repositories (no Ollama)
- [x] 3.2 Use case delegates identify + persist; verify fake repo call order

## 4. Infrastructure — VLM repository

- [x] 4.1 Add bundled `resources/species_catalog/default.txt` and implement `FileSpeciesCatalog` implementing `SpeciesCatalogRepository`; verify default catalog loads (102 labels today)
- [x] 4.2 Implement `VlmOllamaIdentificationRepository` with injected `SpeciesCatalogRepository` (ollama 0.6.2, prompt v1, structured JSON, temperature 0); **requires task 1.6 spike complete**; verify integration on sample image
- [x] 4.3 Prompt v1 requests per-prediction confidence; map to `ObservationResult.uncertain` via `Settings.uncertainty_threshold` (reassess better options during this task if model confidence is unreliable)
- [x] 4.4 Support 1–3 images in one Ollama request; verify multi-photo path
- [x] 4.5 Implement `FileArtifactRepository`; verify artifact JSON written
- [x] 4.6 Add `ClassicalMlIdentificationRepository` stub (catalog-injected constructor) raising clear not-implemented; verify `--backend classical` fails gracefully

## 5. Composition and interfaces (thin CLI)

- [x] 5.1 Implement `interfaces/composition/container.py`: build `FileSpeciesCatalog`, inject into identification repo, wire use case; verify `vlm` wiring in unit test
- [x] 5.2 Implement CLI commands: `verify-env`, `identify --backend vlm`, `demo --backend vlm`, `--quiet`; verify end-to-end demo on Oxford 102 sample
- [x] 5.3 CLI MUST NOT contain business logic beyond argument parsing, wiring, and `ApplicationEvents` binding

## 6. Architecture and testing

- [x] 6.1 Add `.importlinter` contracts: domain independence, application independence, thin interfaces; verify `uv run lint-imports` passes
- [x] 6.2 Integration test `@pytest.mark.integration` with live Ollama via VLM repository; skip when unavailable
- [x] 6.3 README documents layer boundaries, repository pattern, catalog injection, and how to add classical backend later

## 7. Agentic coding (end of phase)

- [x] 7.1 Update AGENTS.md/CLAUDE.md with layer rules, repository ports, composition/catalog injection, import-linter, and CLI commands; verify agent can run demo from docs alone
