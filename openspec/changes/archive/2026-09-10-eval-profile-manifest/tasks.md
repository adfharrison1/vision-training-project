## 1. Profile manifest

- [x] 1.1 Add `eval/profiles/quick.yaml` with eight species/image rows; verify smoke uses first four and quick uses eight distinct species
- [x] 1.2 Implement `eval/profile_manifest.py` load, select, and validation; verify unit tests pass

## 2. Dataset and runner

- [x] 2.1 Wire smoke/quick in `eval/dataset.py` to manifest; keep `full` on test-split enumeration; verify dataset unit tests pass
- [x] 2.2 Add `--profile-manifest` to `eval/run_oxford102.py`; verify runner unit tests pass

## 3. Documentation

- [x] 3.1 Update `eval/README.md` with manifest edit workflow and CLI flag

## 4. Agentic coding

- [x] 4.1 No AGENTS.md change required beyond existing eval profile docs
