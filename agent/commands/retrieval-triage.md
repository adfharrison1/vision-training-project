# Summarize retrieval eval for a run id.

**Analysis order (required):** read **`retrieval_observations[]` per image first** (ground truth, `retrieved_labels`, `scores`, per-row `recall_at_k`, `reciprocal_rank`). Only then use **`retrieval.recall_at_k` / `retrieval.mrr`** as a run-level macro average for comparing runs — never lead with the mean on small profiles (e.g. `bolero_and_canterbury`).

**Report path:** `eval_runs/rag_retrieval_only/<id>/eval/report.json` (manifest: `run_purpose`).

**Steps**

1. List every `retrieval_observations[]` row: image stem, GT label, top‑K labels + scores, hit/miss at configured K.
2. List `failures[]` (GT not in top‑K) and point to `eval/failures/<stem>.json` when present.
3. Optionally cite macro `retrieval.recall_at_k` and `retrieval.mrr` as a single headline for index/history comparison.

```bash
# Replace RUN_ID — per-image first, then macro
python - <<'PY'
import json, sys
from pathlib import Path
p = Path("eval_runs/rag_retrieval_only/RUN_ID/eval/report.json")
r = json.loads(p.read_text())
print("run_purpose:", r.get("run_purpose"), "profile:", r.get("profile"))
for row in r.get("retrieval_observations") or []:
    stem = Path(row["image"]).stem
    print(stem, "GT=", row["ground_truth"], "top=", list(row.get("retrieved_labels") or []),
          "recall@", row.get("recall_at_k"), "RR=", row.get("reciprocal_rank"))
ret = r.get("retrieval") or {}
print("--- macro (after per-image) ---")
print("mrr", ret.get("mrr"), "recall_at_k", ret.get("recall_at_k"))
for f in r.get("failures") or []:
    print("failure", f)
PY
```

On **full identify** runs, use the same order on `retrieval_observations[]` / `retrieval` in `eval_runs/full_identify/<id>/eval/report.json` when debugging RAG or embedding quality (identify misses still come from `failures[]` / `/eval-debug`).
