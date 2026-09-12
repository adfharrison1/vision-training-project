## Why

The project identifies plants from a closed-set catalog tied to Oxford 102 (~102 garden-flower classes). That vocabulary misses common UK houseplants (Monstera, snake plant, peace lily, etc.), so runtime and eval cannot measure or improve identification on realistic indoor plants. We need a **unified dataset extension**—same layout, splits, and catalog rules as Oxford—not a parallel benchmark.

## What Changes

- Extend `resources/species_catalog/default.txt` from **102 → 152** classes by appending **50 net-new** UK-popular houseplant labels (lines 103–152).
- Add curated images under the **same** `data/flowers/jpg/` tree with **continued 1-based indexing** (`image_08190+`), merged `imagelabels.mat` and `setid.mat` (Oxford upstream files remain reproducible; local merge via scripts).
- Assign **train / validation / test** splits to extension images using the same Oxford convention (target ~10 train + ~10 val per new class; remainder test).
- Overlap policy: species already in the 102 catalog are **not** new lines—add photos under existing class ids instead; replacement labels fill the 50-slot extension list.
- Add eval profile manifest `eval/profiles/houseplants-quick.yaml` (and wire profile `houseplants-quick`) for a fixed improvement round on extension classes; keep existing `smoke` / `quick` on Oxford rows for regression.
- Add curation tooling: CSV → `.mat` builder, optional open-licensed image fetch helper, provenance tracking.
- **BREAKING**: Default bundled catalog grows to 152 labels; VLM closed-set prompts and any hard-coded “102 species” tests/docs must update. Prompt version bump recommended.

## Depends on

- `eval-dataset-baseline` — eval runner, Oxford loader, metrics, reports
- `eval-profile-manifest` — YAML manifest pattern for fixed profile rows

## Decision gates (resolve during apply)

- Minimum images per new class before first eval profile run (proposed: ≥3 with at least one test-split image each).
- Image provenance policy (proposed: open licenses only—Wikimedia Commons / iNaturalist research-grade—with `sources.csv`).
- Whether `full` profile enumerates **combined** test split (~6,149 + extension test images) or stays Oxford-only until explicitly requested (proposed: combined when merged mats present).

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- `evaluation-dataset`: unified Oxford + houseplant extension in one dataset root; continued image indexing; merged label/split mats; extension manifest profile; validation for class ids 1–152
- `local-dev-environment`: document curation workflow, merge scripts, license/provenance expectations, and updated catalog size
- `species-identification`: default bundled catalog documents 152-class unified vocabulary (Oxford + houseplants)

## Non-goals

- Separate `data/houseplants/` tree or second runtime catalog file for steady-state use
- Pl@ntNet or other external APIs at runtime
- Auto-labeling without human review
- Committing copyrighted stock photos or the Oxford tarball into git (`data/` stays gitignored)
- Fine-tuning or classical ML training implementation (future `classical-ml-backend` may consume the same train split later)

## Impact

- `resources/species_catalog/default.txt`, `prompt_version` default in settings
- `eval/dataset.py`, `eval/profile_manifest.py`, `eval/run_oxford102.py`, new `eval/profiles/houseplants-quick.yaml`
- New scripts under `scripts/` for mat merge and curation (exact names in design.md)
- `eval/README.md`, `README.md`, unit tests for catalog size, manifest validation, merged index bounds
- Runtime VLM prompt size (+50 labels); expect possible accuracy tradeoff on 2b
