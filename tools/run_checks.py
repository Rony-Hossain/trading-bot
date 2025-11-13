# tools/run_checks.py
from __future__ import annotations
import subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def py(*args: str) -> int:
    return subprocess.run([sys.executable, *args], cwd=str(ROOT)).returncode

def main():
    print("== 1/3 Syntax ==")
    if py("-m", "tools.ci.check_syntax") != 0:
        return 2
    print("== 2/3 Import/Init ==")
    if py("-m", "tools.ci.check_imports") != 0:
        return 2
    print("== 3/3 Functionality ==")
    if py("-m", "tools.ci.check_functionality", "--platform", "quantconnect") != 0:
        return 2
    print("✅ All checks passed.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
