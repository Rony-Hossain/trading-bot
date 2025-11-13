#!/usr/bin/env python3
"""
Pre-build hook for Backtrader.

Runs with CWD set to the project root (see deploy_core._run_hook).
Keep it fast and side-effect-light.
"""
from pathlib import Path
from datetime import datetime

def main():
    out = Path("tools/hooks/_pre_backtrader.log")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(f"[pre] backtrader build at {datetime.utcnow().isoformat()}Z\n", encoding="utf-8")

if __name__ == "__main__":
    main()
