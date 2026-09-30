# Evaluation (`eval/`)

Benchmark and comparison code only — **not** imported by runtime identification.

## Runner

```bash
# Default quick profile (8 test-split images, ~30 min on qwen3-vl:2b)
uv run python -m eval.run_oxford102 --eval-run-id prompt-v1-baseline --run-purpose "baseline comparison"

# Pipeline sanity (4 images)
uv run python -m eval.run_oxford102 --profile smoke --eval-run-id smoke-check --run-purpose "smoke check"

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
| `curated48` | 48 | Full **yellow16** core + mixed16 extensions + 20 stratified species (`curated48.yaml`) |
| `bolero_and_canterbury` | 2 | Pilot pair with sheets today (`bolero_and_canterbury.yaml`) — quick retrieval / embedding iteration |
| `primula_repeat10` | 10 | `eval/profiles/primula_repeat10.yaml` — `image_03641.jpg` × 10 |
| `english_marigold_repeat10` | 10 | `eval/profiles/english_marigold_repeat10.yaml` — `image_05147.jpg` × 10 |
| `full` | 6,149 | All test-split images |

**Profile manifest:** edit `eval/profiles/quick.yaml` to change `species` and `image` independently per row. Ground truth is validated against `imagelabels.mat` on load. Override with `--profile-manifest /path/to.yaml`.

### CLI flags

| Flag | Default | Purpose |
|---|---|---|
| `--profile` | `quick` | … plus `bolero_and_canterbury` (2-image pilot); see table above |
| `--eval-run-id` | timestamp slug | Correlates report + Opik traces |
| `--run-purpose` | *(required)* | Human-readable reason for this eval |
| `--force` | off | Reuse an existing `eval_runs/full_identify/<id>/` directory |
| `--backend` | `vlm-cloud` | Composition backend (`vlm`, `vlm-cloud`, `classical`); use `--backend vlm` for local Ollama |
| `--think` / `--no-think` | `false` (or `PLANT_ID_OLLAMA_THINK`) | Enable Ollama thinking mode for this eval run |
| `--split` | `test` | Oxford split (`train`, `validation`, `test`) |
| `--limit N` | none | Override profile size |
| `--max-duration` | none | Stop when exceeded (e.g. `30m`) |
| `--quiet` / `--no-quiet` | quiet on | Suppress stderr progress |
| `--dataset-root` | `data/flowers` | Oxford 102 root |
| `--profile-manifest` | auto | YAML species/image pairs for smoke and quick |
| `--output` | auto | Report path (default: `eval_runs/full_identify/<id>/eval/report.json`) |
| `--plantnet-baseline` | off | Optional Pl@ntNet comparison |

## Single-image ground truth

```bash
uv run python -m eval.check_ground_truth data/flowers/jpg/image_00018.jpg
uv run python -m eval.check_ground_truth data/flowers/jpg/image_00018.jpg --identify
```

## Cloud VLM (default eval backend)

Eval defaults to **`vlm-cloud`** (OpenAI-compatible hosted inference). Configure:

- `PLANT_ID_VLM_CLOUD_API_KEY` (canonical; you may `export PLANT_ID_VLM_CLOUD_API_KEY="$FIREWORKS_API_KEY"`)
- `PLANT_ID_VLM_CLOUD_BASE_URL` (default Fireworks: `https://api.fireworks.ai/inference/v1`)
- `PLANT_ID_VLM_CLOUD_MODEL` (example: `accounts/fireworks/models/qwen3-vl-8b-instruct`)
- `PLANT_ID_VLM_CLOUD_REASONING_EFFORT` (default `none` — disables Fireworks DeepSeek thinking; set `high` etc. to re-enable)

Local parity runs: `--backend vlm` (requires Ollama). Verify cloud settings: `uv run plant-id verify-env --backend vlm-cloud`.

## Opik linkage (optional)

When `PLANT_ID_OPIK_ENABLED=true`, each observation trace includes `eval_run_id`, `eval_profile`, and `ground_truth`. Report rows include `trace_id` when available.

## Report metrics and failure forensics

Eval reports include **split accuracy** and a single **benchmark miss** notion for the improvement loop:

| Field | Meaning |
|---|---|
| `top1_accuracy_all` / `top3_accuracy_all` | Over every profile image — **headline** for benchmark quality |
| `top1_accuracy` / `top3_accuracy` | On observations that parsed successfully only |
| `parse_failure_count` | Identification/parsing errors (`error` on the row) |
| `misclassification_count` | Parsed OK but wrong top-1 |
| `failures[]` | All benchmark misses: parse **or** wrong top-1 (`len(failures[]) = parse_failure_count + misclassification_count`) |
| `failure_count` | Parse errors only (same as `parse_failure_count`) — **not** `len(failures[])` |
| `success_count` | Valid parses — **not** “all labels correct” |

