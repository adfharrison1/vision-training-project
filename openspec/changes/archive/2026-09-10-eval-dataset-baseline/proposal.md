## Why

Observability is in place for single-image debugging, but the project still lacks systematic accuracy measurement against Oxford 102 ground truth. This is a **learning project**: the default VLM is now **`qwen3-vl:2b`** (fast iteration on Intel macOS). The eval runner must measure that baseline, support ~30-minute improvement rounds, and link failures to Opik traces for diagnosis before optimising prompts, RAG, or classical ML.

## What Changes

- Extend `eval/` with Oxford 102 dataset loading (image paths, labels, train/val/test splits via `setid.mat`).
- Add an eval runner with **named profiles** (`smoke`, `quick`, `full`) — default **`quick`** (~8 images, ~30 min on 2b), not the full 6,149-image test split.
- Wire local backends through `execute_identify`; default model **`qwen3-vl:2b`** via settings (override with `PLANT_ID_VISION_MODEL` e.g. `qwen3-vl:8b` for comparison).
- Compute top-1 / top-3 accuracy, per-class breakdown, per-observation timing, and optional **Opik trace linkage** (`eval_run_id`, `observation_id`, `trace_id` when tracing enabled).
- Write JSON eval reports under `artifacts/eval/`.
- Add **optional** Pl@ntNet baseline adapter — eval-only, flag-gated.
- Document Oxford 102 layout, eval profiles, and the **eval → report → Opik MCP → fix → re-run** improvement loop in README and `eval/README.md`.
- Move `scipy` from dev-only to runtime dependency.

## Depends on

- `uk-plant-id-poc` — layered runtime, `execute_identify`, species catalog, artifact persistence
- `local-opik-observability` — optional tracing during eval; trace metadata links to eval reports

## Decision gates (resolved in design.md)

- Oxford 102 layout: `data/flowers/jpg/`, `imagelabels.mat`, `setid.mat`
- **Test split size: 6,149 images** (10 train + 10 val per class; remainder is test)
- Label matching: exact catalog string equality (same as `check_ground_truth.py`)
- **Default VLM: `qwen3-vl:2b`**; `qwen3-vl:8b` for accuracy comparison only
- **Eval profiles:** `smoke` (4), `quick` (8, default), `full` (all test images — long-running benchmark)
- **30-minute improvement rounds:** `quick` profile on 2b (~3.5 min/image observed)
- Opik: `eval_run_id` on trace metadata; `trace_id` in report rows when enabled
- Pl@ntNet: optional; `PLANTNET_API_KEY`; graceful skip
- Eval MUST NOT implement `IdentificationRepository`

## Capabilities

### New Capabilities

- `evaluation-dataset`: Oxford 102 loading, splits, profile-based image selection
- `evaluation-metrics`: top-k accuracy, per-class stats, eval report with Opik linkage fields
- `eval-baseline-plantnet`: optional Pl@ntNet comparison adapter (eval-only)

### Modified Capabilities

- `local-dev-environment`: Oxford 102 download, eval profiles, 2b default, Opik eval workflow docs

## Non-goals

- RAG, fine-tuning, HTTP API, or production deployment
- Pl@ntNet as runtime fallback
- Full scientific-name ontology for Pl@ntNet (exact catalog match only in v1)
- Classical ML training (deferred)
- Expecting full test-split VLM eval to finish in 30 minutes (use `full` as overnight/weekend benchmark)
- Parallel/async batching in v1

## Impact

- New modules under `eval/` (`dataset`, `metrics`, `runner`, `baselines/plantnet.py`)
- Small infrastructure addition to expose Opik `trace_id` to eval runner when tracing enabled (see design.md)
- `scipy==1.18.1` promoted to main dependencies; pinned `httpx` for Pl@ntNet
- README, `eval/README.md`, AGENTS.md updates
- Runtime default model already `qwen3-vl:2b` in settings (outside this change's core scope but referenced by eval)
