## ADDED Requirements

### Requirement: Bounded retry for empty or channel-misplaced JSON responses

When the first Ollama chat response cannot yield parseable identification JSON from `message.content`, the VLM repository SHALL apply a documented recovery policy before failing the observation.

#### Scenario: Empty content with JSON in thinking triggers retry

- **WHEN** the first response has empty or whitespace-only `message.content` and the `thinking` field contains text that parses as a JSON object with a `predictions` array
- **THEN** the system SHALL perform at most one additional Ollama chat call with the same images and base prompt plus a short corrective instruction to emit JSON in `content` only
- **AND** SHALL record that a retry occurred and the reason in the persisted raw artifact

#### Scenario: Retry succeeds with content JSON

- **WHEN** the retry response provides parseable JSON in `message.content`
- **THEN** the system SHALL parse and return the retry result as the observation outcome
- **AND** SHALL include both first and retry response metadata in the raw artifact

#### Scenario: Retry fails but thinking JSON fallback remains valid

- **WHEN** the retry still has empty `content` but the retry or first response has parseable JSON in `thinking`
- **THEN** the system SHALL parse from the fallback path and complete identification successfully (same as today’s thinking-json extract)
- **AND** SHALL record that fallback was used after retry

#### Scenario: Wholly empty or unparseable after retry

- **WHEN** after at most one retry neither `content` nor `thinking` yields parseable identification JSON
- **THEN** the system SHALL fail with `IdentificationError` and persist the raw responses for debugging

#### Scenario: Happy path unchanged

- **WHEN** the first response has parseable JSON in `message.content`
- **THEN** the system SHALL NOT perform a retry

#### Scenario: Retry limit

- **WHEN** a retry has already been attempted for the observation
- **THEN** the system SHALL NOT call Ollama again for that observation
