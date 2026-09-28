## Why

Closed-set VLM identify struggles on visually similar Oxford 102 species (e.g. campanula confusions) without species-specific disambiguation context. We need **production-honest RAG**: retrieve species sheets from the user photo (or a neutral description) **without** ground truth or a prior identify pass, measure **retrieval quality separately** from top-1/top-3, then optionally inject context into the existing identify flow.

This change **supersedes and merges** the placeholder changes `direct-species-rag` and `vector-retrieval` into one incremental program.

## What Changes

- **Species sheet corpus** in git (`resources/species_sheets/`) — YAML with species-centric `retrieval_text` and VLM-only `context_block` (no vectors in source).
- **Authoring script** (eval/dev tooling): synthesise sheets from **multiple Oxford images per species** via the existing **Fireworks / `vlm-cloud` OpenAI-compatible client** (same settings as identify); human review before merge.
- **Index pipeline**: multi-**prototype** embeddings per species — CLIP image vectors from labelled train (or configured) images **plus** CLIP text vector(s) from `retrieval_text`; aggregate per-species score at query time (e.g. max over prototypes).
- **Local Qdrant** via Docker Compose (pattern like Opik: `docker/qdrant/` + `scripts/qdrant.sh`); **seed** collections from git sheets + built embedding artifacts on `up`/`seed` (not hand-editing the DB).
- **Swappable retrieval port** in domain/infrastructure (mirror `IdentificationRepository` pattern): backends **`clip-prototype`**, **`describe-text`** (neutral cloud/local VLM caption + **BM25 + text embedder** hybrid over sheet text).
- **Retrieval-only eval** with **`eval_runs/`-style layout**: run id, purpose, manifest, report, per-image artifacts, failure forensics when GT species not in top-K; agent commands for triage/debug.
- **Phase 2 (same change, later tasks)**: wire retrieved sheets into identify prompt augmentation (A/B vs no-RAG end-to-end eval).
- **Documentation**: keep root `README.md`, `eval/README.md`, corpus `resources/species_sheets/README.md`, and `agent/commands/README.md` (when commands ship) aligned with commands, env vars, and workflows introduced by this change.

## Capabilities

### New capabilities

- `species-knowledge` — sheet schema, git corpus, VLM authoring script
- `species-retrieval` — Qdrant-backed index, seed pipeline, swappable retrieval repositories
- `retrieval-evaluation` — offline Recall@K / MRR runs, forensics, agent commands

### Modified capabilities

- `species-identification` — optional RAG context injection at composition/prompt layer (identify use case unchanged)
- `evaluation-metrics` — retrieval metrics and report fields distinct from misclassification
- `local-dev-environment` — Qdrant compose, verify-env hooks, seed workflow
- `application-architecture` — new retrieval repository port and composition wiring

## Decision gates (locked for planning)

| Topic | Decision |
|-------|----------|
| Sheet content | Species-centric text; no eval photo framing or dataset names in `retrieval_text` |
| Prototypes | **Multi-prototype from day one** (multiple image embeddings + text per species) |
| Source of truth | Git YAML seeds DB; embeddings are **build artifacts** consumed by seed (regenerate when sheets/images change) |
| Vector store | **Qdrant** local Docker first; infrastructure **port** so store is swappable |
| Retrieval backends | **Both** CLIP-prototype and describe+BM25+text-embed in one change; **one eval runner**, `--retrieval-backend` switch |
| Identify augment | After retrieval eval proves Recall@K; same cloud/local VLM stack as today |
| Documentation | **All relevant READMEs** stay accurate as each phase lands (not a final doc dump only) |

## Non-goals

- Pl@ntNet or other external **identification** APIs in the runtime path
- Fine-tuning CLIP or VLM
- Cloud-hosted Qdrant
- Replacing closed-set allowed catalog with “retrieved labels only” (inject is hints only unless a later experiment says otherwise)
- Direct lookup by ground-truth class name (eval cheat)

## Dependencies

- `eval-dataset-baseline` — Oxford 102 paths, profiles (`curated48`), `eval_runs/` layout
- `vlm-cloud-backend` (archived) — Fireworks client/settings for authoring and optional describe backend

## Impact

- New dependencies: Qdrant client, CLIP/`open_clip` (or equivalent), sentence-transformers (text embedder), BM25 library (e.g. rank-bm25)
- New `docker/qdrant/`, `eval/` retrieval runner and forensics, `resources/species_sheets/`
- `openspec/config.yaml` planned sequence: replace stubs 5–6 with this change
- **Note:** Root OpenSpec context still says “no cloud LLMs at runtime”; this repo already supports **`vlm-cloud` identify**. This change treats **describe** and **sheet authoring** as the same swappable cloud/local pattern; update main context in a follow-up doc pass if we formalise that.

## Impact (systems)

- Opik: optional traces on describe/author VLM calls (infrastructure only)
- Classical ML backend: no retrieval injection in v1 tasks
