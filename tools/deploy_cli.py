# deploy_cli.py — stdlib CLI wrapper (dist/<platform> output)

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import deploy_core


def _add_common_build_flags(p):
    p.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1],
                   help="Project root (default: repo root).")
    p.add_argument("--platform", type=str, default="quantconnect", help="Target platform (folder under dist/).")
    p.add_argument("--platform-config", type=Path, default=None, help="Path to tools/platforms.json.")
    p.add_argument("--include", type=str, default="", help="Comma-separated extra components to include.")
    p.add_argument("--exclude", type=str, default="", help="Comma-separated components to exclude.")
    p.add_argument("--dry-run", action="store_true", help="Simulate without writing files.")
    p.add_argument("--force", action="store_true", help="Overwrite output directory if it exists.")
    p.add_argument("--minify", action="store_true", help="AST minify (remove docstrings/blank lines).")
    p.add_argument("--tree-shake", action="store_true", help="Static tree-shaking (approx).")
    p.add_argument("--shake-with-coverage", dest="shake_with_coverage_cmd", type=str, default=None,
                   help="Run tests under coverage (e.g., 'python -m unittest').")
    p.add_argument("--shake-strict", action="store_true",
                   help="Fail build if provided entry points are not found.")
    p.add_argument("--bundle", action="store_true", help="Bundle into one file when platform allows it.")
    p.add_argument("--bundle-name", type=str, default="strategy.py",
                   help="Bundle filename (sanitized). Accepts '.py' or '.py.gz'.")
    p.add_argument("--verbose", action="store_true",
                   help="Print discovery summary (category counts, required) to stderr.")
    p.add_argument("--stats-detail", action="store_true", help="Print per-file stats after build.")
    p.add_argument("--stats-per-file", type=str, default="",
                   help="Substring to filter per-file stats lines.")
    p.add_argument("--hooks-detail", action="store_true", help="Print full hook logs (no truncation).")
    p.add_argument("--log-max-chars", type=int, default=500, help="Trim hook logs to N characters (default 500).")
    p.add_argument("--entry-points", type=str, default="",
                   help="Comma-separated extra entry points for static shake validation.")
    # Hook arg overrides
    p.add_argument("--pre-args", type=str, default="", help="Space-separated args for pre-build hook (CLI override).")
    p.add_argument("--post-args", type=str, default="", help="Space-separated args for post-build hook (CLI override).")
    # Cache
    p.add_argument("--use-cache", action="store_true", help="Enable on-disk cache for transformed files.")
    p.add_argument("--cache-dir", type=Path, default=None, help="Custom cache directory (default .build_cache).")
    p.add_argument("--cache-max-bytes", type=int, default=None, help="Prune cache to this many bytes (e.g., 1073741824).")
    p.add_argument("--cache-clean", action="store_true", help="Delete cache before building.")
    # Output
    p.add_argument("--json", action="store_true", help="Print machine-readable JSON result.")
    p.add_argument("--stats-file", type=Path, default=None, help="Write stats JSON to this file.")


