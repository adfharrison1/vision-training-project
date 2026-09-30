# Summarize retrieval eval for a run id.

**Analysis order (required):** read **`retrieval_observations[]` per image first** (ground truth, `retrieved_labels`, `scores`, per-row `recall_at_k`, `reciprocal_rank`, **`winning_prototypes`** when present). Then **`retrieval_per_class`** for per-label Recall@K on small profiles. Only then use **`retrieval.recall_at_k` / `retrieval.mrr`** as run-level macro averages — never lead with the mean on `bolero_and_canterbury`.

**Report path:** `eval_runs/rag_retrieval_only/<id>/eval/report.json` (manifest: `run_purpose`).

**Steps**

1. List every `retrieval_observations[]` row: image stem, GT label, top‑K labels + scores, winning prototypes, hit/miss at configured K.
2. Summarize **`retrieval_per_class`** (one line per ground-truth label).
3. List `failures[]` (GT not in top‑K) and point to `eval/failures/<stem>.json` when present.
4. Optionally cite macro `retrieval.recall_at_k` and `retrieval.mrr` for index/history comparison.

```bash
# Replace RUN_ID — per-image first, then per-class, then macro
python - <<'PY'
import json, sys
from pathlib import Path
p = Path("eval_runs/rag_retrieval_only/RUN_ID/eval/report.json")
r = json.loads(p.read_text())
print("run_purpose:", r.get("run_purpose"), "profile:", r.get("profile"))
for row in r.get("retrieval_observations") or []:
    stem = Path(row["image"]).stem
    print(stem, "GT=", row["ground_truth"], "top=", list(row.get("retrieved_labels") or []),
          "winners=", row.get("winning_prototypes"), "recall@", row.get("recall_at_k"))
for label, stats in (r.get("retrieval_per_class") or {}).items():
    print("per_class", label, stats)
ret = r.get("retrieval") or {}
print("--- macro (last) ---")
print("mrr", ret.get("mrr"), "recall_at_k", ret.get("recall_at_k"))
for f in r.get("failures") or []:
    print("failure", f)
PY
```

**Tuning loop:** `resources/species_sheets/prototypes.yaml` → `eval.build_retrieval_index` → Qdrant seed → `eval.inspect_retrieval_index --profile bolero_and_canterbury` → re-run retrieval eval.

On **full identify** runs, use the same order on `retrieval_observations[]` / `retrieval_per_class` / `retrieval` in `eval_runs/full_identify/<id>/eval/report.json` when debugging embedding quality (identify misses still come from `failures[]` / `/eval-debug`).
