---
name: "/opik-up"
description: "Start or check the local Opik observability stack"
category: "Development"
---

Start or verify the local self-hosted Opik stack for VLM trace debugging.

**Steps**

1. **Start Opik**
   ```bash
   ./scripts/opik.sh up
   ```
   - Requires Docker. If `docker` is missing, report install instructions from README (Homebrew docker + colima on macOS).

2. **Check status**
   ```bash
   ./scripts/opik.sh status
   ```
   - Wait until services are healthy (first boot can take several minutes)
   - UI URL: `http://localhost:5173`
   - API base: `http://127.0.0.1:5173/api`

3. **If already running**
   - Report healthy status without treating it as an error

4. **Remind developer**
   - To export traces from plant-id runs:
     ```bash
     export PLANT_ID_OPIK_ENABLED=true
     ```
   - Do **not** set `OPIK_API_KEY` (no Comet cloud)
   - Do **not** call `opik.configure()` from plant-id — tracing uses session config only

5. **Optional next steps**
   - Suggest `/identify` or `/eval-run` with tracing enabled for a traced run
