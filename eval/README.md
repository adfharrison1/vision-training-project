# Evaluation (`eval/`)

Benchmark and comparison code only — **not** imported by runtime identification.

## Runner

```bash
# Default quick profile (8 test-split images, ~30 min on qwen3-vl:2b)
uv run python -m eval.run_oxford102 --eval-run-id prompt-v1-baseline

# Pipeline sanity (4 images)
uv run python -m eval.run_oxford102 --profile smoke --eval-run-id smoke-check

# Full test split (~6,149 images — long-running benchmark)
uv run python -m eval.run_oxford102 --profile full --eval-run-id full-benchmark
```

### Profiles

| Profile | Images | Notes |
|---|---|---|
| `smoke` | 4 | First 4 rows from `eval/profiles/quick.yaml` |
| `quick` | 8 | All 8 rows from `eval/profiles/quick.yaml` — one fixed image per species |
| `mixed16` | 16 | All rows from `eval/profiles/mixed16.yaml` — 2 regression images + 14 fresh species |
| `yellow16` | 16 | All rows from `eval/profiles/yellow16.yaml` — 10 yellow-forward species + 6 contrast rows |
| `full` | 6,149 | All test-split images |

**Profile manifest:** edit `eval/profiles/quick.yaml` to change `species` and `image` independently per row. Ground truth is validated against `imagelabels.mat` on load. Override with `--profile-manifest /path/to.yaml`.

### CLI flags

| Flag | Default | Purpose |
|---|---|---|
| `--profile` | `quick` | `smoke`, `quick`, `mixed16`, `yellow16`, or `full` |
| `--eval-run-id` | timestamp slug | Correlates report + Opik traces |
| `--backend` | `vlm` | Composition backend (`vlm`, `classical`) |
| `--think` / `--no-think` | `false` (or `PLANT_ID_OLLAMA_THINK`) | Enable Ollama thinking mode for this eval run |
| `--split` | `test` | Oxford split (`train`, `validation`, `test`) |
| `--limit N` | none | Override profile size |
| `--max-duration` | none | Stop when exceeded (e.g. `30m`) |
| `--quiet` / `--no-quiet` | quiet on | Suppress stderr progress |
| `--dataset-root` | `data/flowers` | Oxford 102 root |
| `--profile-manifest` | auto | YAML species/image pairs for smoke and quick |
| `--output` | auto | Report path under `artifacts/eval/` |
| `--plantnet-baseline` | off | Optional Pl@ntNet comparison |

## Single-image ground truth

```bash
uv run python -m eval.check_ground_truth data/flowers/jpg/image_00018.jpg
uv run python -m eval.check_ground_truth data/flowers/jpg/image_00018.jpg --identify
```

## Opik linkage (optional)

When `PLANT_ID_OPIK_ENABLED=true`, each observation trace includes `eval_run_id`, `eval_profile`, and `ground_truth`. Report rows include `trace_id` when available.

**Workflow:** read failures from the JSON report → inspect traces in Opik UI or MCP → change one thing → re-run the same profile.

```bash
export PLANT_ID_OPIK_ENABLED=true
uv run python -m eval.run_oxford102 --profile smoke --eval-run-id prompt-v1
```

## Pl@ntNet baseline (optional)

Eval-only external comparison. Requires `PLANTNET_API_KEY`. Skips cleanly when the key is missing. Local backend metrics always run.

```bash
export PLANTNET_API_KEY=your-key
uv run python -m eval.run_oxford102 --plantnet-baseline --eval-run-id prompt-v1
```

Label matching uses **exact catalog string equality** — Pl@ntNet scientific names usually will not match Oxford common names unless they appear verbatim in the catalog.

## Dataset layout

```text
data/flowers/
├── jpg/image_XXXXX.jpg
├── imagelabels.mat
└── setid.mat          # trnid, valid, tstid split index arrays
```

Test split size: **6,149 images**.

## Runtime boundary

```text
Runtime:  CLI --> use case --> IdentificationRepository (local only)

Eval:     eval/run_oxford102.py --> execute_identify (composition)
          eval/baselines/plantnet.py  (optional; NOT a repository)
```

Eval modules MUST NOT be imported from `src/plant_id/`.
