# Summarize retrieval eval misses for a run id.

Read `eval_runs/<id>/eval/report.json` and list `failures[]` with paths under `eval/failures/`.

```bash
# Replace RUN_ID
cat eval_runs/RUN_ID/eval/report.json | python -c "import json,sys; r=json.load(sys.stdin); print('mrr', r.get('mrr')); print('recall', r.get('recall_at_k')); [print(f) for f in r.get('failures',[])]"
```
