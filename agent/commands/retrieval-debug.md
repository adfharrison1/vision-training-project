# Post-mortem retrieval misses for a run id.

Inspect `eval_runs/<id>/eval/failures/*.json` for retrieved labels, scores, and backend metadata.

```bash
ls eval_runs/RUN_ID/eval/failures/
```

Compare with per-image artifacts in `eval_runs/RUN_ID/artifacts/`.
