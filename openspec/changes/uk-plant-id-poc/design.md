## Context

See `proposal.md`. UK flower ID on Oxford 102 with **clean-architecture-ish** layering and **repository pattern** for swappable backends (VLM now, classical ML later).

```text
                         INTERFACES (thin)
                         =================
                           CLI  [future: HTTP]
                              |
                         composition / wiring
                         (--backend vlm|classical)
                              |
                         APPLICATION
                         ===========
                     IdentifyPlantUseCase
                              |
                    IdentificationRepository  (port)
                    ArtifactRepository        (port)
                              |
                         DOMAIN
                         ======
              Observation, ObservationResult, Prediction
              IdentificationRepository (Protocol)
              ArtifactRepository (Protocol)
              ApplicationEvents (port + context binding)
                              ^
                         INFRASTRUCTURE
                         ==============
              VlmOllamaIdentificationRepository   <-- Change 1
              ClassicalMlIdentificationRepository <-- stub / Change 3
              FileArtifactRepository
              FileSpeciesCatalog

  EVAL (outside runtime repositories)
  ===================================
  Oxford102EvalRunner  -->  uses same use case OR compares baselines
  PlantNetBaselineAdapter (optional, eval-only, NOT IdentificationRepository)
```

**Runtime vs eval:** unchanged — Pl@ntNet eval-only, optional, skippable.

## Goals / Non-Goals

**Goals:**

- Layered architecture with testable use cases
- VLM as first `IdentificationRepository` implementation
- CLI `--backend vlm` (classical stub raises clear "not implemented")
- Oxford 102 demo; artifact persistence
- `import-linter` contracts enforcing layer boundaries in CI

**Non-Goals:**

- Classical ML training (Change `classical-ml-backend`)
- HTTP API (interfaces layer ready, not implemented)
- Pl@ntNet in runtime
- Full eval runner (Change 2)

## Decisions

### 1. Layer responsibilities

| Layer | Contains | May import |
|---|---|---|
| **domain** | Entities, value objects, repository Protocols, `ApplicationEvents`, domain exceptions | stdlib, typing, pydantic models |
| **application** | Use cases (`IdentifyPlantUseCase`), DTOs if needed | domain |
| **infrastructure** | Repository implementations, Ollama client, file I/O, species catalog loader, settings | domain (+ third-party libs) |
| **interfaces/cli** | CLI commands, Rich presentation helpers, future FastAPI routes | `interfaces.composition` only (plus stdlib) |
| **interfaces/composition** | Composition root — wires use cases; builds observations; binds `ApplicationEvents` | application, domain, infrastructure |

**Dependency rule:** dependencies point inward. Domain never imports outward. Infrastructure never imports application or interfaces. CLI commands never import domain or infrastructure directly — only via `interfaces.composition`.

### 2. Repository ports (domain)

```python
# domain/repositories.py

class IdentificationRepository(Protocol):
    @property
    def backend_id(self) -> str: ...

    def identify(self, observation: Observation) -> tuple[ObservationResult, dict]:
        """Return structured result and raw model payload for artifact persistence."""


class ArtifactRepository(Protocol):
    def save_identification_run(
        self, observation: Observation, raw: dict, result: ObservationResult | None, error: str | None
    ) -> Path: ...


class SpeciesCatalogRepository(Protocol):
    def list_class_names(self) -> list[str]: ...
```

**Why repository pattern:** swapping VLM ↔ classical ML = new infrastructure class + composition wiring. Use case unchanged.

### 3. Application use case

```python
# application/use_cases/identify_plant.py

class IdentifyPlantUseCase:
    def __init__(
        self,
        identification_repo: IdentificationRepository,
        artifact_repo: ArtifactRepository,
    ): ...

    def execute(self, observation: Observation) -> ObservationResult:
        # validate observation in domain/application
        # call identification_repo.identify()
        # persist via artifact_repo
        # return result
```

No Ollama imports here. No HTTP. No argparse.

### 4. Infrastructure implementations (Change 1)

| Class | Role |
|---|---|
| `VlmOllamaIdentificationRepository` | Ollama multimodal, prompts, structured JSON → `ObservationResult`; emits `ApplicationEvents` stages; receives injected `SpeciesCatalogRepository` |
| `FileArtifactRepository` | JSON artifacts under `artifacts/`; emits `log_event` on save |
| `FileSpeciesCatalog` | Load closed-set labels from a newline-delimited text file (`Settings.species_catalog_path`) |

**Stub:** `ClassicalMlIdentificationRepository` — raises `NotImplementedError` or registered but disabled until Change 3.

### 5. Composition / dev wiring

