# Local Qdrant for species retrieval

Prototype vectors are built with **OpenRouter** multimodal embeddings (see root README).

Run from the repository root:

```bash
export PLANT_ID_VLM_OPENROUTER_API_KEY=...   # required for index build (default provider)
./scripts/qdrant.sh up
./scripts/qdrant.sh health
uv run python -m eval.build_retrieval_index
./scripts/qdrant.sh seed
```

Environment (see `.env.example`):

- `PLANT_ID_VLM_OPENROUTER_API_KEY` — OpenRouter API key for index build and `nemotron-prototype` retrieval
- `PLANT_ID_QDRANT_URL` — default `http://127.0.0.1:6333`
- `PLANT_ID_QDRANT_COLLECTION` — default `species_sheets_v1`

## Troubleshooting

- **Connection refused:** run `./scripts/qdrant.sh up` and wait for the healthcheck.
- **Index build fails on API key:** set `PLANT_ID_VLM_OPENROUTER_API_KEY` (not the Fireworks identify key).
- **Seed fails with missing manifest:** build the index first (`eval.build_retrieval_index`).
- **Collection dimension mismatch:** drop the collection (`./scripts/qdrant.sh down -v`) and re-seed after rebuilding the index.
