## ADDED Requirements

### Requirement: Parallel eval Ollama setup documentation

The project SHALL document how to run optional multi-host eval sharding on a developer machine.

#### Scenario: Second Ollama server documented

- **WHEN** a developer reads eval or setup documentation
- **THEN** they SHALL find how to start an additional local Ollama server on a non-default port (for example `OLLAMA_HOST=127.0.0.1:11435 ollama serve`) and pass both URLs to the eval runner

#### Scenario: Sharded eval command documented

- **WHEN** a developer reads eval documentation
- **THEN** they SHALL find an example of a single eval invocation with `--workers 2` and `--ollama-hosts` that produces one merged JSON report

#### Scenario: Memory guidance for Intel Mac

- **WHEN** a developer reads parallel eval documentation
- **THEN** they SHALL find guidance that two concurrent `qwen3-vl:2b` loads on a 16 GB Intel Mac may require closing heavy apps and that Opik Docker may be left on or off at the developer's choice, with a note that memory pressure can erase expected speedups

#### Scenario: Default remains single worker

- **WHEN** parallel eval documentation is presented
- **THEN** it SHALL state that `--workers 1` is the default and recommended baseline for reproducibility and low memory use

#### Scenario: Opik Thread view documented

- **WHEN** a developer reads eval observability documentation
- **THEN** they SHALL find that eval traces with tracing enabled are grouped in Opik by `thread_id` equal to `--eval-run-id`, and that metadata filter `metadata.eval_run_id` remains valid for trace search