```python
# interfaces/composition/container.py

def build_identify_use_case(backend: Literal["vlm", "classical"], settings: Settings) -> IdentifyPlantUseCase:
    species_catalog = FileSpeciesCatalog(settings.species_catalog_path)
    if backend == "vlm":
        id_repo = VlmOllamaIdentificationRepository(settings, species_catalog)
    elif backend == "classical":
        id_repo = ClassicalMlIdentificationRepository(settings, species_catalog)  # later
    artifact_repo = FileArtifactRepository(settings.artifacts_dir)
    return IdentifyPlantUseCase(id_repo, artifact_repo)
```

**Catalog injection:** `IdentifyPlantUseCase` does **not** depend on `SpeciesCatalogRepository`. The composition root builds `FileSpeciesCatalog` once and injects it into identification repository implementations that need closed-set labels (VLM prompts now; classical ML label mapping later).

**Dataset agnostic runtime:** Application and domain code MUST NOT reference Oxford 102 or other benchmark names. The default bundled catalog (`resources/species_catalog/default.txt`) happens to contain the Oxford 102 vocabulary today; swap via `PLANT_ID_SPECIES_CATALOG_PATH` without code changes. Downloaded images under `data/flowers/` are for eval/demo/training only.

CLI:

```bash
plant-id identify --backend vlm --photos a.jpg,b.jpg
plant-id demo --backend vlm
plant-id identify --backend vlm --photos a.jpg --quiet   # suppress CLI progress
```

**ApplicationEvents:** Infrastructure and application code call domain helpers (`log_event`, `log_stage`, `log_wait`). Default is a silent no-op. CLI binds `RichApplicationEvents` for the duration of `identify` / `demo` via `use_application_events()` (see §15).

### 6. VLM vs classical ML behaviour (future)

| Concern | VLM repository | Classical ML repository |
|---|---|---|
| Multi-photo | All images in one Ollama request | Average softmax across images (planned) |
| RAG | Prompt injection (Change 4) | N/A or separate features |
| Evidence text | From model | Optional omit or post-hoc |
| backend_id | `vlm:qwen3-vl:8b` | `ml:resnet50-oxford102` |

Same `ObservationResult` either way → same eval metrics.

### 7. Eval path (Change 2 hook)

- `eval/runner.py` imports use case + composition OR runs metrics on saved artifacts
- `eval/baselines/plantnet.py` — **separate adapter**, not `IdentificationRepository`
- Eval MAY compare: labels vs VLM repo vs classical repo vs optional Pl@ntNet

### 8. Repository layout

```text
resources/
└── species_catalog/
    └── default.txt            # closed-set labels; Oxford 102 vocabulary today

data/                          # gitignored; benchmark datasets for eval/training/demo
└── flowers/
    └── jpg/ …

src/plant_id/
├── domain/
│   ├── models.py
│   ├── repositories.py      # Protocols
│   ├── application_events.py
│   └── exceptions.py
├── application/
│   └── use_cases/
│       └── identify_plant.py
├── infrastructure/
│   ├── identification/
│   │   ├── vlm_ollama.py
│   │   └── classical_ml.py  # stub
│   ├── persistence/
│   │   └── file_artifacts.py
│   ├── species/
│   │   └── file_catalog.py
│   ├── ollama/
│   │   └── environment.py
│   └── config/
│       └── settings.py
└── interfaces/
    ├── composition/
    │   ├── container.py       # wires use cases to infrastructure
    │   ├── identify.py        # execute_identify orchestration
    │   └── events.py          # ApplicationEvents binding
    └── cli/
        ├── presentation.py    # Rich CLI presentation (uses composition)
        ├── main.py
        ├── rich_events.py     # Rich terminal handler (CLI only)
        └── commands/
            ├── verify_env.py
            ├── identify.py
            └── demo.py

eval/                          # top-level; not imported by use cases
├── README.md
└── (Change 2: runner, baselines/)

tests/
├── unit/
│   ├── domain/
│   └── application/         # use case with fake repos
└── integration/

.importlinter                  # layer boundary contracts (see §11)
```

### 9. Domain validation

`Observation`, `Prediction`, and `ObservationResult` are Pydantic models in `domain/models.py`. Photo count (1–3) and required fields are validated at construction so invalid observations never reach repositories.

The use case may rely on domain construction validation; it does not re-implement photo-count rules.

### 10. Uncertainty flag (Change 1 approach)

Prompt v1 asks the model for a numeric `confidence` (0.0–1.0) per prediction. Parsed confidence is compared to `Settings.uncertainty_threshold` (default documented in README). If top prediction confidence is below threshold, or confidence is missing/unparseable, `ObservationResult.uncertain` is set `True`.

**Reassess at implementation:** VLM confidence from structured output may be unreliable; when building task 4.2, evaluate alternatives (calibration, abstention prompts, score-free heuristics) before locking behaviour beyond the spec minimum.

### 11. Layer boundary enforcement (`import-linter`)

Use **`import-linter` 2.13** (dev dependency) with a root `.importlinter` config and contracts such as:

