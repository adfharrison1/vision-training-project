## ADDED Requirements

### Requirement: Optional RAG context injection

When species retrieval is enabled at composition time, the identification path SHALL append retrieved species `context_block` text to the VLM prompt in infrastructure, without changing `IdentifyPlantUseCase` inputs or domain rules.

#### Scenario: RAG disabled default

- **WHEN** RAG is not enabled in settings
- **THEN** identification behavior SHALL match the pre-RAG prompt and repository path

#### Scenario: RAG enabled

- **WHEN** RAG is enabled and retrieval returns top-K sheets
- **THEN** the VLM prompt SHALL include formatted context derived from those sheets while the model still selects `species_label` only from the allowed catalog list
