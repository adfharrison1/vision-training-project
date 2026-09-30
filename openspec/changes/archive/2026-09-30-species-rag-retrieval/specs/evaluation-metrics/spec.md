## ADDED Requirements

### Requirement: Retrieval quality metrics

Evaluation reports for retrieval runs SHALL include Recall@K (at configured K values) and mean reciprocal rank (MRR) for ground-truth species sheet retrieval, distinct from top-1/top-3 identification accuracy.

#### Scenario: Metric separation

- **WHEN** a retrieval eval report is written
- **THEN** it SHALL NOT conflate retrieval Recall@K with VLM misclassification counts
