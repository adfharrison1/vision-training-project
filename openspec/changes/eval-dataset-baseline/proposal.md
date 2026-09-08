> **Status:** PLACEHOLDER — subject to full revision when planning begins.

## Why

Objective measurement against Oxford 102 ground truth — and optional comparison to Pl@ntNet — before optimising prompts, RAG, or models. Proves the local pipeline works on pre-labelled data without manual labelling effort.

## Depends on

- `uk-plant-id-poc` — local runtime identification with artifact persistence

## Maps from

- Original roadmap Stages 3–4 (eval dataset + baseline), reframed for Oxford 102

## Decision gates (resolve before full planning)

- Oxford 102 download layout and loader for train/val/test splits
- Normalisation rules for matching predictions to Oxford 102 class names
- Pl@ntNet API: key availability, UK flora project id, daily quota — **baseline is optional**
- Rate-limit/backoff strategy; graceful skip when quota exhausted
- Confirm eval module and baselines do not implement `IdentificationRepository`
- Eval runner uses same `IdentifyPlantUseCase` with different wired backends where applicable

## What Changes (indicative)

- Oxford 102 eval runner over test split
- Metrics: top-1, top-3, per-class confusion matrix
- **Optional** Pl@ntNet baseline adapter (`eval/baselines/plantnet.py`) — eval-only, flag-gated
- Comparison report: local backends (VLM, later classical) vs labels; optional Pl@ntNet eval baseline

## Runtime boundary (non-negotiable)

- Pl@ntNet and any external ID API: **eval/benchmark only**, never runtime
- If Pl@ntNet is unavailable or rate-limited, local metrics still run

## Planned capabilities (subject to change)

- `evaluation-dataset` — Oxford 102 loading and splits
- `evaluation-metrics` — top-k accuracy, per-class metrics
- `eval-baseline-plantnet` — optional external comparison adapter

## Non-goals (indicative)

- RAG, fine-tuning, production API
- Using Pl@ntNet as runtime fallback

## Impact

- TBD at planning time
