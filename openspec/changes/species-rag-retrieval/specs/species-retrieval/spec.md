## ADDED Requirements

### Requirement: Species retrieval repository port

The domain layer SHALL define a swappable port (e.g. `SpeciesRetrievalRepository`) that accepts observation photo paths and returns ranked species sheet context for top-K `catalog_label` values without using ground-truth labels or closed-set identify output as the query.

#### Scenario: No ground truth in query

- **WHEN** retrieval runs for a benchmark or user photo
- **THEN** the query SHALL be derived only from the photo(s) and configured retrieval backend, not from known species labels

### Requirement: Multi-prototype vector index

The indexing pipeline SHALL store multiple embedding prototypes per species (at minimum CLIP image prototypes from configured reference images and CLIP text prototypes from `retrieval_text`). Query ranking SHALL aggregate prototype scores per `catalog_label` (default: maximum similarity).

#### Scenario: Multiple image prototypes

- **WHEN** the index is built for a species with N reference images
- **THEN** at least N image prototype vectors SHALL be associated with that `catalog_label` in the vector store

### Requirement: Local Qdrant with git-seeded content

The project SHALL provide Docker Compose (or equivalent) for local Qdrant and a seed workflow that upserts points from built embedding artifacts derived from git sheets. Vector store access SHALL live in infrastructure and be swappable behind the retrieval port.

#### Scenario: Seed from build artifacts

- **WHEN** a maintainer runs the documented seed command after building the retrieval index
- **THEN** Qdrant SHALL contain upserted points whose payloads include `catalog_label` and sheet text fields needed for retrieval and downstream inject

### Requirement: Swappable retrieval backends

Composition SHALL wire one of at least two retrieval backends via settings or CLI, analogous to identification backend selection:

- **clip-prototype** — CLIP image embedding against stored prototypes
- **describe-hybrid** — neutral flower description via VLM, combined BM25 and text-embedding similarity over sheet text

#### Scenario: Backend selection

- **WHEN** retrieval is invoked with backend `clip-prototype`
- **THEN** the infrastructure implementation SHALL NOT call a generative describe model for the query

#### Scenario: Describe hybrid backend

- **WHEN** retrieval is invoked with backend `describe-hybrid`
- **THEN** the implementation SHALL use a neutral describe prompt (no catalog species selection), then rank sheets using both lexical (BM25) and semantic text embedding signals
