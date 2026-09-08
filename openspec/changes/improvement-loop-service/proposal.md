> **Status:** PLACEHOLDER — this proposal is indicative only and subject to full revision when planning begins.

## Why

Once baselines and retrieval exist, the project needs a systematic experiment loop and a production-shaped local service to iterate on identification failures and deploy the plant ID app for real use.

## Depends on

- `eval-dataset-baseline` — reproducible metrics and regression cases
- `vector-retrieval` (or `direct-species-rag` if vector DB deferred)

## Maps from

- `initial_extenal_dev_spec.md` — Stage 7 (Improvement Loop), Stage 8 (Observability Tooling), Stage 9 (Production-Shaped Local Application)

## Decision gates (resolve before full planning)

- Experiment tracking: custom JSON/SQLite vs Langfuse vs DeepEval
- Thin FastAPI interface layer (`interfaces/http/`) calling existing application use cases via composition root — no business logic in HTTP handlers; same pattern as CLI
- Docker Compose service set (app, ollama, qdrant, postgres, langfuse — which are in v1?)
- Failure taxonomy finalisation and regression test process
- What observability is required vs nice-to-have

## What Changes (indicative)

- Repeatable experiment comparison workflow
- Growing regression dataset from real failures
- FastAPI local service
- `docker compose up` deployment
- Optional Langfuse/DeepEval integration

## Planned capabilities (subject to change)

- `experiment-tracking` — model, prompt, config, dataset version, metrics
- `observability` — tracing, prompt versions, searchable history
- `local-service` — FastAPI plant identification API and docker-compose deployment

## Non-goals (indicative)

- Kubernetes
- Fine-tuning
- Multi-language architecture

## Impact

- TBD at planning time
