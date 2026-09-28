# Species RAG retrieval — tasks

## 1. Corpus and authoring

- [ ] 1.1 Define YAML sheet schema and example pilot sheets (campanula pair); document in `eval/README.md` or `resources/species_sheets/README.md`
- [ ] 1.2 Implement `eval/synthesize_species_sheet.py` — multi-image Fireworks/vlm-cloud synth; `--dry-run`; unit tests with mocked client
- [ ] 1.3 Add verify step: synth dry-run or schema validation in CI (no API key required)

## 2. Qdrant local dev

- [ ] 2.1 Add `docker/qdrant/docker-compose.yml` + `scripts/qdrant.sh` (up/down/seed/health) mirroring `scripts/opik.sh` ergonomics
- [ ] 2.2 Settings: `qdrant_url`, collection name, seed paths; document in `.env.example` and README
- [ ] 2.3 Seed script: upsert from built index manifest; idempotent point ids; clear error if index missing

## 3. Index build (multi-prototype)

- [ ] 3.1 Implement `eval/build_retrieval_index.py` — load sheets, Oxford train images per class (cap N), CLIP text+image embeddings, write `artifacts/retrieval_index/manifest.json` + vectors
- [ ] 3.2 Enforce **no test-split images** as prototypes; unit tests on split logic
- [ ] 3.3 Domain + infrastructure: `SpeciesRetrievalRepository` port; `QdrantSpeciesStore` low-level adapter (swappable fake)

## 4. Retrieval backend — CLIP

- [ ] 4.1 Implement `clip_prototype` backend — photo → vector → Qdrant search → aggregate max per `catalog_label` → top-K
- [ ] 4.2 Composition: `build_species_retrieval_repo(backend=clip-prototype)`
- [ ] 4.3 Unit tests with fake store; optional integration test marked `@pytest.mark.integration` with Qdrant

## 5. Retrieval backend — describe hybrid

- [ ] 5.1 Neutral describe prompt module (shared vlm-cloud client settings); no catalog species in output
- [ ] 5.2 BM25 over in-memory corpus from sheets + text-embed similarity via sentence-transformers (vectors in Qdrant or secondary index)
- [ ] 5.3 Fuse scores; expose weights in settings; backend id `describe-hybrid`
- [ ] 5.4 Unit tests: fusion ranking with fixtures

## 6. Retrieval eval harness

- [ ] 6.1 Implement `eval/run_retrieval_eval.py` — profiles reuse (`curated48`), `--retrieval-backend`, `--eval-run-id`, `--run-purpose`
- [ ] 6.2 Report + manifest schema (Recall@K, MRR); per-image artifacts under `eval_runs/{id}/artifacts/`
- [ ] 6.3 Failure forensics when GT not in top-K (`eval/retrieval_failure_forensics.py`); sync helper if needed
- [ ] 6.4 Agent commands `/retrieval-run`, `/retrieval-triage`, `/retrieval-debug`; update `AGENTS.md`
- [ ] 6.5 Delta specs synced to main specs on archive

## 7. Identify augment (end-to-end)

- [ ] 7.1 Prompt builder injects top-K `context_block` (pairwise format); settings `PLANT_ID_RAG_ENABLED`, retrieval backend + k
- [ ] 7.2 Composition wires retrieval → identify path without use case import violations; `lint-imports` clean
- [ ] 7.3 End-to-end eval profile or flag on `run_oxford102` for RAG A/B (document in eval README)

## 8. Documentation and agentic coding

**Stipulation:** each section above is not done until relevant READMEs match the code (same session/PR).

- [ ] 8.1 Update `openspec/config.yaml` planned sequence (merge stubs 5–6 into `species-rag-retrieval`)
- [ ] 8.2 Maintain **root `README.md`**: Qdrant helper, retrieval/RAG env vars, identify+RAG entrypoints, pointer to `eval/README.md`
- [ ] 8.3 Maintain **`eval/README.md`**: synthesise sheets, build-index, seed, `run_retrieval_eval`, failure layout, backend comparison, optional RAG A/B on `run_oxford102`
- [ ] 8.4 Maintain **`resources/species_sheets/README.md`**: schema, species-centric authoring rules, synth CLI
- [ ] 8.5 Maintain **`agent/commands/README.md`** + **`AGENTS.md`** when `/retrieval-run`, `/retrieval-triage`, `/retrieval-debug` land (section 6.4)
- [ ] 8.6 Add or update **`docker/qdrant/README.md`** (or root README subsection) for compose + seed troubleshooting
- [ ] 8.7 Before archive: grep READMEs for stale paths (`artifacts/eval`, old RAG stubs); run `/verify` loop
