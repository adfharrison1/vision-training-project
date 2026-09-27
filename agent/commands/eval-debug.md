---
name: "/eval-debug"
description: "Post-mortem eval failures using split metrics and failure forensics artifacts"
category: "Workflow"
---

Debug Oxford 102 eval failures using the aggregate report, split accuracy metrics, and per-image forensics JSON.

**Input**: Optional `eval-run-id` slug (e.g. `yellow16-no-reason`). If omitted, use the most recent report under `artifacts/eval/` (by modification time).

**When to use**

- After `/eval-run` when `parse_failures` or `misclass` in the stderr summary is non-zero
- When `/eval-triage` points at identification errors or wrong top-1 labels
- When comparing runs with different `PLANT_ID_VLM_CLOUD_REASONING_EFFORT` values

**Step 1 — Load the report**

Find `artifacts/eval/*-<eval-run-id>.json` and read:

| Field | Meaning |
|---|---|
| `top1_accuracy`, `top3_accuracy` | Accuracy on **successful** parses only (legacy headline) |
| `top1_accuracy_all`, `top3_accuracy_all` | Accuracy over **every** profile image (parse failures count as misses) |
| `parse_failure_count` | Rows where identification raised an error (e.g. `Unknown species_label`) |
| `misclassification_count` | Parsed OK but top-1 ≠ ground truth |
| `failure_artifacts_dir` | Directory of forensics JSON when parse failures occurred |
| `failures[]` | Top-1 misses **and** parse errors (`error` set) |
| `inference` | Backend, model, prompt_version, token totals |

Always quote **both** `(success)` and `(all)` top-1 when summarizing — a run can show `top1_accuracy=1.0` with a poor `top1_accuracy_all` if parse failures happened.

**Step 2 — Classify each failure**

1. **Parse failure** (`error` contains `Unknown species_label` or other `IdentificationError` text)
   - Failure mode: model emitted a label **outside** `resources/species_catalog/default.txt`
   - Runtime may retry once when `PLANT_ID_INVALID_LABEL_RETRY_ENABLED=true` (default); eval still records the final outcome
2. **Misclassification** (`error` is null, `top1_match` false)
   - Failure mode: valid catalog JSON but wrong rank-1 (often reasoning-heavy confusions, e.g. primula → fire lily)
   - Check `predictions` in `observations[]` for rank-2/3 hits

**Step 3 — Read failure forensics (parse failures only)**

For each parse failure, open:

```text
artifacts/eval/<eval-run-id>/failures/<image_stem>.json
```

Each file includes:

- `error`, `invalid_species_label` (when applicable), `ground_truth`, `trace_id`
- `model.message_content` — visible JSON from the API
- `model.reasoning_content_preview` — truncated hidden reasoning when the provider returned it
- `model.invalid_label_retry_message_content` — second attempt after catalog retry (if triggered)

Use this before Opik when you need the exact model strings; local Opik LLM spans often store usage/metadata only.

**Step 4 — Optional Opik**

For rows with `trace_id`, open the local UI (`http://localhost:5173`, project `plant-id`) or Opik MCP `read('trace', id)`. Use Opik **explain/diagnose** skills for trace-level RCA; use forensics files for raw JSON and reasoning text.

**Step 5 — Recommend one next change**

Change **one variable** per iteration:

| Symptom | Likely lever |
|---|---|
| Off-catalog labels with `reasoning_effort=none` | Confirm invalid-label retry enabled; prompt v4 synonym hints; re-run same profile |
| primula ↔ fire lily with reasoning on | Set `PLANT_ID_VLM_CLOUD_REASONING_EFFORT=none`; use `primula_repeat10` probe |
| Persistent misclass on one species | Adjust manifest row in profile YAML or prompt disambiguation for that pair |

Suggest a new `--eval-run-id` and the same `--profile` unless smoke is enough.

**Output format**

1. Report path and split metrics table
2. Failure list grouped: parse vs misclass
3. Forensics paths read (quote `message_content` / reasoning excerpt when useful)
4. Single recommended next experiment

**Related commands**

- `/eval-run` — start a run
- `/eval-triage` — quick summary and improvement-loop pointer (use `/eval-debug` for deep forensics)
