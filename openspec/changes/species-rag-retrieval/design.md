## Context

See `proposal.md`. User-locked architecture: git sheets → build embeddings → seed Qdrant → swappable retrieval backends → retrieval eval → (later) identify prompt augment.

## Goals / Non-Goals

**Goals**

- Reproducible corpus + index + local Qdrant seed workflow
- Multi-prototype CLIP indexing per `catalog_label`
- Two retrieval backends comparable via the same eval harness
- Retrieval port swappable in infrastructure (fake in unit tests)
- Eval artifacts parallel to `eval/run_oxford102.py` (manifest, report, failures, agent commands)

**Non-Goals**

- Single-image prototype indexing
- Storing vectors inside YAML sheets
- Runtime dependency on Oxford filenames or GT labels

## Architecture

### Layers

```text
domain/
  SpeciesRetrievalRepository (port)  → retrieve(observation photos, k) → RetrievedSpeciesContext[]
  (optional) SpeciesSheet — value types only

infrastructure/
  retrieval/
    qdrant_store.py          — upsert/query; implements low-level store behind port
    clip_prototype_backend.py
    describe_hybrid_backend.py  — VLM describe + BM25 + text embed fusion
  species_sheets/            — load YAML from disk (also used to seed Qdrant payloads)

composition/
  build_retrieval_repo(backend, settings)
  (later) inject into VLM prompt builder when PLANT_ID_RAG_ENABLED

eval/
  synthesize_species_sheet.py   — multi-image → YAML (Fireworks/vlm-cloud client)
  build_retrieval_index.py      — Oxford train images + sheets → embedding artifacts
  run_retrieval_eval.py         — Recall@K runner
  retrieval_failure_forensics.py
```

Application use case **`IdentifyPlantUseCase`** stays unchanged until augment tasks; RAG is wired in **infrastructure prompt builder** or composition wrapper, not domain rules.

### Sheet schema (YAML)

```yaml
catalog_label: bolero deep blue   # must match species_catalog
retrieval_text: |                 # species morphology; embedded (CLIP text + BM25 corpus)
context_block: |                  # disambiguation; stored in Qdrant payload, not embedded (optional embed later)
provenance:                       # optional
  authored_by: vlm-synth|human
  source_images: []               # Oxford paths used in synth script only
  prompt_version: sheet-synth-v1
```

### Multi-prototype indexing

For each species:

1. **Text point(s):** CLIP text encoder on `retrieval_text` (+ optional title = `catalog_label`).
2. **Image points:** CLIP image encoder on each configured **reference image** (default: Oxford **train** images for that class, cap N per species to control size).

Qdrant point payload: `{ catalog_label, prototype_kind: text|image, prototype_id, retrieval_text?, context_block }`.

**Query scoring:** For each user photo, compute similarity to all points; **species score = max** similarity over that species’ prototypes (configurable to top-m mean later).

Reference images are **indexing-only**; eval **test** images are never used as prototypes (leakage gate in build script).

### Git vs Qdrant vs embeddings

| Artifact | Location | Role |
|----------|----------|------|
| Sheet YAML | `resources/species_sheets/` (git) | Human/VLM-authored source of truth |
| Built index | `artifacts/retrieval_index/` (gitignored by default; optional committed tarball for CI) | Vectors + manifest (model ids, CLIP version, image list checksum) |
| Qdrant | Docker volume | Runtime query; **seeded** from built index |

**Compose flow (corrected):**

1. `docker/qdrant` `up` starts Qdrant only.
2. **`scripts/qdrant.sh seed`** (or compose `depends_on` one-shot seed service) runs **after** Qdrant healthy:
   - Requires prior **`uv run python -m eval.build_retrieval_index`** (or seed invokes build if manifest missing — slower first run).
   - Upserts points idempotently (collection version in manifest).

Embeddings are **not** hand-maintained in git like YAML; they are **regenerated** when sheets or prototype image sets change, then re-seed. Optionally commit a small **pilot** index for curated48 species only later.

### Qdrant seed on `compose up`

**Yes, with a nuance:** auto-seed on every `up` is fine if the seed script is **idempotent** and fast (upsert by point id). First-time devs still run **build-index** once when sheets change. Document: `qdrant up` → `build-index` → `qdrant seed` (seed may be chained in `qdrant.sh up` after healthcheck).

### Swappable backends (like vlm / vlm-cloud)

Settings + composition:

| Backend id | Query | Index use |
|------------|-------|-----------|
| `clip-prototype` | CLIP image embed(photo) vs Qdrant vectors | Image + text prototypes |
| `describe-hybrid` | Neutral VLM describe(photo) → BM25 scores + text-embed vector vs sheet text vectors; fused rank | Text vectors in Qdrant; BM25 corpus from `retrieval_text` in memory or sidecar |

