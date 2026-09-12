# UK Plant Identification

Identify flowering plants from photographs using a local vision-language model. Given 1–3 photos of one plant, the CLI returns ranked species predictions as JSON and saves a run record under `artifacts/`.

Inference runs on your machine via Ollama. No cloud or third-party identification APIs are used at runtime.

## Quick start

**Requirements:** macOS, Python 3.14.7, [uv](https://docs.astral.sh/uv/), [Ollama](https://ollama.com/download) 0.33.3+.

```bash
# Install uv (if needed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install Ollama from ollama.com, start it, then:
ollama pull qwen3-vl:2b

# Project setup
uv sync
uv run plant-id verify-env
```

**Demo** (needs flower images in `data/flowers/` — see [Data](#data)):

```bash
uv run plant-id demo --backend vlm
```

**Identify your own photos:**

```bash
uv run plant-id identify --backend vlm --photos /absolute/path/to/photo.jpg
```

Add `--quiet` to hide progress on stderr. Results go to stdout; artifacts to `artifacts/`.

## CLI

| Command | Purpose |
|---|---|
| `plant-id verify-env` | Check Ollama is up and the vision model is installed |
| `plant-id demo --backend vlm` | Identify the bundled sample image |
| `plant-id identify --backend vlm --photos a.jpg` | Identify 1–3 comma-separated photo paths |
| `plant-id identify --backend vlm --photos a.jpg --think` | Same, with Ollama thinking mode enabled for this run |
| `plant-id identify --backend classical …` | Stub — not implemented yet |

## Configuration

Environment variables use the `PLANT_ID_` prefix (see `.env` support in settings).

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_HOST` | `http://127.0.0.1:11434` | Ollama base URL |
| `OLLAMA_THINK` | `false` | Enable qwen3 thinking mode on identify (use `--think` per run to override) |
| `VISION_MODEL` | `qwen3-vl:2b` | Ollama vision model tag (use `qwen3-vl:8b` for accuracy comparison) |
| `SPECIES_CATALOG_PATH` | `resources/species_catalog/default.txt` | Allowed species labels (one per line) |
| `UNCERTAINTY_THRESHOLD` | `0.5` | Top prediction below this sets `uncertain: true` |
| `ARTIFACTS_DIR` | `artifacts/` | Where run JSON files are written |
| `OPIK_ENABLED` | `false` | Export Ollama traces to local Opik (self-hosted only) |
| `OPIK_BASE_URL` | `http://127.0.0.1:5173/api` | Local Opik API URL — do not point at Comet cloud |
| `OPIK_PROJECT_NAME` | `plant-id` | Opik project for identification traces |

## Observability (optional)

For debugging VLM calls during development, you can run [Opik](https://www.comet.com/docs/opik/self-host/local_deployment) locally via the project Docker Compose wrapper. Traces stay on your machine — no Comet cloud account or API key.

**Start Opik** (requires Docker — on macOS, [Colima](https://github.com/abiosoft/colima) works well):

```bash
colima start --cpu 4 --memory 8   # see resource notes below — default 2 GiB is too small
./scripts/opik.sh up
./scripts/opik.sh status          # wait until services are healthy (first boot: several minutes)
```

If `docker` is not found, install/link the CLI: `brew install docker colima && brew link docker`.

The UI is at [http://localhost:5173](http://localhost:5173). SDK API base: `http://127.0.0.1:5173/api`.

On first run, `./scripts/opik.sh` clones the pinned Opik release into `docker/opik/.upstream/` (gitignored). Stop with `./scripts/opik.sh down`. Server image tag is pinned in `docker/opik/.env` (`OPIK_VERSION=2.2.56`).

**Resource use (Colima / Docker)** — Opik is optional and heavy; plant identification via Ollama does **not** need it.

| Resource | Typical impact |
|---|---|
| **Colima VM RAM** | Opik needs **≥ 8 GiB** allocated to Colima (`colima start --memory 8`). The default **2 GiB** VM tends to hang on backend migrations. |
| **Colima VM disk** | Docker images and volumes live under `~/.colima/` — often **10–15 GiB+** once Opik is pulled (macOS may show this as a Lima/`limactl` VM). |
| **CPU** | First Opik start runs MySQL + ClickHouse + Java backend migrations; allow **5–15 minutes** on first boot. `./scripts/opik.sh status` until `backend` and `frontend` are healthy. |
| **Ollama (separate)** | The VLM (`qwen3-vl:2b` by default) uses additional RAM/CPU outside Docker — keep Opik off when you only need `plant-id identify`. |

Stop when not tracing to free memory:

```bash
./scripts/opik.sh down   # stop Opik containers (keeps volumes/images)
colima stop              # stop the Linux VM (keeps ~/.colima disk)
```

To reclaim disk: `docker system prune -a` (inside a running Colima), or `colima delete` to remove the whole VM (you would run `colima start …` again later).

**Enable tracing** for a run:

```bash
export PATH="$HOME/.local/bin:$PATH"   # if uv is not on PATH in a fresh terminal
export PLANT_ID_OPIK_ENABLED=true
uv run plant-id identify --backend vlm --photos /path/to/your/photo.jpg
```

On first enable, Opik logs a one-line confirmation that traces go to the `plant-id` project — that is normal. **Do not** run `opik configure` interactively for this project; if Opik asks to register an MCP server in Cursor/VS Code, answer **N** (the plant-id CLI configures tracing silently and must not block on editor setup).

Open the Opik UI to inspect latency, token counts, prompts, and model output. Tracing is **off by default** — identification works without Opik running. CLI progress (`ApplicationEvents`) is unchanged.

## Data

**Species catalog (required):** `resources/species_catalog/default.txt` — closed-set labels sent to the model. Override with `PLANT_ID_SPECIES_CATALOG_PATH`.

**Images (optional):** for `demo`, eval, and training. Download [Oxford 102 Flowers](https://www.robots.ox.ac.uk/~vgg/data/flowers/102/) and extract to `data/flowers/` (gitignored):

```text
data/flowers/
├── jpg/
├── imagelabels.mat
└── setid.mat
```

## Architecture

Layered Python package under `src/plant_id/`. Dependencies point inward:

```text
interfaces/cli       →  application, interfaces/composition
interfaces/composition  →  application, domain, infrastructure  (wiring + orchestration)
application          →  domain
infrastructure       →  domain
```

| Layer | Responsibility | Must not import |
|---|---|---|
| **domain** | Models, repository ports (`IdentificationRepository`, …), `ApplicationEvents` | application, infrastructure, interfaces |
| **application** | `IdentifyPlantUseCase` — orchestrates identify + persist | infrastructure, interfaces |
| **infrastructure** | Ollama VLM repo, file artifacts, species catalog, settings | application, interfaces |
| **interfaces/cli** | Argument parsing, printing, Rich presentation | domain, infrastructure (use `interfaces/composition`) |
| **interfaces/composition** | Wires backends; builds observations; runs use cases | — (outer shell; shared by CLI and future HTTP) |

**Repository pattern:** backends implement `IdentificationRepository`. The use case depends on the port only, so swapping `--backend vlm` for `--backend classical` does not change application code.

**Catalog injection:** closed-set labels come from `SpeciesCatalogRepository`. The composition root (`interfaces/composition/container.py`) builds `FileSpeciesCatalog` and injects it into identification repos — the use case never sees the catalog.

**Adding a classical backend later:**

1. Implement `IdentificationRepository` in `infrastructure/identification/` (train/load model, map outputs to catalog labels).
2. Register it in `build_identify_use_case()` beside the VLM repo.
3. Keep returning the same `ObservationResult` schema for eval metrics.

Layer boundaries are enforced by `import-linter` — see [Development](#development).

## Development

```bash
uv run ruff check .
uv run lint-imports            # layer boundary contracts (.importlinter)
uv run pytest                  # unit tests; integration test needs Ollama + sample image
uv run pytest -m integration   # live Ollama test only
```

**Ground truth check** (requires `data/flowers/imagelabels.mat`):

```bash
uv run python -m eval.check_ground_truth data/flowers/jpg/image_00018.jpg
uv run python -m eval.check_ground_truth data/flowers/jpg/image_00018.jpg --identify
```

The second form runs VLM identification and reports whether top-1 matches the `.mat` label.

## Evaluation (Oxford 102)

Offline benchmark runner under `eval/`. Default model is **`qwen3-vl:2b`**. The Oxford 102 **test split contains 6,149 images** — use named profiles instead of running the full split during day-to-day iteration.

| Profile | Images | Target budget (2b) | Use |
|---|---|---|---|
| `smoke` | 4 | ~14 min | Pipeline sanity after code changes |
| `quick` | 8 | ~30 min | **Default** — prompt/catalog iteration |
| `full` | 6,149 | days | Long-running benchmark (explicit opt-in) |

```bash
# Default quick profile (~8 images)
uv run python -m eval.run_oxford102 --eval-run-id prompt-v1-baseline

# Fast sanity check
uv run python -m eval.run_oxford102 --profile smoke --eval-run-id smoke-check

# Optional Pl@ntNet comparison (eval-only; needs PLANTNET_API_KEY)
export PLANTNET_API_KEY=your-key
uv run python -m eval.run_oxford102 --plantnet-baseline --eval-run-id prompt-v1
```

Reports are written to `artifacts/eval/` with top-1/top-3 accuracy, per-class breakdown, failures, and (when tracing is enabled) Opik `trace_id` values for diagnosis.

**Improvement loop:** run eval → read JSON report failures → inspect traces in Opik UI or MCP → change one variable (prompt, catalog, threshold) → re-run the same profile with a new `--eval-run-id` suffix → compare reports.

When committing prompt iterations, use **one commit per version** with Conventional Commits and a `prompt-vN` scope (see [Git commits](#git-commits) below).

Enable Opik during eval runs:

```bash
export PLANT_ID_OPIK_ENABLED=true
uv run python -m eval.run_oxford102 --profile smoke --eval-run-id prompt-v1
```

See `eval/README.md` for eval boundary rules and flag reference.

### Git commits

This project uses [Conventional Commits](https://www.conventionalcommits.org/) with a scope in parentheses:

```text
feat(prompt-v2): disambiguate overlapping catalog labels and harden eval runs
fix(opik): propagate identification errors from identify_trace
chore(openspec): add houseplants-dataset change proposal
```

**Prompt iterations** (`PROMPT_TEMPLATE` / `prompt_version` in settings) should land in **dedicated commits** scoped as `feat(prompt-vN): …`, where `N` matches the version string (e.g. `closed-set-v2` → `prompt-v2`). Keep prompt changes separate from unrelated infrastructure or eval fixes so you can search history and bisect eval results easily.

Prefer **small, atomic commits** in **dependency order** (lower layers before callers; tests with the code they cover).

## Agent shortcuts

Repeatable agent slash commands (eval runs, verify, identify, Opik) are defined in **`agent/commands/`** — one canonical source for any coding agent. Register them in your host per `agent/commands/README.md`. Full index: **`AGENTS.md`** (Agent commands section). OpenSpec planning uses separate `/opsx-*` commands.

Python interpreter: `.venv/bin/python` (created by `uv sync`).

**Pinned versions:** Python 3.14.7, pydantic 2.13.5, ollama 0.6.2, opik 2.2.56, rich 14.3.2 — full list in `pyproject.toml` / `uv.lock`.

## Layout

```text
src/plant_id/           application code
resources/species_catalog/
data/                   downloaded datasets (gitignored)
eval/                   offline evaluation (not used by the CLI)
tests/
artifacts/              run output (gitignored)
```

## License

No production license declared.
