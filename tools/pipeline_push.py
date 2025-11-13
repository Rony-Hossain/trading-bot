# tools/pipeline_push.py
from __future__ import annotations

import argparse
import json
import os
import py_compile
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Tuple
from zipfile import ZipFile, ZIP_DEFLATED

# Local imports
sys.path.insert(0, str(Path(__file__).resolve().parent))
import deploy_core  # noqa: F401


ROOT = Path(__file__).resolve().parents[1]


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _iter_py_files(dirs: Iterable[Path]) -> Iterable[Path]:
    seen = set()
    for base in dirs:
        base = base.resolve()
        if not base.exists():
            continue
        for p in base.rglob("*.py"):
            # skip caches
            if "__pycache__" in p.parts:
                continue
            # de-dup
            rp = p.resolve()
            if rp in seen:
                continue
            seen.add(rp)
            yield p


def _syntax_check(paths: Iterable[Path]) -> Tuple[bool, List[str]]:
    """Return (ok, errors). Uses stdlib py_compile to catch SyntaxError."""
    errors: List[str] = []
    for p in paths:
        try:
            py_compile.compile(str(p), doraise=True)
        except Exception as e:
            errors.append(f"{p}: {e}")
    return (len(errors) == 0, errors)


def _run_unit_tests(root: Path) -> Tuple[bool, str]:
    """
    Try pytest; if unavailable or failing to start, fallback to unittest discover.
    Returns (ok, log_excerpt).
    """
    # Try pytest quietly
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "tools/tests"],
            cwd=str(root), text=True, capture_output=True
        )
        if proc.returncode == 0:
            return True, proc.stdout.strip() or "pytest: ok"
        # If pytest exists but tests failed, return failure
        if "pytest" in (proc.stderr or "").lower() or "pytest" in (proc.stdout or "").lower():
            return False, (proc.stdout + "\n" + proc.stderr)[-2000:]
    except Exception:
        pass

    # Fallback to unittest discover
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", "tools/tests"],
            cwd=str(root), text=True, capture_output=True
        )
        if proc.returncode == 0:
            return True, proc.stdout.strip() or "unittest: ok"
        return False, (proc.stdout + "\n" + proc.stderr)[-2000:]
    except Exception as e:
        return False, f"unit test run failed to start: {e}"


def _zip_dir(src_dir: Path, zip_path: Path):
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(zip_path, "w", compression=ZIP_DEFLATED) as z:
        for p in src_dir.rglob("*"):
            if p.is_file():
                z.write(p, p.relative_to(src_dir))


def _write_qc_readme(out_dir: Path):
    readme = out_dir / "README_QC.txt"
    lines = [
        "QuantConnect Upload Notes",
        "=========================",
        "",
        "1) In QuantConnect Web IDE, create/open your project.",
        "2) Ensure your main algorithm file is named main.py (generated here).",
        "3) Upload the files in the order in UPLOAD_ORDER.txt if prompted.",
        "4) Max 32,000 chars per file (split + facade are generated automatically if needed).",
        "5) Remove emojis/invalid unicode if any warning appears in build stats.",
        "",
        f"Generated at: {_ts()}",
        ""
    ]
    readme.write_text("\n".join(lines), encoding="utf-8")


def _print_next_steps(platform: str, zip_path: Path):
    if platform == "quantconnect":
        msg = (
            "\nNext steps (QuantConnect):\n"
            "  • Open QuantConnect Web IDE → your project → drag-and-drop the ZIP, or upload following UPLOAD_ORDER.txt.\n"
            "  • The builder already split any oversized files and created a facade main.py if needed.\n"
        )
    elif platform == "backtrader":
        msg = (
            "\nNext steps (Backtrader):\n"
            "  • Unzip into your Backtrader project or container and run your entry script (e.g., bt_bundle.py).\n"
        )
    elif platform == "zipline":
        msg = (
            "\nNext steps (Zipline):\n"
            "  • Unzip into your Zipline environment/repo and run your entry script.\n"
        )
    elif platform == "freqtrade":
        msg = (
            "\nNext steps (Freqtrade):\n"
            "  • Unzip into your Freqtrade user_data directory as appropriate.\n"
        )
    else:
        msg = "\nNext steps: Unzip and integrate into the target environment.\n"

    print(f"\n✅ Package ready: {zip_path}")
    print(msg)


