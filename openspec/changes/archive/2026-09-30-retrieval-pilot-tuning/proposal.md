## Why

Retrieval on the `bolero_and_canterbury` pilot shows near-tie prototype scores (e.g. canterbury test photo ranks bolero first by ~0.0002). Macro Recall@K/MRR hide per-image confusions, and index build uses **first-N train** prototypes with no visibility into **which prototype point won**. We need eval-only tooling and optional prototype curation before RAG-on identify runs are meaningful.

## What Changes

- **Retrieval debug artifacts**: per query, record winning prototype metadata (`prototype_kind`, `prototype_id`, `source_image` when present, score) in eval artifacts and/or report rows — in addition to species-level ranks.
- **Optional curated prototypes** for index build: allow specifying train (or manifest-listed) image paths per `catalog_label` instead of only first-N train-split scan — starting with the two pilot sheets.
- **Per–ground-truth retrieval summary** in reports (pilot-friendly): e.g. per `catalog_label` hit rate at K alongside existing macro `retrieval.recall_at_k` (additive fields only).
- **Eval/dev CLI** to inspect index manifest + optional pairwise similarity spike for a profile (read-only, no runtime change).
- **Agent commands** updated to prefer prototype-level forensics when debugging retrieval misses.

## Capabilities

### New Capabilities

_(none — behavior extends existing retrieval eval and index build)_

### Modified Capabilities

- `retrieval-evaluation`: prototype-level debug in artifacts/reports; per-label retrieval summary; triage order (observations before macro).
- `evaluation-metrics`: additive report fields for per-class/per-GT retrieval stats on full identify and retrieval-only reports.
- `species-retrieval`: optional curated prototype image list per species for `build_retrieval_index` (train-split validated, no test leakage).
- `agent-dev-commands`: retrieval debug/triage reference prototype winners and curated-index workflow.

## Impact

- **Eval-only** (`eval/build_retrieval_index.py`, retrieval scoring/report, new small `eval/` helpers); **no** changes to `IdentifyPlantUseCase` or RAG inject path unless later tasks explicitly wire curated index.
- **Infrastructure**: index manifest may gain optional curation metadata; Qdrant payloads unchanged in spirit (still catalog_label + sheet text fields).
- **Docs**: `eval/README.md`, `resources/species_sheets/README.md`, agent commands.
- **Dependencies**: builds on archived **species-rag-retrieval** (OpenRouter + Qdrant, `bolero_and_canterbury` profile, split `eval_runs/` layout).

## Non-goals

- Expanding the species sheet corpus beyond pilot-driven edits (no “index all 102” in this change).
- Replacing Nemotron with a new embedder or adding CLIP/local embed backends.
- Automatic sheet rewriting or fine-tuning embeddings.
- Runtime RAG prompt changes (identify with `--rag` A/B is out of scope until retrieval metrics pass on the pilot).

## Decision gates

1. **Curation source of truth**: YAML alongside species sheets vs entries in `bolero_and_canterbury.yaml` only — design picks one for pilot.
2. **Report shape**: extend `retrieval_observations[]` vs separate `retrieval_prototype_hits[]` — design picks minimal additive JSON.
3. **Gate for RAG eval**: team agrees pilot Recall@1 acceptable on both images (or documents accepted tradeoff) before `--rag` compare runs.

## Developer experience

- Document rebuild loop: edit sheet and/or curation → `build_retrieval_index` → `qdrant.sh seed` → `run_retrieval_eval --profile bolero_and_canterbury`.
- Add a single inspect command (e.g. `eval.inspect_retrieval_index` or flags on existing module) runnable without API keys when manifest/vectors exist locally.
