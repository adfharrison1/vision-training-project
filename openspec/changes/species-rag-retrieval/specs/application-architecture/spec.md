## ADDED Requirements

### Requirement: Species retrieval composition

Species retrieval backend selection and wiring SHALL occur in `interfaces/composition`, mirroring identification backend wiring. Application use cases SHALL depend on retrieval abstractions only when a future use case requires it; initial RAG inject MAY be composed entirely at the infrastructure prompt boundary without new use case methods.

#### Scenario: Swappable retrieval backend

- **WHEN** composition builds a retrieval repository with backend `describe-hybrid`
- **THEN** only infrastructure retrieval modules and settings SHALL differ from the `clip-prototype` wiring
