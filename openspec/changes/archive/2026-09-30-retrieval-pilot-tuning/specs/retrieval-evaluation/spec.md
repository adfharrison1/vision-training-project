## ADDED Requirements

### Requirement: Prototype-level retrieval debug in eval artifacts

Retrieval eval and full-identify eval reports SHALL expose, for each scored query image, which **index prototype(s)** determined the species-level score (at minimum the winning prototype per retrieved `catalog_label`: `prototype_kind`, `prototype_id`, optional `source_image`, and score).

#### Scenario: Canterbury confuser post-mortem

- **WHEN** a maintainer debugs a retrieval miss on `bolero_and_canterbury`
- **THEN** eval artifacts or report rows SHALL identify whether bolero won via a **text** or **image** prototype and which `source_image` (if any) was used

#### Scenario: No runtime identify call

- **WHEN** retrieval-only eval runs
- **THEN** prototype debug metadata SHALL be collected without invoking species identification

### Requirement: Per–ground-truth retrieval summary

Eval reports SHALL include additive per–ground-truth retrieval statistics (e.g. hit rate at configured K per distinct `catalog_label` in the profile) in addition to macro `retrieval.recall_at_k` and `retrieval.mrr`.

#### Scenario: Two-image pilot

- **WHEN** profile `bolero_and_canterbury` completes
- **THEN** the report SHALL make it obvious which of the two labels failed Recall@1 without inferring from macro averages alone

### Requirement: Analysis order in agent retrieval triage

Agent retrieval triage and debug commands SHALL instruct readers to inspect **per-image** `retrieval_observations[]` (and prototype debug when present) **before** citing macro retrieval metrics.

#### Scenario: Triage command

- **WHEN** an agent runs retrieval triage on a completed run under `eval_runs/rag_retrieval_only/`
- **THEN** the workflow SHALL list each observation’s ranks/scores first, then macro `retrieval` summary

## MODIFIED Requirements

### Requirement: Retrieval failure forensics

When ground truth is not in top-K, the eval SHALL write forensics artifacts under `eval_runs/{run_id}/eval/failures/` including retrieved labels, scores, backend id, embed model metadata, and **winning prototype metadata per retrieved label** sufficient for triage.

#### Scenario: Miss capture

- **WHEN** retrieval eval processes an image whose ground-truth species is not in top-K
- **THEN** a failure artifact SHALL be written and listed in the eval report failures collection, with prototype-level detail when the backend is `nemotron-prototype`
