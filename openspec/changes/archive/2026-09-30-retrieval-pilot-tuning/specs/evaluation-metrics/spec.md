## ADDED Requirements

### Requirement: Per-class retrieval metrics in eval reports

Full identify and retrieval-only eval JSON reports SHALL include an additive `retrieval_per_class` (or equivalent) map keyed by ground-truth `catalog_label` with at least observation count and Recall@K hit counts or rates for configured K values, without removing or renaming existing identify `per_class` fields.

#### Scenario: Full identify report unchanged for VLM metrics

- **WHEN** a full identify eval report is written
- **THEN** existing top-1/top-3 identify fields and `per_class` SHALL remain semantically unchanged; retrieval per-class data SHALL be additional keys only

#### Scenario: Retrieval-only report

- **WHEN** a retrieval-only report is written
- **THEN** per-class retrieval summary SHALL be present even when VLM identify metrics are absent
