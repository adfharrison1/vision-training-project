## 1. Index curation

- [x] 1.1 Add `resources/species_sheets/prototypes.yaml` schema docs in `resources/species_sheets/README.md` (optional map label → train image filenames)
- [x] 1.2 Load curation in `eval/build_retrieval_index.py`; validate train split; use curated list when present else first-N train scan
- [x] 1.3 Unit tests: curation accepted, test-split path rejected, fallback when label omitted

## 2. Prototype debug in retrieval scoring

- [x] 2.1 Extend eval retrieval scoring to capture raw prototype hits before `aggregate_max_per_label` (eval-only hook or wrapper)
- [x] 2.2 Persist `winning_prototypes` / capped `raw_hits` in per-image artifacts under `rag_retrieval_only/` and full identify runs
- [x] 2.3 Add optional fields on `RetrievalObservationReportRow` (or sibling structure) in reports; extend retrieval failure forensics JSON
- [x] 2.4 Unit tests for debug payload shape on fake store hits

## 3. Per-label retrieval metrics

- [x] 3.1 Compute `retrieval_per_class` in retrieval metrics/report builders
- [x] 3.2 Include in retrieval-only and full identify JSON reports (additive); update `manifest_from_report` if index needs summary fields
- [x] 3.3 Unit tests: two-row pilot → two entries with distinct hit flags

## 4. Inspect tooling

- [x] 4.1 Implement `eval/inspect_retrieval_index.py` — manifest summary; optional `--profile bolero_and_canterbury` label filter; optional `--query-image` with OpenRouter embed
- [x] 4.2 Document in `eval/README.md` rebuild + inspect loop

## 5. Agent commands & verify

- [x] 5.1 Update `agent/commands/retrieval-debug.md` and `retrieval-triage.md` for prototype fields and curation workflow (if not already complete)
- [x] 5.2 Manual pilot: rebuild index with optional curation tweak → `run_retrieval_eval --profile bolero_and_canterbury` → confirm canterbury/bolero per-row + prototype metadata
- [x] 5.3 `uv run ruff check .` and `uv run pytest tests/unit/eval/`
