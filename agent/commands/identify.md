---
name: "/identify"
description: "Identify plant species from photo path(s) using the local VLM"
category: "Development"
---

Run ad-hoc plant identification on one or more photos.

**Input**: Absolute path(s) to photo file(s), comma-separated for multi-photo observations (1–3 images of the same plant). If no path is provided, ask the user for an absolute path before proceeding.

**Steps**

1. **Validate input**
   - Paths must be absolute
   - Confirm files exist before running

2. **Run identify**
   ```bash
   uv run plant-id identify --backend vlm --photos <absolute-path>[,<path2>,...]
   ```
   Optional: `--think` / `--no-think` for this run (default `false`; env `PLANT_ID_OLLAMA_THINK`).

3. **Summarize results**
   - Top species predictions from stdout JSON or the saved artifact under `artifacts/`
   - Note `uncertain: true` if present

4. **Optional tracing**
   - If the user wants traces, ensure `PLANT_ID_OPIK_ENABLED=true` and Opik is running (`/opik-up`)

**Runtime boundary**

Local VLM only — no Pl@ntNet or other external identification APIs.
