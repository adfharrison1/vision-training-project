> **SUPERSEDED** — This document describes the original safety-equipment domain.
> The active project is **UK Plant Identification** (Oxford 102 Flowers).
> See `openspec/config.yaml` and `openspec/changes/uk-plant-id-poc/` for the
> current specification. Retained for historical reference only.

# Local Safety Equipment Installation Assessment --- Project Specification

## 1. Initial Brief

Build a **fully local, free-to-run multimodal LLM application** that
assesses a series of photographs taken from safety-equipment
installations at individual properties.

For each property, the system will receive:

- A set of installation photographs.
- A list of required safety items for that property.
- Specifications describing what constitutes acceptable evidence for
  each safety item. These specifications will be defined later.

The system must assess each required safety item individually against
the property's photographs and produce an overall result for the
property.

### Pass rule

A property passes **only when 100% of its required safety items are
confirmed as present and compliant with the defined evidence
requirements**.

Any required item that does not satisfy the pass condition causes the
overall property result to be **FAIL**.

The project is also intended as a learning exercise covering:

1.  Running and integrating a multimodal LLM locally.
2.  Structured vision-based assessment rather than conversational use of
    an LLM.
3.  Building a human-labelled evaluation dataset.
4.  Measuring model performance objectively.
5.  Using RAG to provide domain-specific safety-item requirements to the
    model.
6.  Using evaluation results to incrementally improve prompts,
    retrieval, models and system design.
7.  Understanding when fine-tuning might become appropriate.

### Constraints

- All inference should run locally.
- The software stack should be free/open-source.
- No paid LLM APIs should be required.
- The initial implementation should favour simple, explicit components
  over large AI frameworks.
- Python will be the primary implementation language.
- The system should be capable of evolving into a more production-like
  architecture without requiring that complexity initially.
- Fine-tuning is explicitly out of scope for the initial stages.

---

## 2. Core Domain Model

The top-level unit of assessment is a **Property**.

A property has:

- A unique property identifier.
- One or more installation photographs.
- A set of required safety items.
- An assessment result for every required item.
- An overall PASS/FAIL result.

Conceptually:

```text
Property
│
├── Photos
│   ├── photo-001.jpg
│   ├── photo-002.jpg
│   └── ...
│
├── Required Safety Items
│   ├── Item A
│   ├── Item B
│   └── Item C
│
├── Item Assessments
│   ├── Item A → PRESENT
│   ├── Item B → PRESENT
│   └── Item C → PRESENT
│
└── Property Result → PASS
```

If instead:

```text
Item A → PRESENT
Item B → ABSENT
Item C → PRESENT
```

then:

```text
Property Result → FAIL
```

The overall property result is therefore **deterministic application
logic**, not an LLM judgement.

The LLM determines the evidence/status of individual safety items.
Application code calculates whether the property passes.

---

## 3. Assessment Status Model

The initial status vocabulary should distinguish lack of evidence from
evidence of absence.

Each required item should receive exactly one status:

### `PRESENT`

Sufficient photographic evidence exists to confirm that the required
item is present and satisfies the currently defined visual requirements.

### `ABSENT`

The relevant area is sufficiently visible and the required item is not
present.

### `NOT_VISIBLE`

The supplied photographs do not provide enough coverage to determine
whether the required item is present.

### `UNCERTAIN`

Something potentially matching the required item is visible, but the
model cannot identify or assess it reliably enough.

The initial property pass rule is:

```text
PASS = every required item has status PRESENT
```

Therefore:

```text
PRESENT       → item passes
ABSENT        → item fails
NOT_VISIBLE   → item fails
UNCERTAIN     → item fails
```

This deliberately makes the system conservative.

A lack of photographic evidence must never be converted into a
successful assessment.

---

## 4. Example Structured Result

The LLM-facing assessment should produce structured data rather than
free-form prose.

Example:

```json
{
  "property_id": "property-001",
  "items": [
    {
      "requirement_id": "safety-item-a",
      "status": "PRESENT",
      "evidence": [
        {
          "photo": "photo-003.jpg",
          "description": "Required safety item is clearly visible on the wall adjacent to the entrance."
        }
      ]
    },
    {
      "requirement_id": "safety-item-b",
      "status": "NOT_VISIBLE",
      "evidence": [],
      "reason": "None of the supplied photographs show the area in which this item could be verified."
    }
  ]
}
```