- **domain independence** — `plant_id.domain` must not import application, infrastructure, or interfaces
- **application independence** — `plant_id.application` must not import infrastructure or interfaces
- **infrastructure independence** — `plant_id.infrastructure` must not import application or interfaces
- **interfaces CLI independence** — `plant_id.interfaces.cli` must not import infrastructure (wiring lives in `interfaces.composition`)
- **interfaces CLI domain independence** — `plant_id.interfaces.cli` must not import domain (observation building and error mapping live in `interfaces.composition`)

Run via `uv run lint-imports` in CI and locally alongside ruff/pytest.

### 12. Hardware spike (task 1.6 — complete 2026-09-08)

Spike run on **Intel macOS** with Ollama 0.33.3 and `qwen3-vl:8b`:

| Metric | Result |
|---|---|
| Steady RAM | ~7 GB (Ollama) |
| Inference spike | ~+1 GB |
| Latency | Second run ≥2× faster than first |
| Outcome | **Keep `qwen3-vl:8b`** as default; task 4.2 unblocked |

**Integration notes for task 4.2:**

- Use Python `ollama.chat` / `images` array — not CLI path-in-prompt.
- Pass **absolute** image paths; do not rely on `~` expansion.
- Disable or hide thinking output for identification requests.
- Expect cold-start latency on first request after idle.

### 13. Pinned versions

Verified **2026-09-06**:

| Component | Version |
|---|---|
| Python | 3.14.7 |
| uv | 0.12.10 |
| ruff | 0.16.6 |
| pytest | 9.1.1 |
| import-linter | 2.13 |
| Pydantic | 2.13.5 |
| PyYAML | 6.0.3 |
| Pillow | 12.3.0 |
| ollama (Python) | 0.6.2 |
| rich | 14.3.2 |
| Ollama server | 0.33.3+ |
| Default vision model | **qwen3-vl:8b** — confirmed task 1.6 spike (Intel macOS, ~7 GB + ~1 GB spike) |

### 14. Dev experience

- `plant-id verify-env` — Ollama + model (VLM backend)
- `uv run lint-imports` — layer boundary contracts
- Fake `IdentificationRepository` for fast unit tests without Ollama
- `ApplicationEvents` recording test double for stage/event assertions

### 15. Application events (progress / observability)

Cross-cutting runtime events (pipeline stages, artifact saved, future structured logging) use a **domain port** with **context-local binding**:

| Piece | Location | Role |
|---|---|---|
| `ApplicationEvents` protocol | `domain/application_events.py` | `log_event`, `log_stage`, `log_wait`, session begin/end |
| `NoopApplicationEvents` | same | Default when nothing bound (tests, eval, library use) |
| `log_*` helpers | same | Callable from any layer without importing UI |
| `RichApplicationEvents` | `interfaces/cli/rich_events.py` | Rich spinners/colors on stderr (TTY only) |
| Binding | `interfaces/cli/progress.py` | `use_application_events(RichApplicationEvents())` for identify/demo |

**Rules:**

- Domain/application/infrastructure MAY call `log_event` / `log_stage` / `log_wait`; MUST NOT import Rich or write progress directly to stderr.
- CLI binds Rich presentation via `interfaces/cli/presentation.py`, which passes an `ApplicationEvents` handler into `execute_identify` in composition.
- `--quiet` skips binding (events remain no-op).
- `NO_COLOR=1` or non-TTY stderr → plain-text fallback inside `RichApplicationEvents`.

VLM repository emits four numbered stages (validate, build prompt, Ollama call with spinner, parse) when a handler is bound.

## Risks / Trade-offs

- **[Trade-off] More folders upfront** → pays off at backend swap and eval
- **[Risk] Composition root grows** → keep single `container.py` until HTTP justifies split
- **[Risk] Over-abstracting** → only two repository ports in Change 1; add more when needed

## Resolved decisions (design review 2026-09-06)

| Topic | Decision |
|---|---|
| Layer boundary enforcement | **`import-linter` 2.13** with `.importlinter` contracts |
| Species catalog | **`SpeciesCatalogRepository` port** + **`FileSpeciesCatalog`**; inject via composition (not into use case); path via `Settings.species_catalog_path` |
| Species labels | Bundled **`resources/species_catalog/default.txt`** (Oxford 102 vocabulary today); swap file via env; **`data/flowers/`** for images/eval only |
| Application events | **`ApplicationEvents` port** with context binding; Rich handler in CLI only; infra emits stages via `log_*` helpers |
| Uncertainty flag | Prompt-requested per-prediction confidence + `Settings.uncertainty_threshold`; reassess alternatives at task 4.2 |
| Hardware / model | **`qwen3-vl:8b` locked** after task 1.6 spike (Intel macOS); use `images` array + absolute paths in VLM repo |
| Domain validation | **Pydantic models** validate 1–3 photos at construction |
