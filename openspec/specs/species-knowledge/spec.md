# species-knowledge Specification

## Purpose

Maintain a git-versioned corpus of species knowledge sheets (YAML) and eval tooling to draft sheets from reference photos using the configured cloud VLM, without storing vectors in source control.

## Requirements

### Requirement: Species sheet corpus in source control

The project SHALL maintain species knowledge sheets as YAML under `resources/species_sheets/` with at least `catalog_label`, `retrieval_text`, and `context_block`. The `catalog_label` SHALL match an entry in the closed-set species catalog.

#### Scenario: Species-centric retrieval text

- **WHEN** a sheet is authored or synthesised
- **THEN** `retrieval_text` SHALL describe typical plant morphology and disambiguating traits, not a specific benchmark photograph, dataset name, or framing language

### Requirement: VLM-assisted sheet synthesis

The project SHALL provide an eval/dev script that accepts multiple image paths for one species and produces a draft YAML sheet using the configured OpenAI-compatible cloud VLM settings (`vlm_cloud_*`), without writing embeddings or vectors into the sheet file.

#### Scenario: Multi-image synthesis

- **WHEN** a maintainer runs the synthesis script with two or more images for one `catalog_label`
- **THEN** the script SHALL emit YAML containing `retrieval_text` and `context_block` suitable for human review before commit

#### Scenario: No vectors in sheet source

- **WHEN** sheet YAML is committed to git
- **THEN** it SHALL NOT contain embedding vectors or Qdrant point ids
