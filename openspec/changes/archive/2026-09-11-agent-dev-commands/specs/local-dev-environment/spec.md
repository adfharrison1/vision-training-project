## ADDED Requirements

### Requirement: Agent slash commands documented for developers

The project SHALL document agent-agnostic slash commands alongside shell equivalents in developer-facing docs.

#### Scenario: README command index

- **WHEN** a developer reads the main README
- **THEN** they SHALL find a short section listing available agent slash commands, their canonical location under `agent/commands/`, and when to prefer them over typing raw `uv run` commands

#### Scenario: Distinction from OpenSpec commands

- **WHEN** slash command documentation is presented
- **THEN** it SHALL distinguish domain commands (`/eval-run`, `/verify`, etc.) from OpenSpec workflow commands (`/opsx-propose`, `/opsx-apply`, etc.) and SHALL NOT imply that domain commands require a specific agent host
