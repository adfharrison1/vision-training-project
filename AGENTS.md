# Agent guide — UK Plant Identification

Learning project: identify flowering plants from 1–3 photos using a **local Ollama VLM** by default, or optional **`vlm-cloud`** (OpenAI-compatible hosted inference). Pl@ntNet and similar plant-ID APIs stay eval-only. See `README.md` for setup.

## Quick verify (run after code changes)

```bash
uv sync
uv run plant-id verify-env          # Ollama + qwen3-vl:2b (backend vlm)
uv run plant-id verify-env --backend vlm-cloud  # cloud env vars only
uv run ruff check .
uv run lint-imports
uv run pytest                       # unit; skips integration without Ollama/sample
```

**Demo** (optional; needs `data/flowers/jpg/image_00001.jpg`):

```bash
uv run plant-id demo --backend vlm
```

**Identify a photo:**

```bash
uv run plant-id identify --backend vlm --photos /absolute/path/to/photo.jpg
```

Ollama thinking mode defaults **off** (`PLANT_ID_OLLAMA_THINK=false`). Override per run with `--think` on `plant-id identify`, `plant-id demo`, or `eval.run_oxford102`.

When the model returns empty `content` but valid JSON in `thinking`, or a wholly empty response, the VLM repo retries **once** with a fixed corrective suffix (`PLANT_ID_OLLAMA_CONTENT_RETRY_ENABLED=true` by default), then falls back to the existing thinking-json extract if the retry still misplaces JSON.

Ground truth eval (not runtime): `uv run python -m eval.check_ground_truth data/flowers/jpg/image_00018.jpg --identify`

**Oxford 102 eval profiles** (needs `data/flowers/` with `setid.mat`; default backend **`vlm-cloud`**, set `PLANT_ID_VLM_CLOUD_*`):

```bash
uv run python -m eval.run_oxford102 --profile smoke --eval-run-id smoke-check --run-purpose "smoke check"   # 4 images
uv run python -m eval.run_oxford102 --backend vlm --eval-run-id local-smoke --run-purpose "local Ollama parity"      # local Ollama parity
```

Improvement loop: run eval → read `eval_runs/full_identify/index.json` (or `rag_retrieval_only/index.json` for retrieval-only) and run reports → Opik MCP/UI trace diagnosis → change one variable → re-run same profile with new `--eval-run-id` and `--run-purpose`. Enable tracing with `PLANT_ID_OPIK_ENABLED=true`.

## Agent commands

Canonical slash-command prompts live in **`agent/commands/`** (agent-agnostic). Register them in your agent host — see `agent/commands/README.md`. OpenSpec workflow commands (`/opsx-*`) are separate under `.cursor/commands/`.

| Command | Purpose |
|---|---|
| `/eval-run` | Start Oxford 102 eval (default profile `quick`; background run) |
| `/eval-triage` | Summarize benchmark misses (`failures[]`) and next steps |
| `/eval-debug` | Post-mortem all benchmark misses (forensics under `eval/failures/`) |
| `/retrieval-run` | Start retrieval-only eval (`run_retrieval_eval`) |
| `/retrieval-triage` | Summarize retrieval Recall@K misses |
| `/retrieval-debug` | Post-mortem retrieval failures under `eval/failures/` |
| `/verify` | Post-change loop: sync, verify-env, ruff, lint-imports, pytest |
| `/opik-up` | Start/check local Opik via `./scripts/opik.sh` |
| `/identify` | Ad-hoc VLM identify on absolute photo path(s) |
| `/demo` | Bundled sample identify demo |

**Species retrieval (optional):** OpenRouter embeddings (`PLANT_ID_VLM_OPENROUTER_API_KEY`) → `eval.build_retrieval_index` → `./scripts/qdrant.sh seed` → `--retrieval-backend nemotron-prototype`. Optional `describe-hybrid` compares without Qdrant prototypes.

## Layer rules (enforced by `.importlinter`)

```text
interfaces/cli       →  interfaces/composition only (+ stdlib)
interfaces/composition  →  application, domain, infrastructure
application          →  domain
infrastructure       →  domain
domain               →  nothing inward
```

| Layer | Path | Must not import |
|---|---|---|
| domain | `src/plant_id/domain/` | application, infrastructure, interfaces |
| application | `src/plant_id/application/` | infrastructure, interfaces |
| infrastructure | `src/plant_id/infrastructure/` | application, interfaces |
| interfaces/cli | `src/plant_id/interfaces/cli/` | domain, infrastructure |
| interfaces/composition | `src/plant_id/interfaces/composition/` | — (wiring shell; shared by CLI and future HTTP) |

Run `uv run lint-imports` after changing imports.

## Repository ports (domain)

Defined in `src/plant_id/domain/repositories.py`:

