> **Status:** PLACEHOLDER — this proposal is indicative only and subject to full revision when planning begins.

## Why

Determine whether prompt engineering, RAG, and model selection have reached a performance ceiling that justifies adapting model weights. Fine-tuning is explicitly optional and not required for project success (Stage 10 of the external spec).

## Depends on

- `eval-dataset-baseline` — substantial labelled dataset and understood failure modes
- `improvement-loop-service` — experiment infrastructure and plateau evidence from prior changes
- Prior RAG changes evaluated and prompt improvements exhausted

## Maps from

- `initial_extenal_dev_spec.md` — Stage 10 (Investigate Fine-Tuning)

## Decision gates (resolve before full planning)

- Evidence that RAG + prompts + model selection have plateaued
- Sufficient labelled data volume and quality for fine-tuning
- Local fine-tuning feasibility (LoRA/QLoRA, hardware constraints)
- Whether fine-tuning target is vision-language adapter (VLM repository path) vs text-only species context
- Fine-tuned weights remain behind `IdentificationRepository` — no parallel inference path
- Evaluation suite remains authority for go/no-go

## What Changes (indicative)

- Fine-tuning investigation spike(s) only — not production pipeline unless justified
- Comparison of fine-tuned vs best baseline using existing eval suite
- Documented decision: proceed, defer, or abandon

## Planned capabilities (subject to change)

- `fine-tuning-investigation` — spike scope, eval comparison, decision record

## Non-goals (indicative)

- Committing to production fine-tuning pipeline without eval proof
- Replacing the evaluation suite as quality authority

## Impact

- TBD at planning time
