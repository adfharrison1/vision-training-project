> **Status:** SUPERSEDED by `openspec/changes/species-rag-retrieval/` — do not implement separately.

## Why

If direct species-sheet lookup proves valuable, embedding-based retrieval scales to larger or less structured species knowledge libraries and enables separate measurement of retrieval quality vs vision quality.

## Depends on

- `direct-species-rag` — confirmed that species context helps downstream identification
- `eval-dataset-baseline` — metrics framework for end-to-end comparison

## Maps from

- `initial_extenal_dev_spec.md` — Stage 6 (Semantic Retrieval and Vector Search)

## Decision gates (resolve before full planning)

- Local Qdrant vs alternative vector store
- Embedding model choice (`sentence-transformers` and variant)
- Index storage location and rebuild strategy
- Separate retrieval eval suite (Recall@k, MRR) before trusting end-to-end numbers
- Docker Compose scope for local Qdrant

## What Changes (indicative)

- Local Qdrant instance (likely Docker Compose)
- Species knowledge indexing pipeline with local embedding model
- Semantic retrieval consumed by VLM repository / prompt builder in infrastructure — not by classical ML repository
- Semantic retrieval interface (domain or infrastructure port as decided at planning time)
- Retrieval evaluation metrics separate from vision metrics

## Planned capabilities (subject to change)

- `vector-retrieval` — embedding, indexing, semantic search
- `retrieval-evaluation` — retrieval-quality metrics independent of VLM

## Non-goals (indicative)

- Fine-tuning
- Cloud-hosted vector DB
- Langfuse / DeepEval (deferred to improvement-loop change)

## Impact

- TBD at planning time
