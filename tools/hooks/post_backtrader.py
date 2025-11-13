#!/usr/bin/env python3
"""
Post-build hook for Backtrader.

Runs with CWD set to the project root (see deploy_core._run_hook).
You can add linting, checksum writing, etc., here if desired.
"""
from pathlib import Path
from datetime import datetime

def main():
    out = Path("tools/hooks/_post_backtrader.log")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(f"[post] backtrader build at {datetime.utcnow().isoformat()}Z\n", encoding="utf-8")

if __name__ == "__main__":
    main()
