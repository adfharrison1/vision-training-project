## Context

See `proposal.md`. Today the unified catalog and dataset are Oxford-only: 102 labels in `resources/species_catalog/default.txt`, 8,189 images in `data/flowers/jpg/`, ground truth from bundled `imagelabels.mat` / `setid.mat`. Runtime and eval share one closed-set vocabulary via `PLANT_ID_SPECIES_CATALOG_PATH` (default bundled file). Eval profiles `smoke` / `quick` use `eval/profiles/quick.yaml`; loader validation checks manifest species against `imagelabels.mat`.

**Runtime vs eval (unchanged boundary):**

```text
  RUNTIME                         EVAL
  =======                         ====
  plant-id identify               python -m eval.run_oxford102
        |                               |
        v                               v
  IdentificationRepository        eval/dataset.py (same data root)
  + species catalog (152)         + metrics + report
  local Ollama only               optional Pl@ntNet (eval-only)
```

## Goals / Non-Goals

**Goals:**

- One dataset root (`data/flowers/`), one catalog (`default.txt` → 152 lines), Oxford-compatible `.mat` files after merge
- 50 net-new houseplant classes (catalog lines 103–152) with curated photos and human-confirmed labels
- Reuse existing train/val/test semantics for extension images and future classical ML training
- New eval profile `houseplants-quick` for improvement rounds on extension classes; keep Oxford `quick` for regression
- Reproducible curation scripts (CSV → `.mat`, optional licensed fetch helper)

**Non-Goals:**

- Second dataset directory or runtime catalog for steady state
- Auto-labeling or bulk unlicensed scraping
- Changing use case / repository interfaces
- Classical ML training implementation in this change

## Decisions

### 1. Unified catalog append (102 + 50)

**Choice:** Append 50 lines to `default.txt`; class ids 103–152 map to those lines. Oxford lines 1–102 unchanged.

**Overlap rule:** Eight popular houseplants already exist in Oxford vocabulary. They are **not** new lines; curated photos use existing class ids:

| Do not add (use existing class) | Oxford label |
|---|---|
| moth orchid | `moon orchid` |
| anthurium | `anthurium` |
| cyclamen | `cyclamen` |
| poinsettia | `poinsettia` |
| bromeliad | `bromelia` |
| amaryllis | `hippeastrum` |
| orchid cattleya | `ruby-lipped cattleya` |
| desert rose | `desert-rose` |

**50 net-new labels (lines 103–152):**

```text
peace lily              snake plant             spider plant
swiss cheese plant      devil's ivy             aloe vera
rubber plant            weeping fig             chinese money plant
jade plant              prayer plant            boston fern
maidenhair fern         kentia palm             areca palm
cast iron plant         zz plant                dragon tree
yucca                   heartleaf philodendron  african violet
polka dot begonia       wax plant               string of pearls
umbrella tree           fiddle leaf fig         chinese evergreen
dumb cane               inch plant              christmas cactus
parlor palm             nerve plant             radiator plant
croton                  lipstick plant          english ivy
staghorn fern           bird's nest fern        calathea medallion
monstera adansonii      pilea glauca            hawaiian ti plant
money tree              air plant               lucky bamboo
ponytail palm           burro's tail            echeveria
string of hearts        asparagus fern
```

**Rationale:** One closed-set task; VLM and future classical ML see one vocabulary.

**Alternatives considered:**

- *Separate catalog file* — rejected; user wants one dataset mental model
- *Duplicate overlapping retail names* — rejected; causes ambiguous closed-set labels

### 2. Image index continuity

**Choice:** Extension JPEGs start at **`image_08190.jpg`** (first index after Oxford's 8,189). `imagelabels.mat` grows to one row per image index; `setid.mat` grows in parallel.

**Rationale:** Reuses `parse_image_index`, `ground_truth_species_label`, and manifest validation unchanged.

### 3. Merge workflow (Oxford upstream preserved)

**Choice:** Keep pristine Oxford download separate; scripts merge into working `data/flowers/`:

1. Developer downloads Oxford 102 to `data/flowers/` (existing README flow)
2. Curator adds extension JPEGs + `data/flowers/extension/sources.csv` (path, species, split, license, attribution)
3. `scripts/build_dataset_mats.py` (name TBD) reads Oxford mats + extension CSV → writes merged `imagelabels.mat` / `setid.mat`
4. Unit tests use tiny fixtures under `tests/fixtures/dataset/`

**Rationale:** Oxford tarball stays reproducible; extension is additive local data (gitignored).

### 4. Split assignment for extension

**Choice:** Target Oxford convention (~10 train, ~10 val, rest test per new class). Bootstrap with ≥3 images/class minimum for first `houseplants-quick` eval; expand over time.

**Rationale:** Same semantics for future `classical-ml-backend` without redesign.

### 5. Eval profiles

| Profile | Manifest | Purpose |
|---|---|---|
| `smoke` | `eval/profiles/quick.yaml` (4 rows) | Oxford regression |
| `quick` | `eval/profiles/quick.yaml` (8 rows) | Oxford improvement loop |
| `houseplants-quick` | `eval/profiles/houseplants-quick.yaml` | Extension improvement loop (~10 rows, one image per extension class initially) |
| `full` | none (all test indices) | Combined test split when merged mats present |

**Choice:** Add `houseplants-quick` to `EvalProfile` enum and `PROFILE_OBSERVATION_COUNTS`.

### 6. Prompt version bump

**Choice:** Bump default `prompt_version` when 152-class catalog ships (e.g. `closed-set-v3-houseplants`).

**Rationale:** Separates eval reports before/after catalog expansion.

### 7. Image sourcing

**Choice:** Human review required. Optional helper fetches from Wikimedia Commons / iNaturalist with license filters; provenance mandatory. No committed photos in git.

## Risks / Trade-offs

| Risk | Mitigation |
|---|---|
| 152-class prompt too large for 2b VLM | Document expected accuracy dip; keep Oxford `quick` for regression |
| Curation labour | Bootstrap 3–5 images/class; expand incrementally |
| Label errors | Manifest validates against `imagelabels.mat`; human review gate |
| Merge script bugs | Fixture-based unit tests; validate class id bounds 1–152 |
| `full` eval runtime grows | Document new approximate test count after merge |

## Migration Plan

1. Ship catalog append + loader/profile changes (code works with Oxford-only mats until merge)
2. Document curation; curator builds extension CSV + images locally
3. Run merge script → verify `houseplants-quick` eval
4. Update AGENTS.md / README with 152-class note and new profile
5. Rollback: restore 102-line catalog + Oxford-only mats from backup

## Open Questions

_None blocking apply._ Minimum images per class for first eval manifest is documented as ≥3 bootstrap in decision gates; can tighten later.

## Pinned versions

No new runtime dependencies. Merge scripts reuse existing **`scipy==1.18.1`** (already in project deps for `.mat` I/O). Verify pin unchanged at apply time.
