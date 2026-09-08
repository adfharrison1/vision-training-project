# UK Plant Identification

Identify flowering plants from photographs using a local vision-language model. Given 1–3 photos of one plant, the CLI returns ranked species predictions as JSON and saves a run record under `artifacts/`.

Inference runs on your machine via Ollama. No cloud or third-party identification APIs are used at runtime.

## Quick start

**Requirements:** macOS, Python 3.14.7, [uv](https://docs.astral.sh/uv/), [Ollama](https://ollama.com/download) 0.33.3+.

```bash
# Install uv (if needed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install Ollama from ollama.com, start it, then:
ollama pull qwen3-vl:8b

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
| `plant-id identify --backend classical …` | Stub — not implemented yet |

## Configuration

Environment variables use the `PLANT_ID_` prefix (see `.env` support in settings).

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_HOST` | `http://127.0.0.1:11434` | Ollama base URL |
| `VISION_MODEL` | `qwen3-vl:8b` | Ollama vision model tag |
| `SPECIES_CATALOG_PATH` | `resources/species_catalog/default.txt` | Allowed species labels (one per line) |
| `UNCERTAINTY_THRESHOLD` | `0.5` | Top prediction below this sets `uncertain: true` |
| `ARTIFACTS_DIR` | `artifacts/` | Where run JSON files are written |

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
interfaces/cli  →  application  →  domain  ←  infrastructure
                         ↑
              composition wires backends here
```

| Layer | Responsibility | Must not import |
|---|---|---|
| **domain** | Models, repository ports (`IdentificationRepository`, …), `ApplicationEvents` | application, infrastructure, interfaces |
| **application** | `IdentifyPlantUseCase` — orchestrates identify + persist | infrastructure, interfaces |
| **infrastructure** | Ollama VLM repo, file artifacts, species catalog, settings | interfaces |
| **interfaces** | CLI parsing, wiring, Rich progress UI | direct `ollama` calls (use infrastructure) |

**Repository pattern:** backends implement `IdentificationRepository`. The use case depends on the port only, so swapping `--backend vlm` for `--backend classical` does not change application code.

**Catalog injection:** closed-set labels come from `SpeciesCatalogRepository`. The composition root (`infrastructure/composition/container.py`) builds `FileSpeciesCatalog` and injects it into identification repos — the use case never sees the catalog.

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

Python interpreter: `.venv/bin/python` (created by `uv sync`).

**Pinned versions:** Python 3.14.7, pydantic 2.13.5, ollama 0.6.2, rich 14.3.2 — full list in `pyproject.toml` / `uv.lock`.

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
