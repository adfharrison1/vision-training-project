# Species knowledge sheets

YAML sheets seed species retrieval and optional RAG prompt context. They are **source of truth in git**; embedding vectors are built separately (see `eval/README.md`).

## Schema

Each file is one species. Required fields:

| Field | Purpose |
|-------|---------|
| `catalog_label` | Must match a line in `resources/species_catalog/default.txt` exactly |
| `retrieval_text` | Morphology and habitat for lexical + dense retrieval (OpenRouter text embed; BM25 in describe-hybrid fallback) |
| `context_block` | Disambiguation notes for VLM prompt injection (not required in embeddings) |

Optional `provenance` records authoring metadata (`authored_by`, `source_images`, `prompt_version`).

## Curated train prototypes (`prototypes.yaml`)

Optional YAML map at `resources/species_sheets/prototypes.yaml`: `catalog_label` → list of Oxford **train** image filenames (e.g. `image_01234.jpg`). When present for a species, `eval.build_retrieval_index` uses those images instead of the first-N train scan. Paths are validated against the train split and ground-truth label at index build time. Omit the file or leave labels unset to keep automatic train selection.

## Authoring rules

- Describe the **plant**, not a photograph: no “in frame”, dataset names, or image ids in `retrieval_text`.
- Use traits that distinguish confusers in the closed catalog (see `context_block`).
- Review VLM drafts before commit; synthesis is eval/dev tooling only.

## File naming

Use a filesystem slug (e.g. `bolero_deep_blue.yaml`) with `catalog_label` set to the catalog string.

## Synthesis CLI

Draft sheets from Oxford training images (requires cloud VLM env):

```bash
uv run python -m eval.synthesize_species_sheet \
  --species "bolero deep blue" \
  --images /absolute/path/to/img1.jpg /absolute/path/to/img2.jpg \
  --out resources/species_sheets/bolero_deep_blue.yaml
```

Dry-run (no API call):

```bash
uv run python -m eval.synthesize_species_sheet \
  --species "bolero deep blue" \
  --images /path/to/img1.jpg \
  --dry-run
```

Validate committed sheets (no API key):

```bash
uv run python -m eval.validate_species_sheets
```

Index vectors are built with **OpenRouter** (see `eval/README.md`). Optional `describe-hybrid` retrieval does not use those Qdrant vectors.
