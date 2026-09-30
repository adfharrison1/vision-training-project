# retrieval-evaluation Specification

## Purpose

Run offline retrieval-quality benchmarks (Recall@K, MRR) with the same eval run layout as identification eval, plus failure forensics and agent commands for triage.

## Requirements

### Requirement: Retrieval-only evaluation runs

The project SHALL provide an offline retrieval evaluation entrypoint that reuses the eval run directory conventions (`eval_runs/{run_id}/`, manifest, purpose string, git commit metadata) and produces a structured report with Recall@K and MRR for ground-truth `catalog_label` presence in retrieved top-K, without invoking species identification.

#### Scenario: Backend comparison

- **WHEN** a maintainer runs retrieval eval twice with the same profile and different `--retrieval-backend` values
- **THEN** reports SHALL use the same schema so metrics are directly comparable

#### Scenario: Primary backend default

- **WHEN** retrieval eval runs without overriding backend
- **THEN** the default backend SHALL be `nemotron-prototype` (OpenRouter query embeddings against OpenRouter-built Qdrant prototypes)

Optional comparison backend **`describe-hybrid`** is documented for eval; it is not a replacement for OpenRouter prototype embeddings.

### Requirement: Retrieval failure forensics

When ground truth is not in top-K, the eval SHALL write forensics artifacts under `eval_runs/{run_id}/eval/failures/` including retrieved labels, scores, backend id, and embed model metadata sufficient for triage.

#### Scenario: Miss capture

- **WHEN** retrieval eval processes an image whose ground-truth species is not in top-K
- **THEN** a failure artifact SHALL be written and listed in the eval report failures collection

### Requirement: Agent commands for retrieval eval

The project SHALL document agent slash commands for starting retrieval eval, triaging retrieval misses, and debugging failure artifacts, parallel to existing VLM eval commands.

#### Scenario: Triage command

- **WHEN** an agent runs the retrieval triage command against a completed retrieval run id
- **THEN** it SHALL summarize misses and point to failure forensics paths

### Requirement: Retrieval eval documented in eval README

Retrieval evaluation entrypoints, profiles, backends, artifact layout, and triage workflow SHALL be documented in `eval/README.md` and cross-linked from the root README when shipped.

#### Scenario: New retrieval runner

- **WHEN** `run_retrieval_eval` (or equivalent module) is added
- **THEN** `eval/README.md` SHALL include example commands with `--eval-run-id`, `--run-purpose`, and `--retrieval-backend`
