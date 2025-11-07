# Framework Plan — Trading Bot Build & Test Framework

This document defines the architecture, components, and implementation plan for a small build/test/deploy framework for the Extreme-Aware Trading Strategy repository. The framework's goals are to provide reproducible builds for QuantConnect, local testability without the QuantConnect runtime, a reliable CLI, and a lightweight developer UI.

Version: 1.0
Date: 2025-11-07

---

## Objectives

- Provide a repeatable way to produce a QuantConnect-ready package (flattened folder) from the source tree.
- Allow running unit tests locally without the QuantConnect runtime by providing lightweight shims/stubs.
- Offer a CLI to perform build, clean, and inspection tasks.
- Provide an optional local UI (Streamlit) for developer ergonomics.
- Integrate with CI to run tests and build validation on push/PR.
- Keep secrets out of the repo and prevent accidental live deployments.

## High-level architecture

Components:

- tools/deploy_core.py (library): Build logic implemented as pure Python functions. This is callable from CLI, UI, and tests.
- tools/deploy_cli.py (CLI): User-facing command line that uses deploy_core functions. Supports subcommands: build, clean, list.
- tools/deploy_to_qc.py (compat): lightweight wrapper that calls deploy_core for backward compatibility.
- tools/ui_streamlit.py (optional): Streamlit app that imports deploy_core and exposes a small GUI.
- tests/shims/: Lightweight QC stubs used by pytest to import and run unit tests.
- tests/: Unit tests for config, cascade prevention, and other pure-Python logic.
- .github/workflows/ci.yml: CI workflow to run pytest and a dry-run build.
- quantconnect/: Generated folder (ignored by default) that is ready to upload to QuantConnect.

Dataflow:

1. Developer modifies code in `src/` and `config/`.
2. Developer runs `python -m tools.deploy_cli build` (or `deploy_to_qc.bat`).
3. CLI calls deploy_core.build_quantconnect(...). The function copies files, writes UPLOAD_ORDER.txt, and returns a result object describing the build.
4. The CLI prints results and optionally commits generated files (if --commit specified).
5. Developer runs pytest locally; tests import shims so modules depending on `AlgorithmImports` or `QCAlgorithm` don't fail.

## Design Principles

- Single source of truth: `tools/deploy_core.py` contains the copy/filter logic. CLI and UI call into it.
- Idempotence: `build` can be run multiple times; `--force` will overwrite quantconnect/.
- Safety: defaults to dry-run for sensitive actions like `--commit`. `OBSERVATION_MODE` remains the recommended default for runtime config.
- Minimal dependencies: prefer stdlib (argparse, pathlib, shutil). Optional UI uses Streamlit (documented separately).
- Testability: functions return data structures that tests can assert on, rather than just printing.


## Implementation Plan (tasks)

1. Refactor existing `tools/deploy_to_qc.py` into `tools/deploy_core.py` exposing functions:
   - build_quantconnect(root: Path, files: List[Tuple[Path,str]], docs: List[Tuple[Path,str]], dry_run: bool=False, force: bool=False, include: Optional[List[str]]=None) -> dict
   - clean_quantconnect(root: Path) -> bool
   - list_components() -> List[str]

2. Implement CLI `tools/deploy_cli.py` using argparse with subcommands:
   - build [--dry-run] [--include x,y] [--force] [--commit] [--message TEXT]
   - clean
   - list

3. Add unit-test shims in `tests/conftest.py` or `tests/shims/qc_stub.py` to mock:
   - `AlgorithmImports`: simple module exposing `QCAlgorithm` base class and helpers
   - Algorithm methods used by modules: `Log`, `Debug`, `Error`, `ObjectStore.Save`, `Portfolio` with attributes used (TotalPortfolioValue, Cash, etc.)

4. Add focused tests under `tests/`:
   - `tests/test_config.py`: instantiate Config with different versions and assert flags.
   - `tests/test_cascade_prevention.py`: test blocking logic across different violation combos.
   - `tests/test_deploy_core.py`: dry-run build returns expected file list (requires no QC runtime).

5. Add CI workflow `.github/workflows/ci.yml`:
   - Run on push/PR
   - Steps: checkout, setup-python 3.11, pip install -r requirements.txt, pytest -q, python -m tools.deploy_cli build --dry-run

6. Add developer docs (`docs/DEVELOPER.md`) describing environment setup, tests, and build commands.

7. Formalize dependencies with `requirements-dev.txt` for framework tools like `pytest` and `streamlit`.

8. (Enhancement) Move file-to-component mappings from Python lists into a `build.json` configuration file to make the framework data-driven.

9. (Enhancement) Implement support for a `.qcignore` file to allow custom exclusion patterns.
Optional:

- Add `--commit` to CLI that will run `git add quantconnect/ && git commit -m "build(qc): <timestamp>"` (opt-in only).
- Add `--upload` that integrates with QuantConnect API (future — needs secure token management).

## Output contract for build_quantconnect()

Return value (dict) fields:

- success: bool
- root: str (path to quantconnect folder)
- copied: list[str] (relative file names copied)
- skipped: list[str] (missing files or intentionally excluded)
- warnings: list[str]
- timestamp: ISO formatted string

This structured return makes the function easy to test and the CLI/ UI easy to render.

## Error handling

- The build function raises only for unexpected errors (IO errors). For missing source files it should not raise; instead, it records them in `skipped` and returns `success=False`.
- The CLI translates exceptions into user-friendly messages and returns non-zero exit codes.

## Security considerations
- Never commit secrets. The build process will ignore files matching patterns in a `.qcignore` file, which should include common secret patterns like `.env`, `secrets.json`, and `*credentials*.py`.
- The `--commit` flag is opt-in and should be used only on protected branches and by trusted CI or developers.

## Timeline & Milestones

- Day 0: Create core functions (deploy_core.py) and simple CLI wrapper (deploy_cli.py).
- Day 1: Add QC shims and basic tests (config + cascade tests).
- Day 2: Add CI workflow and docs, run through end-to-end.

---

If you approve this plan, I'll implement the first two items (deploy_core + CLI) and add a small test shim so tests can run. After that I'll add two unit tests and the CI file.
