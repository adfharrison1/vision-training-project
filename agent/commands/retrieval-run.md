# Start a retrieval-only eval run (background-friendly).

```bash
uv run python -m eval.run_retrieval_eval \
  --profile bolero_and_canterbury \
  --retrieval-backend nemotron-prototype \
  --eval-run-id retrieval-bolero-canterbury \
  --run-purpose "pilot pair retrieval check"
```

Requires Qdrant seeded for `nemotron-prototype`. Set `PLANT_ID_VLM_OPENROUTER_API_KEY` for index build/query. Use `describe-hybrid` without Qdrant (git sheets + cloud describe).
