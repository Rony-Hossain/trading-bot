# CLI Plan — Deploy & Build Command Line Interface

This document describes the CLI design and implementation details for the deploy/build tool used to produce a QuantConnect-ready package from the repository. The CLI is intended to be simple, cross-platform, and scriptable. It calls into a small library (`deploy_core`) so the logic can be reused by UIs and tests.

Version: 1.0
Date: 2025-11-07

---

## Goals

- Provide a friendly, well-documented command-line tool for building the `quantconnect/` package.
- Support reproducible builds and a dry-run mode for safe validation.
- Allow selective inclusion of components to support testing and trimmed uploads.
- Optionally commit generated artifacts to git (explicit --commit flag).
- Return machine-readable status (exit codes and JSON output option) for CI integration.

## CLI overview

Executable: `python -m tools.deploy_cli` or `deploy_to_qc.bat` on Windows.

Subcommands:

- build (default): create the `quantconnect/` folder with flattened files.
- clean: remove the `quantconnect/` folder.
- list: print the list of available components that can be included.

Global options:

- `--root PATH` : Root directory of the repository (default: project root where CLI runs).
- `--verbose` : Increase logging verbosity.
- `--json` : Output a machine-readable JSON summary at completion.

build options:

- `--dry-run` : Print what would be copied and where, but do not write files.
- `--include COMPONENTS` : Comma-separated list of additional components to include (by name). If omitted, use core list.
- `--exclude COMPONENTS` : Comma-separated list to exclude. Exclusions are processed after inclusions and always take precedence.
- `--force` : Overwrite an existing `quantconnect/` folder.
- `--commit` : After building, run `git add quantconnect/` and commit with a message. Use only in CI or by trusted devs.
- `--message MSG` : Custom commit message (default: `build(qc): <timestamp>`).

Return codes:

- 0 : success
- 1 : general error (short message printed)
- 2 : missing required files (build incomplete)
- 3 : commit failed (if --commit used)

CLI behaviour details

1. Execution flow for `build`:
   - Parse args
   - Resolve root path and component inclusion/exclusion lists
   - Validate source files exist for the requested components
   - If `--dry-run`: print the planned operations (files to be copied) and exit with code 0 (or 2 if required files missing)
   - If `--force` and `quantconnect/` exists: delete it
   - Create `quantconnect/` and copy files, preserving file names as defined in deploy_core
   - Write `UPLOAD_ORDER.txt` and any docs
   - Print summary and return success
   - If `--commit`: attempt to run `git add` and `git commit` and return code 3 on commit failure

2. JSON output (`--json`):
   - If requested, the CLI prints a JSON summary to stdout and suppresses verbose human-readable logging (but writes a short log file).
   - Example JSON fields: {"success": true, "root": "quantconnect", "copied": [...], "skipped": [...], "warnings": [...]}.

3. Dry-run behavior:
   - Validate all source file paths
   - List planned copies and report missing files
   - If missing files exist, dry-run should exit with code 2 and include missing files in JSON output if `--json` used

4. Commit behavior:
   - Only executed when `--commit` is present
   - Before building, the CLI will check if the git working tree is dirty (excluding the `quantconnect/` directory itself). If so, it will print a warning to prevent accidental inclusion of unrelated changes in the commit.
   - Stages the `quantconnect/` folder (git add) and commits with message given by `--message` or default
   - If repo has uncommitted changes outside of `quantconnect/`, do not alter them
   - If commit fails (no git, conflict, protected branch), CLI returns code 3 with explanation

Component naming and selection

- The CLI presents a canonical list of components (core and extras). Example:
  - core: config, logger, log_retrieval, universe_filter, extreme_detector, hmm_regime, avwap_tracker, risk_monitor, main
  - extras: cascade_prevention, dynamic_sizer, entry_timing

- Users can pass `--include cascade_prevention` to add extras.

- The `list` command will provide a detailed view of components:
  ```
  Available Components:
  [CORE]   config             (config/config.py)
  [CORE]   main               (src/main.py)
  [EXTRA]  cascade_prevention (src/components/cascade_prevention.py)
  [EXTRA]  pvs_monitor        (src/components/pvs_monitor.py)
  ```

Examples

- Default build (core components):
  ```bash
  python -m tools.deploy_cli build
  ```

- Dry-run including an extra component:
  ```bash
  python -m tools.deploy_cli build --dry-run --include cascade_prevention
  ```

- Build and commit generated files (use with care):
  ```bash
  python -m tools.deploy_cli build --force --commit --message "build(qc): package v1"
  ```

Logging and output

- Human-readable logging goes to stderr and includes progress messages.
- When `--json` provided, summary is printed to stdout as JSON for CI consumption.

Testing the CLI

- Create unit tests for `tools/deploy_core.build_quantconnect` behavior using a temporary directory (pytest tmp_path) and assert the returned dict and file system state.
- Create integration tests that call the CLI via `subprocess.run([...])` for dry-run and check output and exit codes.

CI integration

- CI job runs `python -m tools.deploy_cli build --dry-run --json` and fails if `success` is false or exit code is non-zero.

Error handling and UX

- Keep messages actionable: when a file is missing, show the path and how to fix (e.g., check src/ or run build from repo root).
- Exit codes should be documented and consistent so automation can react appropriately.

Extensibility

- The CLI should import and use `deploy_core` functions to keep logic testable and reusable by the UI.
- Add new component mappings to a single registry in `deploy_core` so both CLI/UI and tests use the same mapping.

---

If you approve this design I'll implement the CLI as described and add tests for dry-run + commit flag simulation (commit will be simulated in tests, not actually committed).
