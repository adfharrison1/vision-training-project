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
| `VISION_MODEL` | `qwen3-vl:8b` | Model tag (confirm via hardware spike) |
| `UNCERTAINTY_THRESHOLD` | `0.5` | Below this, top prediction marked uncertain |
| `CLASS_NAMES_PATH` | `resources/oxford102/class_names.txt` | Oxford 102 label list |
| `ARTIFACTS_DIR` | `artifacts/` | JSON run artifacts |

## Oxford 102 data

**Demo / closed-set labels:** bundled `resources/oxford102/class_names.txt` (added in a later task).

**Full eval dataset (optional until Change 2):** download Oxford 102 Flowers from the [VGG page](https://www.robots.ox.ac.uk/~vgg/data/flowers/102/) for train/val/test splits and labelled images.

## Commands

```bash
uv run plant-id verify-env          # Ollama + model check
uv run ruff check .                 # lint
uv run pytest                       # unit tests
uv run lint-imports                 # layer boundaries (added in task 6.1)
```

Identification commands (`identify`, `demo`) arrive in a later implementation phase.

## Hardware spike (task 1.6)

Before live VLM integration (task 4.2), run this manual spike on **your** machine:

1. Install Ollama 0.33.3+ and run `ollama pull qwen3-vl:8b`
2. Pick one Oxford 102 sample image (or any clear flower photo for a smoke test)
3. Record:
   - Wall-clock latency for one identification-sized request
   - Peak RAM during inference (Activity Monitor)
   - Subjective output quality (does the model follow JSON instructions?)
4. If `qwen3-vl:8b` is too slow or heavy on Intel hardware, try a smaller vision model, set `PLANT_ID_VISION_MODEL`, and document the choice here

```bash
# Quick connectivity check (full identify flow comes later)
uv run plant-id verify-env
ollama run qwen3-vl:8b "Describe this flower in one sentence." --verbose
```

Update `PLANT_ID_VISION_MODEL` / README only after the spike passes.

## Project layout

```text
src/plant_id/
  domain/           models, repository Protocols
  application/      use cases
  infrastructure/   repos, config, composition
  interfaces/cli/   plant-id CLI
resources/oxford102/
eval/               eval-only code (Change 2); not runtime
tests/
openspec/           specifications and change plans
```

## License

Learning project — no production license declared.