Application code then derives:

```json
{
  "property_id": "property-001",
  "passed_items": 1,
  "required_items": 2,
  "completion_rate": 0.5,
  "result": "FAIL"
}
```

The `completion_rate` is useful for reporting and analysis, but **does
not create a partial-pass state**.

Only `1.0` / `100%` is PASS.

---

# Stage 1 --- Local Multimodal Proof of Concept

## Goal

Prove that a locally running vision-language model can inspect
installation photographs and return useful structured observations.

## Scope

Install and run a multimodal model locally using Ollama.

Initial candidate:

```text
Qwen2.5-VL 7B
```

Alternative models may be evaluated later.

Create a minimal Python application capable of:

```python
inspect_photo("photo.jpg")
```

and sending the image to the local model.

Initially ask simple questions such as:

- What safety-related objects are visible?
- Where in the image are they?
- What visual evidence supports the identification?

## Suggested stack

- Python
- Ollama
- Qwen2.5-VL or another suitable locally runnable VLM
- Pydantic
- Pillow
- pytest

## Deliverables

- Local model installation instructions.
- Minimal Python client.
- Ability to submit one or more photographs.
- Pydantic response schema.
- Structured JSON output.
- A small collection of representative installation photographs.

## Learning objectives

Understand:

- Local LLM/VLM inference.
- Multimodal prompts.
- Image input handling.
- Model context limitations.
- Structured output.
- Model latency and hardware constraints.
- Hallucination and uncertainty in visual models.

## Exit criteria

The application can reliably send installation photographs to a local
VLM and parse the response into a validated Python object.

No RAG is required.

---

# Stage 2 --- Property and Requirement Assessment

## Goal

Move from generic image description to the actual domain problem.

The system should assess a complete property containing multiple
photographs against a predefined list of required safety items.

## Proposed interface

```python
assessment = assess_property(
    property_id="property-001",
    photos=[
        "front-room.jpg",
        "hallway.jpg",
        "kitchen.jpg",
        "landing.jpg",
    ],
    required_items=[
        "safety-item-a",
        "safety-item-b",
        "safety-item-c",
    ],
)
```

## Requirement definitions

At this stage, requirements can be represented using static
Python/JSON/YAML configuration.

For example:

```yaml
id: safety-item-a
name: Safety Item A

description: >
  Placeholder description. Detailed specification to be supplied later.

visual_indicators:
  - placeholder

acceptable_variants:
  - placeholder

exclusions:
  - placeholder
```

The exact safety items and their acceptance criteria are explicitly
**TBD**.

## Assessment behaviour

For every required item, the model must independently return:

```text
PRESENT
ABSENT
NOT_VISIBLE
UNCERTAIN
```

It must also identify which photograph(s) contain supporting evidence
where applicable.

## Property decision

Property-level status must be calculated in normal application code:

```python
passed = all(
    item.status == Status.PRESENT
    for item in assessment.items
)
```

The LLM should **not** be asked to decide whether the property passes.

## Deliverables

- Property input model.
- Requirement model.
- Item assessment model.
- Property assessment model.
- Deterministic property pass/fail calculation.
- Support for multiple photographs per property.
- Persistence of raw model responses for debugging.

## Exit criteria

A property containing multiple photographs and multiple requirements can
be processed end-to-end and produces:

- One assessment per requirement.
- Evidence references.
- A deterministic overall PASS/FAIL.

---

# Stage 3 --- Build the Evaluation Dataset

## Goal

Create objective ground truth against which system performance can be
measured.

This stage should happen **before introducing RAG**.

## Dataset structure

Example:

```text
eval/
├── property-001/
│   ├── photos/
│   │   ├── 001.jpg
│   │   ├── 002.jpg
│   │   └── 003.jpg
│   ├── requirements.json
│   └── expected.json
│
├── property-002/
│   └── ...
│
└── property-003/
    └── ...
```

`expected.json` contains human-labelled ground truth.

Example:

