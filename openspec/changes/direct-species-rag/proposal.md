> **Status:** SUPERSEDED by `openspec/changes/species-rag-retrieval/` — do not implement separately.

## Why

Species knowledge sheets (visual markers, confusion species) may improve local VLM accuracy. Direct lookup validates RAG value before vector DB complexity.

## Depends on

- `eval-dataset-baseline` — metrics to compare against

## Maps from

- Original roadmap Stage 5 (requirement RAG → species sheets)

## Decision gates (resolve before full planning)

- Species sheet YAML schema (Oxford 102 class → description, lookalikes)
- Source material for sheets (manual curation vs Wikipedia summaries)
- RAG injected in VLM repository / prompt builder only — not in classical ML repository

## What Changes (indicative)

- YAML species knowledge under `species/`
- Direct lookup by class name
- A/B eval: no context vs species sheet context

## Planned capabilities (subject to change)

- `species-knowledge` — structured species documents
- `species-retrieval` — direct lookup (no embeddings)

## Non-goals (indicative)

- Vector DB, Pl@ntNet at runtime, fine-tuning

## Impact

- TBD at planning time
