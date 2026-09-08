# UK Plant Identification

Local-only plant identification learning project targeting the **Oxford 102 Flowers** benchmark (~102 UK flowering plant classes). Runtime inference uses local backends only — no Pl@ntNet or other external ID APIs at runtime.

OpenSpec change: `openspec/changes/uk-plant-id-poc/`

## Architecture

```text
interfaces (CLI)  -->  composition  -->  application use cases
                                              |
                         domain (models + repository Protocols)
                                              ^
                         infrastructure (VLM repo, file repo, catalog)
```

| Layer | Role |
|---|---|
| **domain** | Models, repository interfaces — no outward imports |
| **application** | `IdentifyPlantUseCase` — depends on repository ports only |
| **infrastructure** | Ollama VLM repo, artifacts, Oxford 102 catalog |
| **interfaces** | Thin CLI (`plant-id`) — parsing and wiring only |

Swappable backends via `IdentificationRepository` (`--backend vlm` now; `--backend classical` later).

**Runtime policy:** local Ollama + project code only. External APIs (Pl@ntNet) are eval-only in a later change.

## Prerequisites

| Tool | Version | Notes |
|---|---|---|
| macOS | recent | primary dev platform |
| Python | 3.14.7 | `.python-version` |
| [uv](https://docs.astral.sh/uv/) | 0.12.10+ | dependency management |
| [Ollama](https://ollama.com/download) | 0.33.3+ | local VLM server |
| Node | 24.13.1 | OpenSpec CLI only (see `.nvmrc`) |

### Install uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Install Ollama

Download from [ollama.com/download](https://ollama.com/download), start the app, then pull the candidate vision model:

```bash
ollama pull qwen3-vl:8b
```

## Setup

```bash
uv sync
uv run plant-id verify-env
```

## Pinned runtime libraries

| Package | Version |
|---|---|
| Python | 3.14.7 |
| pydantic | 2.13.5 |
| pydantic-settings | 2.13.0 |
| PyYAML | 6.0.3 |
| Pillow | 12.3.0 |
| ollama | 0.6.2 |

Dev: ruff 0.16.6, pytest 9.1.1, import-linter 2.13

## Configuration

Environment variables (prefix `PLANT_ID_`):

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_HOST` | `http://127.0.0.1:11434` | Ollama base URL |
| `VISION_MODEL` | `qwen3-vl:8b` | Locked after task 1.6 spike (Intel macOS) |
| `UNCERTAINTY_THRESHOLD` | `0.5` | Below this, top prediction marked uncertain |
| `SPECIES_CATALOG_PATH` | `resources/species_catalog/default.txt` | Closed-set label list for identification |
| `ARTIFACTS_DIR` | `artifacts/` | JSON run artifacts |

## Datasets

**Runtime species catalog (bundled):** `resources/species_catalog/default.txt` — one label per line. The default file is the Oxford 102 Flowers vocabulary; point `PLANT_ID_SPECIES_CATALOG_PATH` at another file to swap closed sets without code changes.

**Downloaded images (local, gitignored):** extract under `data/oxford102/` for eval, demo, and future training:

```text
data/oxford102/
├── jpg/              # image_00001.jpg …
├── imagelabels.mat
└── setid.mat
```

**Full dataset source:** [VGG Oxford 102 Flowers](https://www.robots.ox.ac.uk/~vgg/data/flowers/102/) (train/val/test splits in `setid.mat`).

## Commands

```bash
uv run plant-id verify-env          # Ollama + model check
uv run plant-id demo --backend vlm  # sample image from data/oxford102/
uv run plant-id identify --backend vlm --photos path/to/photo.jpg
uv run ruff check .                 # lint
uv run pytest                       # unit tests
uv run lint-imports                 # layer boundaries (added in task 6.1)
```

Use `--quiet` to suppress CLI progress output on stderr.

## Hardware spike (task 1.6) — complete

**Decision (2026-09-08, Intel macOS):** keep default **`qwen3-vl:8b`**. No fallback model.

| Metric | Observed |
|---|---|
| Ollama steady RAM | ~7 GB |
| RAM spike during inference | ~+1 GB |
| Latency | Second run ≥2× faster than first (cold model load) |
| Vision quality | Correctly described photo content (not path guessing) |

**CLI notes (Ollama 0.33.3):**

- No `--image` flag — put an **absolute** `.jpg` path in the prompt (`~` is not expanded).
- Use `--hidethinking` for smoke tests; the app will disable thinking for identification.
- Production path uses the Python `ollama` client with an `images` array (task 4.2).

```bash
uv run plant-id verify-env

# Manual vision smoke test (replace with your absolute path)
ollama run qwen3-vl:8b --hidethinking \
  "describe this image: /Users/you/.../data/oxford102/jpg/image_00001.jpg"
```

Task **4.2** (live VLM integration) is unblocked.

## Project layout

```text
src/plant_id/
  domain/           models, repository Protocols
  application/      use cases
  infrastructure/   repos, config, composition
  interfaces/cli/   plant-id CLI
resources/species_catalog/   bundled default.txt (Oxford 102 labels today)
data/oxford102/              downloaded images + .mat splits (gitignored)
eval/                eval-only code (Change 2); not runtime
tests/
openspec/           specifications and change plans
```

## License

Learning project — no production license declared.
