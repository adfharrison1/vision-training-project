## ADDED Requirements

### Requirement: Retrieval eval agent commands with prototype debug

The project SHALL document agent slash commands for retrieval eval such that **retrieval-debug** and **retrieval-triage** workflows inspect per-image observations and prototype-winning metadata before macro Recall@K/MRR, and reference the curated-index rebuild loop when tuning the pilot profile.

#### Scenario: Debug command

- **WHEN** an agent follows retrieval-debug for a run id
- **THEN** instructions SHALL include reading prototype fields in artifacts/report and comparing to `artifacts/retrieval_index` manifest entries

#### Scenario: Index rebuild reminder

- **WHEN** an agent recommends sheet or prototype changes
- **THEN** commands or eval README links SHALL remind: `build_retrieval_index` → Qdrant seed → `run_retrieval_eval --profile bolero_and_canterbury`