When any benchmark miss occurs, stderr prints `Failure forensics: eval_runs/full_identify/<eval-run-id>/eval/failures/` and a summary line `benchmark_misses=N (parse=… misclass=…) parsed_ok=…`.

Each forensics JSON (`eval/failures/<image_stem>.json`) is written for **parse failures and misclassifications**, with `failure_kind`, ground truth, trace id, and (when available) `model.message_content` / truncated reasoning. Use agent command **`/eval-debug`** for a structured post-mortem workflow.

**Eval run layout**

```text
eval_runs/
├── full_identify/              # run_oxford102 bundles + index.json
│   ├── index.json
│   └── <eval-run-id>/…
├── rag_retrieval_only/         # run_retrieval_eval bundles + index.json
│   ├── index.json
│   └── <eval-run-id>/…
└── _legacy_flat_index.json     # optional archive after reorganize_eval_run_layout
```

Do **not** add new runs as flat `eval_runs/<id>/`. One-time move for old trees:

```bash
uv run python -m eval.reorganize_eval_run_layout
```

Full identify reports keep all existing identify fields unchanged and add a **`retrieval`** block (Recall@K, MRR, backend, whether RAG was enabled for identify) plus `retrieval_observations[]` / `retrieval_failures[]`.

**Backfill forensics** for a run that already has `eval/report.json` and identify artifacts but predates misclass forensics:

```bash
uv run python -m eval.sync_failure_forensics curated48-baseline
```

**Legacy layout:** one-time migration from the old flat `artifacts/` tree:

```bash
uv run python -m eval.migrate_eval_runs          # eval reports -> eval_runs/
uv run python -m eval.finalize_legacy_artifacts  # remaining eval + CLI JSON, then remove artifacts/
```

**Workflow:** read failures from the JSON report → open forensics JSON or Opik traces → change one thing → re-run the same profile.

Eval JSON reports include **`inference.usage`** (aggregated prompt/completion/total tokens from API responses) and per-observation token fields when the backend returns usage. Dollar cost is not estimated in-repo; use your provider billing API or dashboard for rated spend.

```bash
export PLANT_ID_OPIK_ENABLED=true
uv run python -m eval.run_oxford102 --profile smoke --eval-run-id prompt-v1 --run-purpose "smoke with Opik"
```

## Pl@ntNet baseline (optional)

Eval-only external comparison. Requires `PLANTNET_API_KEY`. Skips cleanly when the key is missing. Local backend metrics always run.

```bash
export PLANTNET_API_KEY=your-key
uv run python -m eval.run_oxford102 --plantnet-baseline --eval-run-id prompt-v1
```

Label matching uses **exact catalog string equality** — Pl@ntNet scientific names usually will not match Oxford common names unless they appear verbatim in the catalog.

## Species retrieval eval

Retrieval-only runs measure **Recall@K** and **MRR** (ground-truth `catalog_label` in top-K) without calling identify.

**Primary path:** OpenRouter embeddings → `eval.build_retrieval_index` → Qdrant seed → `--retrieval-backend nemotron-prototype`.

Optional **`describe-hybrid`** (VLM describe + BM25 + text embed) is a comparison backend without Qdrant prototype search.

```bash
uv run python -m eval.run_retrieval_eval \
  --profile bolero_and_canterbury \
  --retrieval-backend nemotron-prototype \
  --eval-run-id retrieval-bolero-canterbury \
  --run-purpose "pilot pair retrieval check"
```

| Flag | Default | Purpose |
|---|---|---|
| `--retrieval-backend` | `nemotron-prototype` | `nemotron-prototype` (OpenRouter + Qdrant) or `describe-hybrid` |
| `--top-k` | settings | Recall cutoff and artifact depth |

Artifacts mirror identify eval layout under **`eval_runs/rag_retrieval_only/<id>/`**: `manifest.json`, `eval/report.json`, `artifacts/`, `eval/failures/` on misses. Reports use `run_type: rag_retrieval_only` with a **`retrieval`** metrics block (no VLM `top1_accuracy_all` aliases).

**Corpus workflow**

```bash
uv run python -m eval.validate_species_sheets
uv run python -m eval.synthesize_species_sheet --species "bolero deep blue" --images img1.jpg img2.jpg --out resources/species_sheets/bolero_deep_blue.yaml
# Requires PLANT_ID_VLM_OPENROUTER_API_KEY (OpenRouter Nemotron multimodal embeddings)
uv run python -m eval.build_retrieval_index
./scripts/qdrant.sh seed
```

See `resources/species_sheets/README.md` and `docker/qdrant/README.md`.

**RAG A/B on identify eval**

```bash
uv run python -m eval.run_oxford102 --profile smoke --run-purpose "RAG off" --no-rag --eval-run-id rag-off
uv run python -m eval.run_oxford102 --profile smoke --run-purpose "RAG on" --rag --eval-run-id rag-on
```

Requires `PLANT_ID_RAG_ENABLED` or `--rag` / `--no-rag` and a seeded OpenRouter index for `nemotron-prototype` RAG.

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
