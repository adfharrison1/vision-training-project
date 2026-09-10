## Context

See `proposal.md`. Runtime uses `execute_identify` with default **`qwen3-vl:2b`**. Partial eval groundwork exists (`oxford102_ground_truth.py`, `check_ground_truth.py`). Opik traces individual identifies when `PLANT_ID_OPIK_ENABLED=true`.

**Empirical latency (Intel macOS, one Oxford image, closed-set-v1 prompt, 2026-09-10):**

| Model | Total | Vision (prompt eval) | Generation | ~Images / 30 min |
|---|---|---|---|---|
| `qwen3-vl:2b` | **~209 s** | ~147 s | ~28 s | **~8** |
| `qwen3-vl:4b` | ~432 s | ~256 s | ~139 s | ~4 |
| `qwen3-vl:8b` | ~511 s | ~337 s | ~123 s | ~3–4 |

**Oxford 102 split sizes:** train 1,020 · validation 1,020 · **test 6,149**. Full test eval at ~3.5 min/image ≈ **15 days** on 2b — not a daily workflow.

```text
  IMPROVEMENT LOOP
  ================
  eval runner (--profile quick, --eval-run-id prompt-v1)
        |
        +--> JSON report (metrics + failures + trace_ids)
        |
        v
  Opik UI / MCP read trace for each failure
        |
        v
  Change ONE thing (prompt, catalog, threshold)
        |
        v
  Re-run same profile + run_id suffix → compare reports

  RUNTIME                          EVAL
  =======                          ====
  plant-id identify                python -m eval.run_oxford102
  (default qwen3-vl:2b)                  |
        |                                +--> dataset (profiles, splits)
        v                                +--> execute_identify (composition)
  Opik traces (optional)                 +--> metrics + report
        ^                                +--> optional Pl@ntNet baseline
        |______________________________________ trace_id + eval_run_id metadata
```

## Goals / Non-Goals

**Goals:**

- Named eval profiles with documented runtime budgets on 2b
- Default **`quick`** profile for ~30-minute improvement rounds
- **`full`** profile for long-running benchmarks (explicit opt-in)
- Link eval reports to Opik traces for failure diagnosis
- Measure and improve **`qwen3-vl:2b`** baseline (learning-project framing)
- Optional Pl@ntNet comparison; exact label matching

**Non-Goals:**

- Full test split as default runner mode
- Pl@ntNet ontology mapping
- `plant-id` subcommand for eval (stay `python -m eval.*`)
- Parallel batching in v1
- Changing use case or repository interfaces

## Decisions

### 1. Default VLM: qwen3-vl:2b

**Choice:** Eval and runtime default **`qwen3-vl:2b`**. Document `PLANT_ID_VISION_MODEL=qwen3-vl:8b` for comparison runs.

**Rationale:** ~2.4× faster than 8b on observed hardware; ~8 images per 30 min enables a real improvement loop. Learning goal is to raise 2b accuracy, not only match 8b out of the box.

**Alternatives considered:**

- *8b default, 2b eval-only* — rejected; user chose 2b as project default
- *4b as middle tier* — rejected; only ~15% faster than 8b here, slower than 2b

### 2. Eval profiles

**Choice:** Fixed profiles (deterministic, documented):

| Profile | Images | Split source | Target budget (2b) | Use |
|---|---|---|---|---|
| `smoke` | 4 | First 4 test-split images (stable order) | ~14 min | Pipeline sanity after code changes |
| `quick` | 8 | First 8 test-split images | **~30 min** | **Default** — prompt/catalog iteration |
| `full` | all | All 6,149 test images | days | Benchmark; overnight/weekend |

Also support `--limit N` and `--max-duration 30m` (stop when budget exceeded) as overrides.

**Rationale:** Profiles encode expected runtime; avoids ad-hoc `--limit` guesswork.

**Future:** stratified `mini` (1 per class = 102 images) as follow-up once basic runner works.

### 3. Dataset module

**Choice:** Extend `oxford102_ground_truth.py` → `eval/dataset.py` with `setid.mat` splits. Test split = setid `3`.

**Split mapping:** `1=train`, `2=validation`, `3=test`.

### 4. Label matching

Exact case-sensitive catalog string equality (unchanged).

### 5. Eval runner uses composition

`execute_identify(backend, [photo], observation_id, settings, quiet=True)` — unchanged.

