# Post-mortem retrieval eval (per-image first).

**Input:** retrieval run id under `eval_runs/rag_retrieval_only/<id>/`.

**Analysis order (required)**

1. **`eval/report.json` → `retrieval_observations[]`** — for each image: GT vs ranked `retrieved_labels`, scores, per-row `recall_at_k`, `reciprocal_rank`, and when present **`winning_prototypes`** / **`raw_hits`** (which prototype kind/id/source_image scored before species aggregation).
2. **`retrieval_per_class`** — per ground-truth label Recall@K (readable on two-image pilots); macro `retrieval.recall_at_k` last among summary stats.
3. **`artifacts/<stem>.json`** — same retrieval payload persisted per query; use when you need the full retrieved list beyond report truncation.
4. **`eval/failures/<stem>.json`** — only for top‑K misses; includes failure reason, retrieved list, and prototype debug when available.
5. **`retrieval` macro block last** — `recall_at_k` / `mrr` are means over observations; use for run-to-run comparison, not for explaining a single confuser pair.

```bash
RUN_ID=bolero-canterbury-pilot
# Per-image report rows
python - <<'PY'
import json
from pathlib import Path
r = json.loads(Path(f"eval_runs/rag_retrieval_only/{RUN_ID}/eval/report.json").read_text())
for row in r["retrieval_observations"]:
    winners = row.get("winning_prototypes") or []
    print(Path(row["image"]).name, row["ground_truth"], "->", row["retrieved_labels"], winners)
PY
ls eval_runs/rag_retrieval_only/$RUN_ID/eval/failures/
ls eval_runs/rag_retrieval_only/$RUN_ID/artifacts/
```

**Index curation loop:** edit `resources/species_sheets/prototypes.yaml` and/or sheet `retrieval_text` → `uv run python -m eval.build_retrieval_index` → `./scripts/qdrant.sh seed` → `uv run python -m eval.inspect_retrieval_index --profile bolero_and_canterbury` → re-run retrieval eval.

**Output:** one paragraph per observation (what ranked where, which prototype won, score gap), then per-class and macro metrics, then one suggested next change (index rebuild, sheet text, prototype images, etc.).