- **`IdentificationRepository`** — `identify(observation) -> (ObservationResult, raw dict)`; backends: `vlm` (Ollama), `vlm-cloud` (OpenAI-compatible API), `classical` stub
- **`ArtifactRepository`** — persist run JSON under `identify_artifacts/` (CLI) or eval run `artifacts/` dir (eval-only override)
- **`SpeciesCatalogRepository`** — closed-set label list for prompts

**Use case** (`IdentifyPlantUseCase`) depends only on `IdentificationRepository` + `ArtifactRepository`. It does **not** receive the species catalog.

## Composition and catalog injection

Wiring lives in **`src/plant_id/interfaces/composition/`** — not in infrastructure or use cases.

| Module | Role |
|---|---|
| `container.py` | `build_identify_use_case(backend, settings)` — builds `FileSpeciesCatalog`, injects into repo, wires use case |
| `identify.py` | `execute_identify(...)` — builds `Observation`, runs use case, returns `IdentifyRunResult` |
| `events.py` | `application_events_session(handler)` — binds `ApplicationEvents` |

CLI commands call **`identify_with_cli_presentation`** in `interfaces/cli/presentation.py` (Rich progress). Future HTTP should call **`execute_identify`** directly (no Rich).

**Adding a backend:** implement `IdentificationRepository` in `infrastructure/identification/`, register in `build_identify_use_case()`. Do not change the use case.

## ApplicationEvents

Domain port in `domain/application_events.py`. Infrastructure emits `log_stage` / `log_wait`; default is noop. CLI binds `RichApplicationEvents` via composition + presentation — infrastructure must not import Rich.

## Observability (optional, local-only)

Self-hosted [Opik](https://www.comet.com/docs/opik/self-host/local_deployment) traces VLM calls (Ollama and cloud) from `infrastructure/observability/`. **Default off.** No Comet cloud — do not set `OPIK_API_KEY`.

```bash
export PATH="$HOME/.local/bin:$PATH"   # fresh terminals may need this for uv
# Start Opik (Docker): ./scripts/opik.sh up — UI at http://localhost:5173
export PLANT_ID_OPIK_ENABLED=true
uv run plant-id identify --backend vlm --photos /path/to/your/photo.jpg
```

Tracing uses session config only — **never** call `opik.configure()` from plant-id (it prompts to install Opik MCP in Cursor/VS Code and can hang identify). If you already answered **y** to that prompt, Ctrl+C and re-run; optional cleanup: remove the `opik` entry from `~/.cursor/mcp.json` if you do not want it.

Tracing code MUST stay in infrastructure only — domain, application, and CLI must not import Opik. `ApplicationEvents` / Rich progress is unchanged.

## Eval boundary

Code under **`eval/`** is benchmark-only. It may import runtime/composition for comparisons but must **not** be imported by `IdentifyPlantUseCase`, CLI, or infrastructure repos. External APIs (Pl@ntNet) belong in eval only.

## Conventions for agents

- **Python 3.14.7**, dependencies via **`uv`** (`uv run …`). Interpreter: `.venv/bin/python`.
- Pin versions in `pyproject.toml` / `uv.lock`; bump deliberately.
- Match existing layer placement; never fix import-linter violations by weakening `.importlinter`.
- Species catalog: `resources/species_catalog/default.txt`; images for demo/eval: `data/flowers/` (gitignored).
- OpenSpec main specs: `openspec/specs/`. Completed changes archived under `openspec/changes/archive/`. Next planned change: `classical-ml-backend` (stub in `openspec/changes/classical-ml-backend/`). Do not copy OpenSpec into code comments.
- Prefer minimal diffs; no DI framework — manual composition in `interfaces/composition/`.

### Git commits

Use **Conventional Commits** with a short scope in parentheses:

```text
feat(prompt-v2): disambiguate overlapping catalog labels and harden eval runs
fix(opik): propagate identification errors from identify_trace
chore(openspec): add houseplants-dataset change proposal
```

- **Prompt changes:** one commit per prompt iteration, scope `prompt-vN` matching `prompt_version` in settings (e.g. `closed-set-v2` → `feat(prompt-v2): …`). Do not mix prompt edits with unrelated fixes in the same commit — that makes `git log --grep=prompt` and bisecting eval runs much harder.
- **Small and atomic:** one logical change per commit; split infra, prompt, and eval tooling when they are independent.
- **Dependency order:** commit foundational changes before dependents (e.g. domain/port → infrastructure → tests → docs) so history rebases cleanly and bisect stays meaningful.
- Only commit when the user asks; do not push unless asked.

## Key paths

```text
src/plant_id/domain/              models, ports, ApplicationEvents
src/plant_id/application/         IdentifyPlantUseCase
src/plant_id/infrastructure/      VLM repo, artifacts, catalog, settings, Opik tracing, Ollama env check
src/plant_id/interfaces/composition/   wiring + execute_identify
src/plant_id/interfaces/cli/        plant-id entrypoint
eval/                               offline eval (run_oxford102.py, check_ground_truth.py)
tests/unit/                         fast tests with fakes
tests/integration/                  live Ollama (@pytest.mark.integration)
```
