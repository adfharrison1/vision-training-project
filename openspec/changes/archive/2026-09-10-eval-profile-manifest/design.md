## Context

See `proposal.md`. Code already implements manifest-based smoke/quick selection after the first smoke run exposed the passion-flower-only bug.

## Decisions

### 1. Single manifest file for smoke and quick

**Choice:** `eval/profiles/quick.yaml` with eight rows; smoke takes first four.

**Rationale:** One editable file; smoke remains a subset of quick for pipeline checks.

### 2. Independent species and image fields

**Choice:** YAML rows with `species` and `image`; validate `imagelabels.mat` ground truth matches `species`.

**Rationale:** Allows swapping a harder image without changing species label, or changing species with a matching image, when the default set becomes too easy.

### 3. Default eight species

**Choice:** First test-split image per species for eight catalog-ordered species (pink primrose through bird of paradise in default manifest).

**Rationale:** Deterministic, diverse, reproducible baseline without running 102 images.

### 4. CLI override

**Choice:** `--profile-manifest` optional path; default `eval/profiles/quick.yaml`.

## Testing

- Unit tests for manifest load, profile slice sizes, species/image mismatch rejection
- Existing dataset integration tests updated for eight distinct quick species
