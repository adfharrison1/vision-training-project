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
     - `top1_accuracy`, `top3_accuracy`, `observation_count`, `failure_count`
     - `failures[]`: `image`, `ground_truth`, `predicted`, `trace_id`, `observation_id`, `error`
     - `observations[]`: per-row `top1_match`, `top3_match`, `trace_id`
     - `per_class`: breakdown by species
   - Present: aggregate metrics, list of top-1 failures (ground truth vs predicted), and any identification errors

3. **Improvement-loop guidance**
   - Recommend changing **one variable** before the next run (prompt, model, temperature, manifest row, etc.)
   - Suggest a new `--eval-run-id` for the re-run
   - Point to `/eval-run` with the same profile unless the user wants smoke for a quick check

4. **Opik follow-up (optional)**
   - For failed rows with `trace_id`, recommend inspecting traces in the local Opik UI (`http://localhost:5173`) or via connected Opik tooling if available
   - For deep root-cause analysis, use the project's Opik diagnose/explain skills when installed — do not duplicate their logic here

5. **Output**
   - Cite the report file path
   - Keep the summary actionable: which species/images failed and what to inspect first
