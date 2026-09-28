---
name: "/eval-debug"
description: "Post-mortem eval failures using split metrics and failure forensics artifacts"
category: "Workflow"
---

Debug Oxford 102 eval failures using the aggregate report, split accuracy metrics, and per-image forensics JSON.

**Input**: Optional `eval-run-id` slug (e.g. `yellow16-no-reason`). If omitted, use the newest entry in `eval_runs/index.json` (or newest `eval_runs/*/eval/report.json` by mtime).

**When to use**

- After `/eval-run` when stderr `benchmark_misses=` is non-zero
- When `/eval-triage` lists failures from `failures[]`
- When comparing runs with different `PLANT_ID_VLM_CLOUD_REASONING_EFFORT` values

**Step 1 — Load the report**

Open `eval_runs/<eval-run-id>/eval/report.json` and read `eval_runs/<eval-run-id>/manifest.json` for `run_purpose`:

| Field | Meaning |
|---|---|
| `run_purpose` | Why this eval was run |
| **Benchmark misses** | `parse_failure_count + misclassification_count` (= `len(failures[])` when complete) |
| `top1_accuracy_all`, `top3_accuracy_all` | Accuracy over **every** profile image |
| `top1_accuracy`, `top3_accuracy` | Accuracy on **successful** parses only |
| `parse_failure_count` | Identification/parsing errors (`error` set on the row) |
| `misclassification_count` | Parsed OK but top-1 ≠ ground truth |
| `failure_count` | Parse errors only — **not** total benchmark failures |
| `success_count` | Valid parses — **not** “all correct” |
| `failure_artifacts_dir` | Forensics JSON for **every** benchmark miss |
| `failures[]` | Same set as benchmark misses: parse (`error`) or misclass (`error` null) |
| `inference` | Backend, model, prompt_version, token totals |

Always quote **both** `(success)` and `(all)` top-1 when summarizing — a run can show high `(success)` with a poor `(all)` when parse failures happened.

**Step 2 — Classify each failure**

Use `failures[]` (or `benchmark_misses` breakdown):

1. **Parse failure** (`error` non-null — e.g. `Unknown species_label`, rank validation)
   - Failure mode: invalid JSON, off-catalog label, or other identification error
   - Runtime may retry once when `PLANT_ID_INVALID_LABEL_RETRY_ENABLED=true` (default); eval still records the final outcome
2. **Misclassification** (`error` null, wrong top-1 in report / `failure_kind: misclassification` in forensics)
   - Failure mode: valid catalog JSON but wrong rank-1
   - Check `predictions` in forensics or `observations[]` for rank-2/3 hits

**Step 3 — Read failure forensics (all benchmark misses)**

For **each** row in `failures[]`, open:

```text
eval_runs/<eval-run-id>/eval/failures/<image_stem>.json
```

Each file includes:

- `failure_kind`: `parse` or `misclassification`
- `ground_truth`, `trace_id`, `observation_id`
- **Parse:** `error`, optional `invalid_species_label`
- **Misclass:** `predicted`, `predictions`, optional `top3_match` (no `error`)
- **Both:** `model.message_content`, optional `model.reasoning_content_preview`, retry fields when applicable

If files are missing for an older run, backfill from identify artifacts:

```bash
uv run python -m eval.sync_failure_forensics <eval-run-id>
```

Use forensics before Opik when you need exact model strings; local Opik LLM spans often store usage/metadata only.

**Step 4 — Optional Opik**

For rows with `trace_id`, open the local UI (`http://localhost:5173`, project `plant-id`) or Opik MCP `read('trace', id)`. Use Opik **explain/diagnose** skills for trace-level RCA; use forensics files for raw JSON and reasoning text.

**Step 5 — Recommend one next change**

Change **one variable** per iteration:

| Symptom | Likely lever |
|---|---|
| Off-catalog labels with `reasoning_effort=none` | Confirm invalid-label retry enabled; prompt v4 synonym hints; re-run same profile |
| primula ↔ fire lily with reasoning on | Set `PLANT_ID_VLM_CLOUD_REASONING_EFFORT=none`; use `primula_repeat10` probe |
| Persistent misclass on one species | Adjust manifest row in profile YAML or prompt disambiguation for that pair |
| Non-consecutive prediction ranks | Normalize ranks in parser (`vlm_common`); re-run same profile |

Suggest a new `--eval-run-id`, `--run-purpose`, and the same `--profile` unless smoke is enough.

**Output format**

1. Report path, `run_purpose`, **benchmark miss count**, and split metrics table
2. Failure list grouped: parse vs misclass (every `failures[]` row)
3. Forensics paths read (quote `message_content` / reasoning excerpt when useful)
4. Single recommended next experiment

**Related commands**

- `/eval-run` — start a run
- `/eval-triage` — quick summary and improvement-loop pointer (use `/eval-debug` for forensics)
