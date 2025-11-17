"""
Backward-compatibility wrapper for the build script.

Usage:
  python tools/deploy_to_qc.py

This script calls the new core deployment logic to produce a QuantConnect-ready
folder. It is maintained for any existing workflows that might call it directly.
For new features, use `python -m tools.deploy_cli`.
"""
from __future__ import annotations
from pathlib import Path
import sys

import deploy_core


def main():
    print("\n=== Building QuantConnect package ===\n")
    root_dir = Path(__file__).resolve().parents[1]
    result = deploy_core.build_quantconnect(root_dir=root_dir, dry_run=False , force=True)

    if not result["success"]:
        print("Build failed. Warnings:", file=sys.stderr)
        for warning in result["warnings"]:
            print(f"  - {warning}", file=sys.stderr)
        sys.exit(1)

    print("\n✅ Deployment package ready at: {}".format(result['root']))
    print("\nUpload the files to QuantConnect in the order listed in UPLOAD_ORDER.txt")
    print("Use Paper Trading for any live deployments.\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Build failed: {e}", file=sys.stderr)
        sys.exit(1)
