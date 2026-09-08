# Evaluation (`eval/`)

This directory is for **benchmark and comparison code only**. It is intentionally separate from the runtime identification path.

## What belongs here (Change 2+)

- Oxford 102 eval runner (test split, top-1 / top-3 metrics)
- Optional **Pl@ntNet API baseline** — eval-only, flag-gated, skippable if rate-limited
- Comparison reports: local backends (VLM, later classical ML) vs ground truth

## What does NOT belong here

- Runtime `IdentificationRepository` implementations
- Code imported by `IdentifyPlantUseCase` or the production CLI identify path
- Pl@ntNet or any external ID API called during normal `plant-id identify`

## Runtime boundary

```text
Runtime:  CLI --> use case --> IdentificationRepository (local only)

Eval:     eval/runner --> metrics on labels vs wired backends OR saved artifacts
          eval/baselines/plantnet.py  (optional; NOT a repository)
```

See `openspec/changes/eval-dataset-baseline/` for the planned eval change.