Describe VLM: reuse **`VlmCloudIdentificationRepository`**’s client with a **different prompt** (infrastructure module, not identify repo), or small `DescribeClient` sharing settings. Local Ollama describe variant optional parity task.

**One change, two backends:** implement CLIP path first for end-to-end index+eval; describe-hybrid second — **same** `run_retrieval_eval.py` and report schema, not two OpenSpec changes.

**BM25 + text embed:** not two iterations — **one describe backend** that merges lexical and semantic scores (weighted sum; weights in settings for eval sweeps).

### Sheet synthesis script (a)

- CLI: `eval/synthesize_species_sheet.py --species "bolero deep blue" --images img1 img2 ... --out resources/species_sheets/...`
- Uses `Settings` vlm_cloud_* ; multi-image message same as identify
- Prompt: synthesise `retrieval_text` + `context_block`; **forbid** dataset names, image ids, “in frame”; require confusion notes vs catalog neighbors optional flag
- Output YAML for **human review** before git commit

### Retrieval eval (d)

Mirror VLM eval patterns:

```text
eval_runs/   (reuse dir or retrieval_runs/ — **decision: reuse eval_runs/** with run_type in manifest)
  {retrieval_run_id}/
    manifest.json       # run_purpose, retrieval_backend, embed_models, git_commit, qdrant_collection
    eval/report.json    # Recall@1/@3/@5, MRR, per-profile aggregates
    eval/failures/      # GT not in top-K forensics
    artifacts/          # per-image retrieval JSON (scores, top labels, query metadata)
```

Agent commands: `/retrieval-run`, `/retrieval-triage`, `/retrieval-debug` (parallel to eval-*)

Metrics: **Recall@K** (GT `catalog_label` in top-K species), **MRR**, optional confuser-ranked-above-GT flag.

No identify call in retrieval-only mode.

### Identify augment (e)

Later tasks in same change: `PLANT_ID_RAG_ENABLED`, inject formatted `context_block` for top-K with pairwise layout; end-to-end eval profile compares v4.2 + RAG vs baseline.

## Alternatives considered

| Alternative | Rejected because |
|-------------|------------------|
| Direct GT class lookup | Eval cheat; not prod-shaped |
| Single prototype per species | Overfits one reference photo |
| numpy-only index forever | User wants Qdrant now for scale practice |
| Separate OpenSpec changes per backend | Same eval harness; swappable repos suffice |
| Embed `context_block` | Long noisy vectors; inject only for VLM |

## Risks

- **Train-image prototypes + test eval** — mitigate with split enforcement in build script
- **Describe path cost/latency** — eval default backend `clip-prototype`; describe for comparison runs
- **OpenSpec “local-only runtime”** — document that retrieval describe may use vlm-cloud like identify; CLIP stays local

## Open questions (non-blocking)

- Weight defaults for BM25 vs text-embed fusion
- Whether to use separate Qdrant collection per embed model or payload filter
- Commit pilot `artifacts/retrieval_index/` for CI or generate in CI job only

## Pinned versions (verify on implementation date)

| Component | Target |
|-----------|--------|
| Python | 3.14.7 (existing) |
| qdrant-client | latest stable at task time |
| open-clip-torch or open_clip | latest stable at task time |
| sentence-transformers | latest stable at task time |
| rank-bm25 | latest stable at task time |

Record exact pins in `pyproject.toml` when tasks execute.

## Supersedes

- `openspec/changes/direct-species-rag/` (placeholder)
- `openspec/changes/vector-retrieval/` (placeholder)

Update `openspec/config.yaml` sequence when this change is approved for implementation.

## Documentation (standing stipulation)

Every implementation task group that changes developer-facing behavior SHALL update **all relevant READMEs in the same PR/session**, not deferred to archive-only.

| README | Update when |
|--------|-------------|
| [`README.md`](../../../README.md) | Qdrant/Opik-style setup, new env vars, RAG identify flags, links to eval retrieval |
| [`eval/README.md`](../../../eval/README.md) | Sheet synth, build-index, retrieval eval, forensics, RAG A/B on Oxford eval |
| `resources/species_sheets/README.md` | Sheet schema, authoring, review expectations (created in task 1.1) |
| [`agent/commands/README.md`](../../../agent/commands/README.md) | Register `/retrieval-*` commands when added |
| `docker/qdrant/README.md` (if present) | Compose, seed, troubleshooting |

Cross-links between root and eval README SHALL stay consistent (single canonical command strings). `AGENTS.md` agent command table updated alongside `agent/commands/README.md`.
