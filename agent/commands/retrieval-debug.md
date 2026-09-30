# Post-mortem retrieval eval (per-image first).

**Input:** retrieval run id under `eval_runs/rag_retrieval_only/<id>/`.

**Analysis order (required)**

1. **`eval/report.json` → `retrieval_observations[]`** — for each image: GT vs ranked `retrieved_labels`, scores, per-row `recall_at_k`, `reciprocal_rank`. This is the primary signal for embedding/index iteration (especially on `bolero_and_canterbury`).
2. **`artifacts/<stem>.json`** — same retrieval payload persisted per query; use when you need the full retrieved list beyond report truncation.
3. **`eval/failures/<stem>.json`** — only for top‑K misses; includes failure reason and retrieved list.
4. **`retrieval` macro block last** — `recall_at_k` / `mrr` are means over observations; use for run-to-run comparison, not for explaining a single confuser pair.

```bash
RUN_ID=bolero-canterbury-pilot
# Per-image report rows
python - <<'PY'
import json
from pathlib import Path
r = json.loads(Path(f"eval_runs/rag_retrieval_only/{RUN_ID}/eval/report.json").read_text())
for row in r["retrieval_observations"]:
    print(Path(row["image"]).name, row["ground_truth"], "->", row["retrieved_labels"], row["scores"])
PY
ls eval_runs/rag_retrieval_only/$RUN_ID/eval/failures/
ls eval_runs/rag_retrieval_only/$RUN_ID/artifacts/
```

**Output:** one paragraph per observation (what ranked where, score gap), then macro metrics, then one suggested next change (index rebuild, sheet text, prototype images, etc.).
