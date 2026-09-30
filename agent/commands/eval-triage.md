---
name: "/eval-triage"
description: "Summarize eval report failures and suggest next improvement-loop steps"
category: "Workflow"
---

Triage an Oxford 102 eval report and suggest what to fix next.

**Input**: Optional `eval-run-id` slug (e.g. `prompt-v1-baseline`). If omitted, use the newest entry in `eval_runs/full_identify/index.json` (or the newest report under that tree if the index is missing).

**Steps**

1. **Locate report**
   - If an id was provided, open `eval_runs/full_identify/<eval-run-id>/eval/report.json` (and `eval_runs/full_identify/<eval-run-id>/manifest.json` for `run_purpose`)
   - Else read `eval_runs/full_identify/index.json` and pick the first entry, or scan for the newest report
   - If none exist, tell the user to run `/eval-run` first

2. **Read and summarize**
   - Parse the JSON report. Key fields:
     - `eval_run_id`, `run_purpose`, `profile`, `model_tag`, `backend`
     - **Benchmark misses (improvement loop):** `benchmark_misses = parse_failure_count + misclassification_count` — MUST equal `len(failures[])` when the report is complete
     - `top1_accuracy_all`, `top3_accuracy_all` — headline accuracy over **every** profile image (each benchmark miss counts as a miss)
     - `top1_accuracy`, `top3_accuracy` — on **successful parses only** (denominator excludes parse errors)
     - `parse_failure_count`, `misclassification_count` — breakdown of benchmark misses
     - `failure_count` — **parse errors only** (same as `parse_failure_count`); do **not** treat as total failures
     - `success_count` — observations that parsed OK (`error` null); **not** the same as “benchmark pass”
     - `failure_artifacts_dir` — per-image forensics JSON for **all** benchmark misses (parse + misclass)
     - `failures[]`: canonical triage list (`error` set → parse; else wrong top-1)
     - `observations[]`: per-row `top1_match`, `top3_match`, `trace_id`, `predictions`
     - `per_class`: breakdown by species
     - **Retrieval (if present):** analyze **`retrieval_observations[]` per image before** `retrieval.recall_at_k` / `retrieval.mrr`; macro metrics are run averages, not substitutes for per-query ranks
   - Lead the summary with **benchmark misses** and list every row in `failures[]`, grouped parse vs misclass
   - Then show split metrics `(success)` vs `(all)` for context

3. **Deep debug**
   - Run **`/eval-debug`** (same optional `eval-run-id`) for forensics JSON under `eval/failures/` and grouped RCA

4. **Improvement-loop guidance**
   - Recommend changing **one variable** before the next run (prompt, model, reasoning effort, manifest row, etc.)
   - Suggest a new `--eval-run-id` for the re-run
   - Point to `/eval-run` with the same profile unless the user wants smoke for a quick check

5. **Opik follow-up (optional)**
   - For failed rows with `trace_id`, recommend inspecting traces in the local Opik UI (`http://localhost:5173`) or via connected Opik tooling if available
   - For deep root-cause analysis, use the project's Opik diagnose/explain skills when installed — do not duplicate their logic here

6. **Output**
   - Cite `run_purpose`, manifest path, and report file path
   - Keep the summary actionable: which species/images failed and what to inspect first
