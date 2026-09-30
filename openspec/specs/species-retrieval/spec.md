# species-retrieval Specification

## Purpose

Retrieve ranked species knowledge sheets from user photos using OpenRouter multimodal embeddings, a local Qdrant prototype index built from git sheets, and swappable retrieval backends for eval comparison.

## Requirements

### Requirement: Species retrieval repository port

The domain layer SHALL define a swappable port (e.g. `SpeciesRetrievalRepository`) that accepts observation photo paths and returns ranked species sheet context for top-K `catalog_label` values without using ground-truth labels or closed-set identify output as the query.

#### Scenario: No ground truth in query

- **WHEN** retrieval runs for a benchmark or user photo
- **THEN** the query SHALL be derived only from the photo(s) and configured retrieval backend, not from known species labels

### Requirement: Multi-prototype vector index

The indexing pipeline SHALL store multiple embedding prototypes per species using **OpenRouter multimodal embeddings**: text prototype(s) from `retrieval_text` and image prototypes from configured reference images (e.g. Oxford train images, capped per species). Query ranking SHALL aggregate prototype scores per `catalog_label` (default: maximum similarity).

#### Scenario: Multiple image prototypes

- **WHEN** the index is built for a species with N reference images
- **THEN** at least N image prototype vectors SHALL be associated with that `catalog_label` in the vector store

#### Scenario: OpenRouter index build

- **WHEN** a maintainer runs the documented index build
- **THEN** vectors SHALL be produced via OpenRouter `/embeddings` using `PLANT_ID_VLM_OPENROUTER_API_KEY` and the configured embed model id

### Requirement: Local Qdrant with git-seeded content

The project SHALL provide Docker Compose (or equivalent) for local Qdrant and a seed workflow that upserts points from built embedding artifacts derived from git sheets. Vector store access SHALL live in infrastructure and be swappable behind the retrieval port.

#### Scenario: Seed from build artifacts

- **WHEN** a maintainer runs the documented seed command after building the retrieval index
- **THEN** Qdrant SHALL contain upserted points whose payloads include `catalog_label` and sheet text fields needed for retrieval and downstream inject

### Requirement: Swappable retrieval backends

Composition SHALL wire retrieval backends via settings or CLI:

- **nemotron-prototype** (default) — OpenRouter image embedding against stored OpenRouter prototypes in Qdrant
- **describe-hybrid** (optional comparison) — neutral flower description via VLM, combined BM25 and text-embedding similarity over sheet text (no OpenRouter query embed)

#### Scenario: Primary backend selection

- **WHEN** retrieval is invoked with default settings or backend `nemotron-prototype`
- **THEN** the infrastructure implementation SHALL embed the query photo via OpenRouter and search Qdrant prototypes built with OpenRouter

#### Scenario: Describe hybrid backend

- **WHEN** retrieval is invoked with backend `describe-hybrid`
- **THEN** the implementation SHALL use a neutral describe prompt (no catalog species selection), then rank sheets using both lexical (BM25) and semantic text embedding signals

### Requirement: No local CLIP prototype path

The project SHALL NOT provide local CLIP/open-clip prototype indexing or retrieval. Prototype embeddings SHALL use OpenRouter only.

#### Scenario: Index build uses OpenRouter only

- **WHEN** a maintainer runs the documented retrieval index build
- **THEN** the pipeline SHALL NOT invoke local CLIP or open-clip encoders

### Requirement: No alternate embedding vendors in runtime

Fireworks or other cloud **`/embeddings`** endpoints SHALL NOT be integrated into the runtime retrieval or index build path. Exploratory probe scripts in `eval/` are permitted and are not runtime.

#### Scenario: Runtime retrieval path

- **WHEN** prototype index build or `nemotron-prototype` retrieval runs in production code paths
- **THEN** embeddings SHALL be requested only from the configured OpenRouter API

### Requirement: Optional curated train prototypes for index build

The retrieval index build entrypoint SHALL support an optional curated list of prototype images per `catalog_label` (validated on Oxford **train** split, same rules as automatic train prototype selection) used instead of the first-N train scan when configured for a species.

#### Scenario: Pilot campanula pair

- **WHEN** a maintainer lists curated train images for `bolero deep blue` and `canterbury bells`
- **THEN** built index manifest points SHALL reference those paths as `prototype_kind=image` with stable `prototype_id`s

#### Scenario: Test split rejected

- **WHEN** a curated path resolves to a test-split image
- **THEN** index build SHALL fail with an explicit error (no test leakage)

#### Scenario: Fallback

- **WHEN** no curation is configured for a species with a sheet
- **THEN** index build SHALL retain first-N train behavior up to `retrieval_max_prototypes_per_species`
