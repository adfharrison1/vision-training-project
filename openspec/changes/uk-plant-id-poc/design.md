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
                              ^
                         INFRASTRUCTURE
                         ==============
              VlmOllamaIdentificationRepository   <-- Change 1
              ClassicalMlIdentificationRepository <-- stub / Change 3
              FileArtifactRepository
              Oxford102SpeciesCatalog

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
| **domain** | Entities, value objects, repository Protocols, domain exceptions | stdlib, typing, pydantic models |
| **application** | Use cases (`IdentifyPlantUseCase`), DTOs if needed | domain |
| **infrastructure** | Repository implementations, Ollama client, file I/O, Oxford 102 loader | domain (+ third-party libs) |
| **interfaces** | CLI commands, future FastAPI routes | application, infrastructure (composition only) |

**Dependency rule:** dependencies point inward. Domain never imports outward.

### 2. Repository ports (domain)

```python
# domain/repositories.py

class IdentificationRepository(Protocol):
    @property
    def backend_id(self) -> str: ...

    def identify(self, observation: Observation) -> ObservationResult: ...


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
| `VlmOllamaIdentificationRepository` | Ollama multimodal, prompts, structured JSON → `ObservationResult`; receives injected `SpeciesCatalogRepository` |
| `FileArtifactRepository` | JSON artifacts under `artifacts/` |
| `Oxford102SpeciesCatalog` | Load 102 class names from bundled `resources/oxford102/class_names.txt` |

**Stub:** `ClassicalMlIdentificationRepository` — raises `NotImplementedError` or registered but disabled until Change 3.

### 5. Composition / dev wiring

```python
# infrastructure/composition/container.py

def build_identify_use_case(backend: Literal["vlm", "classical"], settings: Settings) -> IdentifyPlantUseCase:
    species_catalog = Oxford102SpeciesCatalog(settings.class_names_path)
    if backend == "vlm":
        id_repo = VlmOllamaIdentificationRepository(settings, species_catalog)
    elif backend == "classical":
        id_repo = ClassicalMlIdentificationRepository(settings, species_catalog)  # later
    artifact_repo = FileArtifactRepository(settings.artifacts_dir)
    return IdentifyPlantUseCase(id_repo, artifact_repo)
```

**Catalog injection:** `IdentifyPlantUseCase` does **not** depend on `SpeciesCatalogRepository`. The composition root builds `Oxford102SpeciesCatalog` once and injects it into identification repository implementations that need closed-set labels (VLM prompts now; classical ML label mapping later).

CLI:

```bash
plant-id identify --backend vlm --photos a.jpg,b.jpg
plant-id demo --backend vlm
```

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
└── oxford102/
    └── class_names.txt        # 102 canonical labels; no full dataset download required for demo

src/plant_id/
├── domain/
│   ├── models.py
│   ├── repositories.py      # Protocols
│   └── exceptions.py
├── application/
│   └── use_cases/
│       └── identify_plant.py
├── infrastructure/
│   ├── composition/
│   │   └── container.py
│   ├── identification/
│   │   ├── vlm_ollama.py
│   │   └── classical_ml.py  # stub
│   ├── persistence/
│   │   └── file_artifacts.py
│   ├── species/
│   │   └── oxford102.py
│   └── config/
│       └── settings.py
└── interfaces/
    └── cli/
        ├── main.py
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
- **interfaces thin** — interfaces may import application and infrastructure composition only (no direct Ollama imports in CLI modules)

Run via `uv run lint-imports` in CI and locally alongside ruff/pytest.

### 12. Hardware spike (deferred to task 1.6)

Do **not** lock the default vision model until task **1.6** is executed on the developer machine:

1. Install Ollama 0.33.3+ and pull candidate `qwen3-vl:8b`
2. Run a documented manual spike (one Oxford 102 sample image; note latency, RAM, quality)
3. If unusable on Intel hardware, document and configure an alternate model in `Settings`/README
4. Only then proceed with task 4.2 (live VLM integration)

Architecture scaffold (tasks 1–3, 5–6) may proceed in parallel; task 4.2 depends on spike outcome.

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
| Ollama server | 0.33.3+ |
| Default vision model (candidate) | qwen3-vl:8b — confirm via task 1.6 spike |

### 14. Dev experience

- `plant-id verify-env` — Ollama + model (VLM backend)
- `uv run lint-imports` — layer boundary contracts
- Fake `IdentificationRepository` and fake `SpeciesCatalogRepository` for fast unit tests without Ollama

## Risks / Trade-offs

- **[Trade-off] More folders upfront** → pays off at backend swap and eval
- **[Risk] Composition root grows** → keep single `container.py` until HTTP justifies split
- **[Risk] Over-abstracting** → only two repository ports in Change 1; add more when needed

## Resolved decisions (design review 2026-09-06)

| Topic | Decision |
|---|---|
| Layer boundary enforcement | **`import-linter` 2.13** with `.importlinter` contracts |
| Species catalog | **`SpeciesCatalogRepository` port**; inject `Oxford102SpeciesCatalog` into identification repos via composition (not into use case) |
| Oxford 102 labels | Bundled **`resources/oxford102/class_names.txt`**; Change 2 may also load from downloaded dataset |
| Uncertainty flag | Prompt-requested per-prediction confidence + `Settings.uncertainty_threshold`; reassess alternatives at task 4.2 |
| Hardware / model | Manual spike in **task 1.6** before locking default model; task 4.2 blocked until spike completes |
| Domain validation | **Pydantic models** validate 1–3 photos at construction |