```json
{
  "items": {
    "safety-item-a": "PRESENT",
    "safety-item-b": "ABSENT",
    "safety-item-c": "NOT_VISIBLE"
  },
  "property_result": "FAIL"
}
```

## Initial target

Create approximately **30--50 representative properties**.

The dataset should deliberately contain:

- Clear positive examples.
- Clear negative examples.
- Poor-quality photographs.
- Partial visibility.
- Occlusion.
- Different viewing angles.
- Different lighting.
- Visually similar objects.
- Different valid equipment variants.
- Properties with complete evidence.
- Properties with exactly one missing item.
- Properties with several missing items.

## Metrics

At minimum measure:

- Accuracy.
- Precision.
- Recall.
- F1.
- False-positive rate.
- False-negative rate.
- Confusion matrix.

Metrics should be calculated:

- Globally.
- Per requirement type.
- Per status.
- At property PASS/FAIL level.

Because PASS requires 100%, property-level false positives are
particularly important.

## Deliverables

- Versioned evaluation dataset.
- Python evaluation runner.
- Machine-readable results.
- Human-readable summary.
- Per-requirement metrics.
- Property-level metrics.

## Exit criteria

A single command can run the current system against the entire labelled
dataset and produce reproducible metrics.

---

# Stage 4 --- Establish and Improve the Baseline

## Goal

Create a measurable baseline before adding retrieval.

Example experiment:

```text
Model:        Qwen2.5-VL 7B
Prompt:       v1
RAG:          none
Dataset:      v1
Temperature:  fixed
```

Store each experiment's:

- Model.
- Model version.
- Quantisation.
- Prompt version.
- Configuration.
- Dataset version.
- Individual predictions.
- Latency.
- Aggregate metrics.

Example:

```text
Experiment: baseline-v1

Item accuracy:             84%
Item recall:               79%
Item precision:            91%
Property pass/fail:        88%
False property passes:      3
False property failures:    5
```

## Failure analysis

Incorrect cases should be categorised manually.

Possible categories:

```text
object not recognised
object confused with another object
insufficient image resolution
occlusion
incorrect ABSENT vs NOT_VISIBLE
incorrect requirement interpretation
model ignored requirement
model hallucinated evidence
structured-output failure
```

## Regression dataset

Every meaningful real-world failure should become a permanent regression
case where legally and practically possible.

## Deliverables

- Baseline metrics.
- Experiment storage format.
- Prompt versioning.
- Failure categorisation.
- Regression-test process.

## Exit criteria

Changes to prompts or models can be objectively compared against the
baseline rather than judged subjectively.

---

# Stage 5 --- Introduce Requirement RAG

## Goal

Use retrieval to provide the vision model with detailed, domain-specific
information describing what constitutes valid evidence for each safety
requirement.

RAG should answer:

> **What exactly am I looking for and what counts as acceptable?**

The VLM should answer:

> **Does the photographic evidence satisfy that requirement?**

## Requirement knowledge

A mature requirement might contain:

```yaml
id: safety-item-a

name: Safety Item A

description: >
  Domain-specific description.

required_characteristics:
  - characteristic A
  - characteristic B

visual_indicators:
  - indicator A
  - indicator B

acceptable_variants:
  - variant A
  - variant B

not_acceptable:
  - condition A
  - condition B

do_not_confuse_with:
  - visually similar object A
  - visually similar object B

reference_images:
  - examples/valid-001.jpg
  - examples/valid-002.jpg
```

Actual safety-equipment specifications will be added later.

## Initial retrieval implementation

Do **not** immediately introduce a vector database.

If requirement IDs are known, direct lookup is preferable:

```python
requirement = requirements[requirement_id]
```

This provides a simple baseline for assessing whether additional
requirement context improves vision performance.

## Deliverables

- Requirement knowledge format.
- Retrieval interface.
- Requirement context added to VLM prompts.
- RAG-enabled experiment.
- Comparison against the no-RAG baseline.

## Exit criteria

The evaluation suite demonstrates whether domain context improves
assessment accuracy.

---

# Stage 6 --- Semantic Retrieval and Vector Search

## Goal

Learn conventional embedding-based RAG and support larger or less
structured requirement libraries.

## Proposed stack

Add:

- `sentence-transformers`
- Qdrant
- Docker Compose

