---
name: "/eval-run"
description: "Start an Oxford 102 eval run with project defaults"
category: "Workflow"
---

Start an Oxford 102 benchmark eval for the plant-id improvement loop.

**Input**: Optional trailing arguments: `[profile] [eval-run-id]`. Default profile is `quick` (8 manifest observations). Examples: `/eval-run`, `/eval-run smoke`, `/eval-run quick prompt-v1-baseline`.

**Steps**

1. **Parse arguments**
   - Profile: first arg if it is `smoke`, `quick`, or `full`; else default `quick`
   - `--eval-run-id`: second arg, or first arg if profile omitted; if still missing, generate a slug like `quick-YYYYMMDD-HHMM`

2. **Required run purpose**
   - Before starting, obtain a **non-empty** `--run-purpose` from the developer (why this eval exists — prompt change, regression check, etc.).

3. **Guardrail: full profile**
   - If profile is `full` (~6,149 test images), STOP and ask the user to confirm explicitly before proceeding. Do not start without confirmation.

4. **Prerequisites**
   - Verify Oxford 102 dataset exists under `data/flowers/` (`jpg/`, `imagelabels.mat`, `setid.mat`). If missing, stop and point to README dataset download instructions.
   - Confirm Ollama is expected to be running when using `--backend vlm` (default eval backend is `vlm-cloud`).

5. **Opik tracing (recommended for improvement loops)**
   - Check whether local Opik is reachable (`./scripts/opik.sh status` or HTTP check to `http://127.0.0.1:5173`).
   - If Opik is down, offer to run `/opik-up` first.
   - For traced runs, set `PLANT_ID_OPIK_ENABLED=true` in the eval shell environment. Do not call `opik.configure()` from plant-id code paths.
   - Do not set `OPIK_API_KEY` (local self-hosted only).

6. **Run eval**
   - Command:
     ```bash
     uv run python -m eval.run_oxford102 --profile <profile> --eval-run-id <id> --run-purpose "<purpose>"
     ```
   - Optional: `--think` / `--no-think` for this run (default `false`; env `PLANT_ID_OLLAMA_THINK`).
   - Run as a **background/long-running process** (~14 min for `smoke`, ~30 min for `quick` on qwen3-vl:2b). Poll periodically for progress and completion rather than blocking silently.
   - On success, report paths under `eval_runs/<eval-run-id>/` (`eval/report.json`, `manifest.json`, and updated `eval_runs/index.json`) plus summary metrics (`benchmark_misses`, split top-1/top-3, `parsed_ok`).

7. **After completion**
   - Suggest `/eval-triage <eval-run-id>` to review failures, or remind the user to change one variable and re-run with a new `--eval-run-id`.

**Profiles**

| Profile | Images | Notes |
|---|---|---|
| `smoke` | 4 | First 4 rows of `eval/profiles/quick.yaml` |
| `quick` | 8 | All manifest rows — default improvement round |
| `full` | 6,149 | Full test split — long benchmark; confirm first |