**Observation ID convention:** `eval-{eval_run_id}-{image_stem}` (e.g. `eval-prompt-v1-image_00001`).

### 6. Opik linkage

**Choice:** When `PLANT_ID_OPIK_ENABLED=true`:

1. Runner generates **`eval_run_id`** (CLI flag or timestamp slug); passes to tracing layer
2. Infrastructure adds trace metadata: `eval_run_id`, `eval_profile`, `ground_truth` (after identify), `match` (bool)
3. Infrastructure exposes **`trace_id`** back to caller after identify (small addition to observability helper or return path used only by eval)
4. Report JSON includes per-observation rows:

```json
{
  "eval_run_id": "prompt-v1-baseline",
  "profile": "quick",
  "model_tag": "qwen3-vl:2b",
  "backend": "vlm",
  "split": "test",
  "observation_count": 8,
  "duration_total_ms": 1680000,
  "top1_accuracy": 0.375,
  "top3_accuracy": 0.5,
  "failures": [
    {
      "image": "image_00042.jpg",
      "ground_truth": "tiger lily",
      "predicted": "english marigold",
      "trace_id": "01a08cae-...",
      "observation_id": "eval-prompt-v1-baseline-image_00042"
    }
  ],
  "observations": [ "... per-row detail ..." ],
  "per_class": { "...": { "total": 1, "top1": 0, "top3": 0 } },
  "plantnet": null
}
```

**MCP workflow (documented, not automated):** read failures from report → `read('trace', trace_id)` in Opik MCP → inspect thinking/timing → change one variable → re-run same profile.

**Alternatives considered:**

- *Opik-only, no report linkage* — rejected; need aggregate metrics in JSON
- *Report-only, no trace_id* — rejected; MCP diagnosis requires stable trace reference

### 7. Runner CLI

| Flag | Default | Purpose |
|---|---|---|
| `--profile` | `quick` | `smoke` \| `quick` \| `full` |
| `--eval-run-id` | auto timestamp slug | Correlates report + Opik traces |
| `--backend` | `vlm` | Composition backend |
| `--split` | `test` | Oxford split (profiles use test unless noted) |
| `--limit N` | none | Override profile size |
| `--max-duration` | none | e.g. `30m` — stop when exceeded |
| `--quiet` | true | Suppress Rich progress |
| `--dataset-root` | `data/flowers` | Override dataset path |
| `--plantnet-baseline` | off | Pl@ntNet comparison |
| `--output` | auto | Report path |

### 8. Pl@ntNet baseline

Unchanged from prior design — eval-only, `PLANTNET_API_KEY`, retry/backoff, exact catalog match.

### 9. Dependencies

Promote `scipy==1.18.1` to main deps; add `httpx==0.28.1` for Pl@ntNet.

### 10. Testing

| Layer | Tests |
|---|---|
| `eval/dataset.py` | Splits, profiles, skip without dataset |
| `eval/metrics.py` | Synthetic fixtures |
| Opik linkage | Unit test with fake trace_id injection |
| Runner | Integration `@pytest.mark.integration` with `--profile smoke` |

## Pinned versions (verified 2026-09-10)

| Component | Version | Notes |
|---|---|---|
| Python | 3.14.7 | unchanged |
| Default VLM | `qwen3-vl:2b` | settings default |
| scipy | 1.18.1 | main deps |
| httpx | 0.28.1 | Pl@ntNet client |

## Risks / Trade-offs

- **[Risk] 2b accuracy lower than 8b on Oxford 102** → Expected; learning goal is measurable improvement; compare with 8b runs via env override
- **[Risk] Full profile impractical on VLM** → Mitigation: explicit `full` opt-in; document multi-day runtime
- **[Risk] Opik UI stale until browser refresh** → Document hard-refresh or open CLI trace URL after long runs
- **[Risk] trace_id plumbing touches infrastructure** → Minimal change in observability helper only; no Opik in domain/application
- **[Risk] Pl@ntNet name mismatch** → Optional baseline; local metrics always run

## Migration Plan

1. Dataset + metrics + profile selection
2. Runner with `quick` default; smoke integration test
3. Opik linkage (eval_run_id, trace_id in report)
4. Pl@ntNet baseline behind flag
5. Docs: profiles, improvement loop, MCP workflow

## Open Questions

None blocking v1. Stratified `mini` profile (1 image/class) can follow once basic runner is stable.