Conceptually:

```text
Requirement documents
        │
        ▼
Embedding model
        │
        ▼
     Qdrant
        │
        ▼
Relevant requirement context
        │
        ▼
Vision model + photographs
```

## Retrieval evaluation

Retrieval should be evaluated independently from visual assessment.

Metrics may include:

- Recall@1.
- Recall@3.
- Mean Reciprocal Rank.
- Correct requirement/context retrieved.

This separates:

```text
retrieval failure
```

from:

```text
vision/reasoning failure
```

## Deliverables

- Local Qdrant instance.
- Requirement indexing process.
- Local embedding model.
- Semantic retrieval.
- Retrieval evaluation suite.
- End-to-end RAG evaluation.

## Exit criteria

Retrieval quality and downstream vision quality can be measured
independently.

---

# Stage 7 --- Evaluation-Driven Improvement Loop

## Goal

Turn the prototype into a system that improves systematically from
observed failures.

The core lifecycle becomes:

```text
             ┌───────────────┐
             │ Run eval suite│
             └───────┬───────┘
                     ▼
              Analyse failures
                     │
                     ▼
              Form hypothesis
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
   Improve prompt/RAG      Try another model
          │                     │
          └──────────┬──────────┘
                     ▼
                Run evals
                     │
                     ▼
             Compare results
                     │
                     ▼
          Add failures to dataset
                     │
                     └──────────────► repeat
```

## Experiment examples

Test changes independently where possible:

- Better requirement descriptions.
- Additional visual indicators.
- Explicit negative examples.
- Different prompt structures.
- Different image resolutions.
- Individual-image vs multi-image assessment.
- Two-stage detection and verification.
- Alternative local VLMs.
- Different quantisations.
- Reference-image prompting.
- Different retrieval strategies.

## Important rule

A change is considered an improvement only if it improves relevant
evaluation metrics without causing unacceptable regressions elsewhere.

## Deliverables

- Repeatable experiment process.
- Experiment comparison reports.
- Growing regression dataset.
- Documented failure taxonomy.

---

# Stage 8 --- Observability and Evaluation Tooling

## Goal

Introduce dedicated LLM tooling once custom JSON/files become
cumbersome.

Potential local/open-source tools include:

- DeepEval for evaluation.
- Langfuse for tracing, datasets, prompt versions and experiments.

These are deliberately deferred so the fundamental mechanics are
understood first.

## Desired observability

For every property assessment, eventually capture:

```text
property
    │
    ├── requirements retrieved
    ├── photos supplied
    ├── model
    ├── prompt version
    ├── model inputs
    ├── raw model output
    ├── parsed assessment
    ├── item statuses
    ├── property decision
    ├── latency
    └── evaluation scores where ground truth exists
```

## Deliverables

- Local tracing.
- Dataset management.
- Experiment comparison.
- Prompt version tracking.
- Searchable historical assessments.

---

# Stage 9 --- Production-Shaped Local Application

## Goal

Turn the learning prototype into a clean local service while retaining
the ability to run the entire system for free.

Possible architecture:

```text
                         ┌─────────────────┐
                         │ Property photos │
                         └────────┬────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │     FastAPI     │
                         └────────┬────────┘
                                  │
                   ┌──────────────┴──────────────┐
                   │                             │
                   ▼                             ▼
             Requirement RAG                Local VLM
                Qdrant                       Ollama
                   │                             │
                   └──────────────┬──────────────┘
                                  ▼
                           Item assessments
                                  │
                                  ▼
                         Deterministic rules
                                  │
                                  ▼
                        Property PASS / FAIL
                                  │
                                  ▼
                        Results / observability
```

## Local deployment

Target:

```bash
docker compose up
```

Potential services:

```text
app
ollama
qdrant
postgres
langfuse
```

Not all services need to be introduced immediately.

Kubernetes is explicitly unnecessary for the learning implementation.

---

# Stage 10 --- Investigate Fine-Tuning

## Goal

Determine whether RAG, prompting and model selection have reached a
performance ceiling that justifies adapting model weights.

Fine-tuning should only be investigated once:

