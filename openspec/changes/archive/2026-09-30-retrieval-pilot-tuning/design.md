## Context

See `proposal.md`. Today: Nemotron query embed → Qdrant search over text + train-image prototypes; species score = max prototype score per label (`aggregate_max_per_label`). Index build picks first matching train images per label. Pilot eval profile `bolero_and_canterbury` has two test images; canterbury Recall@1 fails with ~0.0002 score gap. Reports already include macro `retrieval` + `retrieval_observations[]` but not **which prototype won**.

## Goals / Non-Goals

**Goals:**

- Make retrieval tuning **actionable**: see prototype winners per query without manual Qdrant/vector hacking.
- Allow **curated train prototypes** for pilot species without forking embedder code.
- Add **per-label retrieval stats** so two-image pilots are readable without abandoning macro metrics for larger profiles.
- Keep all changes **eval/index tooling**; no identify use case changes in this change.

**Non-Goals:**

- New species sheets at scale, new embed models, RAG prompt edits, or auto-optimization loops.
- Committing large `artifacts/retrieval_index/` vectors to git (unchanged policy).

## Decisions

### 1. Curation source: `resources/species_sheets/prototypes.yaml` (pilot)

**Choice:** Single optional YAML map `catalog_label → list of train image filenames` (e.g. `image_01234.jpg`), validated at index build.

**Alternatives:** Per-sheet `prototypes:` field in each species YAML (more scattered); reuse `bolero_and_canterbury.yaml` (wrong layer — eval profile ≠ index corpus).

**Rationale:** One place to edit while tuning the campanula pair; sheets stay morphology/RAG focused.

### 2. Prototype debug: extend per-query eval artifacts + observation rows

**Choice:** When scoring retrieval in eval, capture top-M raw Qdrant hits (or in-memory search hits) before aggregation; persist in per-image artifact JSON under `winning_prototypes` / `raw_hits` and mirror summary fields on `retrieval_observations[]` (additive optional fields).

**Alternatives:** Separate report section only (harder to diff in gitignored runs); Opik spans (overkill).

**Rationale:** Artifacts already exist per stem; agents already read them.

### 3. Per-class retrieval: `retrieval_per_class` sibling to identify `per_class`

**Choice:** New top-level map `{ label: { total, recall_at_k: {1: …} } }` computed from observation rows.

**Alternatives:** Overload identify `per_class` (confusing semantics).

### 4. Inspect CLI: `python -m eval.inspect_retrieval_index`

**Choice:** Read manifest + optional vectors; print point counts per label, list image paths, optional cosine matrix for labels in a profile manifest.

**Alternatives:** Notebook only (not documented in repo).

### 5. Backend change scope

**Choice:** Extend `NemotronPrototypeRetrievalRepository` search path used by eval scoring only with a debug hook returning raw hits; runtime identify/RAG continues to call `retrieve()` without new surface area unless needed later.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Larger artifact JSON | Cap raw hits (e.g. top 10 pre-aggregate); keep report rows slim |
| Curation overfits pilot test photos if someone cheats test paths | Train-split validation + assert_not_test_split |
| Dual prototype sources (curated + first-N) duplicate points | Merge policy: curated replaces auto list when non-empty for that label |

## Migration Plan

1. Ship curation YAML optional — empty file means current behavior.
2. Rebuild index + seed Qdrant; re-run retrieval pilot.
3. Update agent command docs (already partially done for observation-first order).
4. No migration of old eval runs; new fields appear on new runs only.

## Open Questions

- Whether to expose inspect CLI similarity for **query embed of a test photo** (requires OpenRouter key) vs manifest-only mode — default manifest-only, optional `--query-image` flag in tasks.
