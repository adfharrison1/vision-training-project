---
name: "/verify"
description: "Run the post-change verification loop"
category: "Development"
---

Run the standard post-change verification sequence for this project. Execute each step in order; report pass/fail for each. Do not skip failing steps silently.

**Steps**

Run these commands from the project root:

```bash
uv sync
uv run plant-id verify-env
uv run plant-id verify-env --backend species-sheets
uv run ruff check .
uv run lint-imports
uv run pytest
```

**Notes**

- `verify-env` needs Ollama running with `qwen3-vl:2b` (default model)
- `pytest` runs unit tests; integration tests skip without Ollama/sample data
- After implementation work, summarize any failures with file references and suggested fixes
- Do not commit unless the user explicitly asks

**On failure**

Stop at the first failing step only if later steps depend on it (e.g. skip pytest if `uv sync` fails). Otherwise run all steps and report a combined summary.
