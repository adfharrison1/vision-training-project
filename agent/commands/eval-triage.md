---
name: "/eval-triage"
description: "Summarize eval report failures and suggest next improvement-loop steps"
category: "Workflow"
---

Triage an Oxford 102 eval report and suggest what to fix next.

**Input**: Optional `eval-run-id` slug (e.g. `prompt-v1-baseline`). If omitted, use the most recent JSON report under `artifacts/eval/` (by file modification time).

**Steps**

1. **Locate report**
   - If an id was provided, find `artifacts/eval/*-<eval-run-id>.json`
   - Else pick the newest `artifacts/eval/*.json`
   - If none exist, tell the user to run `/eval-run` first

2. **Read and summarize**
   - Parse the JSON report. Key fields:
     - `eval_run_id`, `profile`, `model_tag`, `backend`
     - `top1_accuracy`, `top3_accuracy` — on **successful** parses only
     - `top1_accuracy_all`, `top3_accuracy_all` — over **all** profile images
     - `parse_failure_count`, `misclassification_count`, `failure_count`
     - `failure_artifacts_dir` — forensics JSON when parse failures occurred
     - `failures[]`: `image`, `ground_truth`, `predicted`, `trace_id`, `observation_id`, `error`
     - `observations[]`: per-row `top1_match`, `top3_match`, `trace_id`, `predictions`
     - `per_class`: breakdown by species
   - Present: split metrics (success vs all), parse failures vs misclassifications separately

3. **Deep debug (optional)**
   - For parse failures or when the user wants model text, run **`/eval-debug`** (same optional `eval-run-id`) instead of duplicating its workflow here

4. **Improvement-loop guidance**
   - Recommend changing **one variable** before the next run (prompt, model, reasoning effort, manifest row, etc.)
   - Suggest a new `--eval-run-id` for the re-run
   - Point to `/eval-run` with the same profile unless the user wants smoke for a quick check

5. **Opik follow-up (optional)**
   - For failed rows with `trace_id`, recommend inspecting traces in the local Opik UI (`http://localhost:5173`) or via connected Opik tooling if available
   - For deep root-cause analysis, use the project's Opik diagnose/explain skills when installed — do not duplicate their logic here

6. **Output**
   - Cite the report file path
   - Keep the summary actionable: which species/images failed and what to inspect first