def main():
    ap = argparse.ArgumentParser(description="Preflight → Build → Package to release/ (stdlib-only)")
    ap.add_argument("--platform", type=str, default="quantconnect",
                    choices=["quantconnect", "backtrader", "zipline", "freqtrade"])
    ap.add_argument("--platform-config", type=Path, default=ROOT / "tools" / "platforms.json")
    ap.add_argument("--force", action="store_true", help="Overwrite dist/<platform> if exists.")
    ap.add_argument("--minify", action="store_true", help="AST minify.")
    ap.add_argument("--tree-shake", action="store_true", help="Static tree-shake.")
    ap.add_argument("--bundle", action="store_true", help="Bundle when platform allows it.")
    ap.add_argument("--bundle-name", type=str, default="strategy.py", help="Bundle filename (.py or .py.gz).")
    ap.add_argument("--include", type=str, default="", help="Comma-separated components to include.")
    ap.add_argument("--exclude", type=str, default="", help="Comma-separated components to exclude.")
    ap.add_argument("--dry-run", action="store_true", help="Build simulation only (no writes).")
    ap.add_argument("--json", action="store_true", help="Print build JSON result.")
    ap.add_argument("--stats-file", type=Path, default=None, help="Write stats json.")

    # Preflight controls
    ap.add_argument("--no-tests", dest="run_tests", action="store_false", help="Skip unit tests.")
    ap.add_argument("--run-tests", dest="run_tests", action="store_true", help="Run unit tests (default).")
    ap.set_defaults(run_tests=True)
    ap.add_argument("--preflight-only", action="store_true", help="Run checks, skip build/package.")
    ap.add_argument("--fail-on-warn", action="store_true", help="Treat build warnings as errors.")
    args = ap.parse_args()

    include = [s.strip() for s in args.include.split(",") if s.strip()]
    exclude = [s.strip() for s in args.exclude.split(",") if s.strip()]

    # -------------------- PREFLIGHT: Syntax/compile --------------------
    print("== Preflight: syntax/compile checks ==")
    py_files = list(_iter_py_files([ROOT / "src", ROOT / "config"]))
    ok, errs = _syntax_check(py_files)
    if not ok:
        print("❌ Syntax/compile errors detected:")
        for e in errs:
            print("  -", e)
        return 2
    print(f"✓ Syntax OK ({len(py_files)} files)")

    # -------------------- PREFLIGHT: Unit tests -----------------------
    if args.run_tests:
        print("== Preflight: unit tests ==")
        ok, log = _run_unit_tests(ROOT)
        print(log)
        if not ok:
            print("❌ Tests failed.")
            return 2
        print("✓ Tests OK")
    else:
        print("== Preflight: unit tests skipped ==")

    # -------------------- PREFLIGHT: Dry-run build --------------------
    print("== Preflight: dry-run build validation ==")
    dry_run_result = deploy_core.build_for_platform(
        root_dir=ROOT,
        platform=args.platform,
        platform_config=args.platform_config,
        dry_run=True,
        force=True,
        minify=args.minify,
        tree_shake=args.tree_shake,
        bundle=args.bundle,
        bundle_name=args.bundle_name,
        include=include,
        exclude=exclude,
        verbose=True,
        log_max_chars=300,  # compact logs for preflight
    )

    if args.json:
        print(json.dumps({"preflight": dry_run_result}, indent=2))

    if not dry_run_result["success"]:
        print("❌ Dry-run build failed.")
        print(json.dumps(dry_run_result["stats"], indent=2))
        return 2

    warns = dry_run_result["stats"].get("warnings", [])
    if warns:
        print("\n⚠️  Build warnings:")
        for w in warns:
            print("  -", w)
        if args.fail_on_warn:
            print("❌ Failing due to --fail-on-warn.")
            return 2
    else:
        print("✓ No build warnings")

    if args.preflight_only:
        print("\n✅ Preflight completed. (preflight-only: skipping build/package)")
        return 0

    # --------------------------- REAL BUILD ---------------------------
    print("\n== Build: live ==")
    result = deploy_core.build_for_platform(
        root_dir=ROOT,
        platform=args.platform,
        platform_config=args.platform_config,
        dry_run=args.dry_run,
        force=args.force,
        minify=args.minify,
        tree_shake=args.tree_shake,
        bundle=args.bundle,
        bundle_name=args.bundle_name,
        include=include,
        exclude=exclude,
        verbose=True,
    )

    if args.json:
        print(json.dumps(result, indent=2))

    if not result["success"]:
        print("\n❌ Build failed.")
        print(json.dumps(result["stats"], indent=2))
        return 2

    out_dir = Path(result["root"])
    if args.platform == "quantconnect" and not args.dry_run:
        _write_qc_readme(out_dir)

    if args.stats_file:
        try:
            args.stats_file.parent.mkdir(parents=True, exist_ok=True)
            args.stats_file.write_text(json.dumps(result["stats"], indent=2), encoding="utf-8")
        except Exception as e:
            print(f"[warn] Failed to write stats file: {e}", file=sys.stderr)

    if args.dry_run:
        print("\n[Dry-run] Skipping packaging step.")
        return 0

    # --------------------------- PACKAGE ZIP --------------------------
    print("\n== Package: zip ==")
    release_dir = ROOT / "release"
    zip_name = f"{args.platform}-{_ts()}.zip"
    zip_path = release_dir / zip_name
    _zip_dir(out_dir, zip_path)

    print(f"✓ Packaged: {zip_path}")
    _print_next_steps(args.platform, zip_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