- A substantial labelled dataset exists.
- Baseline performance is well understood.
- Failure modes are categorised.
- RAG quality is measured.
- Prompt improvements have plateaued.
- Multiple suitable local models have been evaluated.

Possible future techniques include:

- LoRA.
- QLoRA.
- Supervised fine-tuning.
- Vision-language fine-tuning where supported.

The existing evaluation suite must remain the authority for determining
whether fine-tuning actually improves the system.

Fine-tuning is **not a requirement for project success**.

---

# 5. Safety and Decision Semantics

Because the application deals with safety-equipment evidence, false
confidence is particularly undesirable.

The system should therefore follow these principles:

### Evidence over inference

An item passes because the photographs contain sufficient evidence, not
because the model believes it is likely to exist.

### Missing evidence fails

`NOT_VISIBLE` cannot produce a property PASS.

### Uncertainty fails

`UNCERTAIN` cannot produce a property PASS.

### Property decisions are deterministic

The LLM cannot override the 100% rule.

### Evidence should be auditable

Where practical, every `PRESENT` judgement should reference the
photograph(s) that provide the evidence.

### Confidence is not ground truth

If numerical model confidence is introduced, it should not initially be
treated as a calibrated probability.

---

# 6. Proposed Repository Structure

Initial structure:

```text
safety-installation-assessor/
│
├── README.md
├── pyproject.toml
│
├── src/
│   └── assessor/
│       ├── models.py
│       ├── ollama.py
│       ├── prompts.py
│       ├── assessment.py
│       ├── requirements.py
│       └── scoring.py
│
├── requirements/
│   ├── safety-item-a.yaml
│   ├── safety-item-b.yaml
│   └── safety-item-c.yaml
│
├── eval/
│   ├── datasets/
│   │   └── v1/
│   └── runner.py
│
├── experiments/
│   ├── baseline-v1/
│   └── ...
│
├── tests/
│   ├── unit/
│   └── integration/
│
├── docker/
│   └── ...
│
└── docker-compose.yml
```

The structure should evolve only when required.

---

# 7. Initial Technology Choices

## Stage 1--4

```text
Python
Pydantic
Ollama
Qwen2.5-VL 7B (initial candidate)
Pillow
pytest
SQLite / filesystem
```

## Stage 5--7

Add:

```text
sentence-transformers
Qdrant
Docker Compose
```

## Stage 8+

Potentially add:

```text
DeepEval
Langfuse
PostgreSQL
FastAPI
```

Avoid initially:

```text
LangChain
LlamaIndex
Kubernetes
agents
fine-tuning
complex orchestration frameworks
```

The intention is to expose rather than hide the mechanics of multimodal
inference, RAG and evaluation.

---

# 8. Key Success Metrics

The project should ultimately answer four separate questions.

## 1. Item recognition

How accurately can the system determine whether each required safety
item is evidenced in the photographs?

## 2. Property assessment

How accurately does the resulting 100%-required rule classify complete
properties as PASS or FAIL?

## 3. Retrieval

Does RAG retrieve the correct specification and supporting information
for each requirement?

## 4. Improvement

Can changes to prompts, requirement knowledge, retrieval or models
demonstrate measurable improvement against a stable evaluation dataset?

The primary success criterion is not:

> "The LLM gives convincing answers."

It is:

> **The system produces reproducibly accurate safety-item assessments,
> with auditable evidence, and changes to the system can be objectively
> measured against human-labelled ground truth.**

---

# 9. Immediate First Milestone

The first milestone should remain intentionally small.

Build a Python program that:

1.  Connects to a locally running Ollama instance.
2.  Sends several photographs belonging to one property to a local
    multimodal model.
3.  Supplies three placeholder safety requirements.
4.  Requests one of `PRESENT`, `ABSENT`, `NOT_VISIBLE`, or `UNCERTAIN`
    for each requirement.
5.  Validates the response with Pydantic.
6.  Records which photographs provide evidence.
7.  Calculates PASS only when every required item is `PRESENT`.
8.  Saves the complete input and output for later evaluation.

No embeddings.

No vector database.

No RAG framework.

No Langfuse.

No fine-tuning.

Once this works, **Stage 3's evaluation dataset should be created before
significant effort is spent making the model appear more accurate**.
That gives every subsequent change a measurable baseline.
