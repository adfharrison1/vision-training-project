> **Status:** PLACEHOLDER — subject to full revision when planning begins.

## Why

Provide a classical machine learning identification backend implementing the same `IdentificationRepository` port, enabling fair comparison against the VLM on Oxford 102 using identical use cases and metrics.

## Depends on

- `uk-plant-id-poc` — layered architecture and repository interface
- `eval-dataset-baseline` — eval runner and metrics (recommended before training)

## Decision gates (resolve before full planning)

- Framework choice: torchvision ResNet vs smaller sklearn baseline
- Train on Oxford 102 train split; evaluate on test split
- Multi-photo policy: average softmax across 1–3 images
- Model artifact storage path and versioning
- Pin torch/sklearn versions

## What Changes (indicative)

- `ClassicalMlIdentificationRepository` fully implemented
- Training script on Oxford 102 train split
- `--backend classical` wired in composition container
- Eval comparison report: VLM vs classical ML on same test set

## Architecture (non-negotiable)

- MUST implement domain `IdentificationRepository` — no parallel code path
- MUST NOT call external APIs
- Use case and CLI unchanged except backend flag

## Planned capabilities (subject to change)

- `classical-ml-identification` — train + inference repository

## Non-goals (indicative)

- Replacing VLM as default backend
- Fine-tuning VLMs

## Impact

- TBD at planning time