def main():
    parser = argparse.ArgumentParser(description="Multi-platform builder for the trading bot.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser("list", help="List dynamically discovered components.")
    p_list.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    p_list.add_argument("--json", action="store_true")

    p_build = sub.add_parser("build", help="Build for a target platform.")
    _add_common_build_flags(p_build)
    p_build.add_argument("--commit", action="store_true", help="git add/commit dist/<platform> on success.")
    p_build.add_argument("--message", type=str,
                         default=f"build({datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%SZ')}): automated",
                         help="Commit message when using --commit.")

    p_clean = sub.add_parser("clean", help="Remove a platform build folder (dist/<platform>).")
    p_clean.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    p_clean.add_argument("--platform", type=str, default="quantconnect")
    p_clean.add_argument("--platform-config", type=Path, default=None)
    p_clean.add_argument("--cache-clean", action="store_true", help="Also delete transform cache (.build_cache).")
    p_clean.add_argument("--cache-dir", type=Path, default=None, help="Custom cache directory to delete.")

    p_plat = sub.add_parser("platforms", help="Show supported platforms (effective rules).")
    p_plat.add_argument("--platform-config", type=Path, default=None)
    p_plat.add_argument("--json", action="store_true")

    p_cfg = sub.add_parser("config-dump", help="Print effective platform rules (alias of 'platforms').")
    p_cfg.add_argument("--platform-config", type=Path, default=None)
    p_cfg.add_argument("--json", action="store_true")

    args = parser.parse_args()

    if args.cmd == "list":
        comps = deploy_core.list_components(args.root)
        if args.json:
            print(json.dumps(comps, indent=2)); return 0
        print("Available Components (dynamic):")
        print("-" * 80)
        for name, d in sorted(comps.items(), key=lambda kv: (0 if kv[1]["required"] else 1, kv[0])):
            req = "yes" if d.get("required") else "no"
            print(f"  {name:<24} | Category: {d['category']:<10} | Required: {req:<3} | {d['source']}")
        return 0

    if args.cmd in ("platforms", "config-dump"):
        rules = deploy_core.effective_rules(args.platform_config)
        if args.json:
            print(json.dumps(rules, indent=2, default=str)); return 0
        print("Effective Platform Rules:")
        print(json.dumps(rules, indent=2, default=str))
        return 0

    if args.cmd == "clean":
        rules = deploy_core.load_platform_rules(args.platform_config)
        ok = deploy_core.clean_build(args.root, args.platform, platform_rules=rules,
                                     cache_clean=args.cache_clean, cache_dir=args.cache_dir)
        print(f"{'Removed' if ok else 'Nothing to remove'}: {args.root / 'dist' / args.platform}")
        if args.cache_clean:
            cdir = args.cache_dir or (args.root / ".build_cache")
            print(f"Cache removed (if existed): {cdir}")
        return 0

    if args.cmd == "build":
        include = [s.strip() for s in (args.include.split(",") if args.include else []) if s.strip()]
        exclude = [s.strip() for s in (args.exclude.split(",") if args.exclude else []) if s.strip()]
        entry_points = {s.strip() for s in (args.entry_points.split(",") if args.entry_points else []) if s.strip()} or None
        pre_args = shlex.split(args.pre_args) if args.pre_args else None
        post_args = shlex.split(args.post_args) if args.post_args else None

        result = deploy_core.build_for_platform(
            root_dir=args.root,
            platform=args.platform,
            include=include,
            exclude=exclude,
            dry_run=args.dry_run,
            force=args.force,
            minify=args.minify,
            bundle=args.bundle,
            tree_shake=args.tree_shake,
            platform_config=args.platform_config,
            verbose=args.verbose,
            bundle_name=args.bundle_name,
            shake_with_coverage_cmd=args.shake_with_coverage_cmd,
            entry_points=entry_points,
            use_cache=args.use_cache,
            cache_dir=args.cache_dir,
            cache_max_bytes=args.cache_max_bytes,
            cache_clean=args.cache_clean,
            log_max_chars=(None if args.hooks_detail else max(0, args.log_max_chars)),
            pre_args_override=pre_args,
            post_args_override=post_args,
            shake_strict=args.shake_strict,
        )

        if args.stats_file:
            try:
                args.stats_file.parent.mkdir(parents=True, exist_ok=True)
                with args.stats_file.open("w", encoding="utf-8") as f:
                    json.dump(result["stats"], f, indent=2)
            except Exception as e:
                print(f"Failed to write stats file: {e}", file=sys.stderr)

        if args.json:
            print(json.dumps(result, indent=2))
            rc = 0 if result["success"] else 2
        else:
            print("=== Build Summary ===")
            print(f"Platform: {result.get('platform')}")
            print(f"Output: {result.get('root')}")
            print(f"Mode: {'Dry Run' if result['dry_run'] else 'Live Build'}")
            print(f"Timestamp: {result['timestamp']}")
            print(f"Success: {result['success']}")
            print("\nCopied:")
            for p in result["copied"]:
                print(f"  - {p}")
            if result["skipped"]:
                print("\nSkipped:")
                for s in result["skipped"]:
                    print(f"  - {s}")
            stats = result["stats"]
            print("\nStats:")
            print(json.dumps({
                "files_processed": stats["files_processed"],
                "files_split": stats["files_split"],
                "files_bundled": stats["files_bundled"],
                "original_bytes": stats["original_size_bytes"],
                "final_bytes": stats["final_size_bytes"],
                "size_reduction_%": stats["size_reduction_percent"]
            }, indent=2))
            if args.stats_detail and stats.get("per_file_stats"):
                filtered = stats["per_file_stats"]
                if args.stats_per_file:
                    sub = args.stats_per_file
                    filtered = [x for x in filtered if sub in (x.get("path") or "")]
                print("\nPer-file stats:")
                print(json.dumps(filtered, indent=2))
            if stats.get("hooks"):
                print("\nHook/Coverage logs:")
                for h in stats["hooks"]:
                    print(json.dumps(h, indent=2))
            if stats["warnings"]:
                print("\nWarnings:")
                for w in stats["warnings"]:
                    print(f"  - {w}")
            if stats["errors"]:
                print("\nErrors:")
                for e in stats["errors"]:
                    print(f"  - {e}")
            rc = 0 if result["success"] else 2

        if rc != 0:
            return rc

        if getattr(args, "commit", False) and not args.dry_run:
            outdir = Path(result["root"])
            print("\n--- Committing Build ---")
            try:
                subprocess.run(["git", "add", str(outdir)], check=True)
                subprocess.run(["git", "commit", "-m", args.message], check=True)
                print("✅ Successfully committed build files.")
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                print(f"Commit failed: {e}", file=sys.stderr)
                return 3

        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
