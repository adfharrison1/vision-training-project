## Why

Build a local-only plant identification learning project with a swappable architecture: prove a vision-language model can identify UK-occurring flowering plants from photographs, while establishing clean layers and repository interfaces so classical ML backends can be plugged in later without rewriting the app.

Oxford 102 Flowers provides free, pre-labelled, downloadable images with train/val/test splits.

## What Changes

- Introduce clean-architecture-ish Python project: domain, application, infrastructure, interfaces.
- Define repository interfaces in domain; implement VLM/Ollama as first `IdentificationRepository`.
- Add `IdentifyPlantUseCase` in application layer; thin CLI in interfaces layer.
- 1–3 photos → structured top-k predictions; artifact persistence via repository.
- Runtime vs eval boundary; composition root selects backend from config/CLI.

## Non-goals

- Classical ML training/inference implementation (deferred to `classical-ml-backend` change).
- External identification APIs at runtime.
- Pl@ntNet baseline (Change 2; optional eval-only).
- RAG, vector DB, HTTP API service, fine-tuning.
- Checklist survey or PASS/FAIL semantics.

## Capabilities

### New Capabilities

- `application-architecture`: Layer boundaries, repository ports, dependency rules, composition/wiring.
- `local-dev-environment`: Prerequisites, pinned tools, Ollama setup, verify command.
- `local-vlm-inference`: VLM repository implementation (Ollama multimodal, structured output).
- `species-identification`: Observation model, use case contract, top-k result semantics.

### Modified Capabilities

- None (greenfield).

## Impact

- New layered package under `src/plant_id/`.
- Oxford 102 for demo vocabulary; VLM as default `--backend vlm`.
- Architecture supports future `--backend classical` without use-case changes.
