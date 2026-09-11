---
name: "/demo"
description: "Run the bundled sample plant identification demo"
category: "Development"
---

Run the project demo identify path on the bundled sample image.

**Steps**

1. **Check sample image**
   - Expected path: `data/flowers/jpg/image_00001.jpg`
   - If missing, explain that Oxford 102 flower images are required (see README Data section) and stop

2. **Run demo**
   ```bash
   uv run plant-id demo --backend vlm
   ```

3. **Summarize results**
   - Top predictions from stdout or saved artifact
   - Confirm Ollama and default model (`qwen3-vl:2b`) were used

**Notes**

- Demo uses the configured species catalog at `resources/species_catalog/default.txt`
- Local runtime only — no external identification APIs
