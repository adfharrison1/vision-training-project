## 1. Catalog extension

- [ ] 1.1 Append 50 houseplant labels (lines 103–152) to `resources/species_catalog/default.txt` per `design.md`; verify no duplicate of Oxford lines 1–102
- [ ] 1.2 Bump default `prompt_version` in settings and update unit tests that assert catalog/prompt defaults

## 2. Dataset merge tooling

- [ ] 2.1 Add `scripts/build_dataset_mats.py` (or equivalent) to merge Oxford baseline mats + extension CSV into `imagelabels.mat` and `setid.mat`; verify unit tests with tiny fixtures under `tests/fixtures/dataset/`
- [ ] 2.2 Add extension CSV schema docs and example row in `eval/README.md` (fields: image filename, species, split, license, source url)
- [ ] 2.3 Add optional `scripts/fetch_extension_images.py` for open-licensed sources with provenance output (skip if no suitable stable API; document manual download path)

## 3. Eval loader and profiles

- [ ] 3.1 Extend `EvalProfile` with `houseplants-quick`; add `PROFILE_OBSERVATION_COUNTS` and default manifest path `eval/profiles/houseplants-quick.yaml`
- [ ] 3.2 Update `eval/dataset.py` for class id bounds 1–152, extension index support, and combined `full` test enumeration when merged mats present
- [ ] 3.3 Add `eval/profiles/houseplants-quick.yaml` skeleton (one row per extension class; placeholder images until curated)
- [ ] 3.4 Wire `--profile houseplants-quick` in `eval/run_oxford102.py`; verify runner unit tests

## 4. Documentation and agent guidance

- [ ] 4.1 Update `eval/README.md` and `README.md` with unified 152-class catalog, curation/merge workflow, overlap rule, and `houseplants-quick` profile
- [ ] 4.2 Update `AGENTS.md` eval section with new profile and catalog size note

## 5. Verification

- [ ] 5.1 Extend `tests/unit/eval/test_dataset.py` for 152-class validation, extension manifest path, and merged-index fixtures
- [ ] 5.2 Run `uv run pytest tests/unit/eval/`, `uv run ruff check .`, `uv run lint-imports`
- [ ] 5.3 Document manual smoke: merge fixture dataset → `uv run python -m eval.run_oxford102 --profile houseplants-quick --eval-run-id houseplants-smoke` (requires local curated or fixture data)

## 6. Agentic coding

- [ ] 6.1 Review whether `/eval-run` agent command should mention `houseplants-quick` profile (optional follow-up)
