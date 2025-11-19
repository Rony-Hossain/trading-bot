# tools/run_checks.py
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from tools.qc_init_smoke import run_qc_init_smoke

ROOT = Path(__file__).resolve().parents[1]


def py(*args: str) -> int:
    """Run a Python module/command in repo root."""
    return subprocess.run([sys.executable, *args], cwd=str(ROOT)).returncode


def run_qc_init_phase() -> bool:
    """Run the QC-style Initialize() smoke test against dist/quantconnect."""
    print("== 4/4 QC Init Smoke ==")
    dist_root = ROOT / "dist" / "quantconnect"

    try:
        run_qc_init_smoke(dist_root)
        print("QC init smoke: Initialize() completed without exception.")
        return True
    except Exception as e:
        print(f"QC init smoke FAILED: {e}")
        return False


def main() -> int:
    # 1) Syntax
    print("== 1/4 Syntax ==")
    if py("-m", "tools.ci.check_syntax") != 0:
        return 2

    # 2) Import / init (module wiring)
    print("== 2/4 Import/Init ==")
    if py("-m", "tools.ci.check_imports") != 0:
        return 2

    # 3) Functionality (unit tests + existing smoke harness)
    print("== 3/4 Functionality ==")
    if py("-m", "tools.ci.check_functionality", "--platform", "quantconnect") != 0:
        return 2

    # 4) QC init smoke (build dist + run Initialize() in dist layout)
    #    This makes sure the *built* QC package actually initializes, which is
    #    where you were seeing the Config / ctor signature errors.
    if py("-m", "tools.deploy_cli", "build", "--platform", "quantconnect", "--force") != 0:
        print("QC build step failed; skipping init smoke.")
        return 2

    if not run_qc_init_phase():
        return 2

    print("✅ All checks (including QC Initialize) passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
