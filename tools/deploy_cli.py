"""
Command-Line Interface for building the QuantConnect package.

This CLI provides subcommands to build, clean, and inspect the components
of the trading strategy for deployment to QuantConnect.
"""
import argparse
import json
from pathlib import Path
import sys
import subprocess
from datetime import datetime, timezone

# Ensure the tool can be run from the root directory
sys.path.insert(0, str(Path(__file__).resolve().parent))

import deploy_core


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Build and manage the QuantConnect deployment package.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[1],
        help="Root directory of the repository."
    )
    parser.add_argument("--json", action="store_true", help="Output a machine-readable JSON summary.")

    subparsers = parser.add_subparsers(dest="command", required=True, help="Available commands")

    # Build command
    parser_build = subparsers.add_parser("build", help="Create the quantconnect/ folder with flattened files.")
    parser_build.add_argument("--dry-run", action="store_true", help="Print what would be done, but do not write files.")
    parser_build.add_argument("--include", type=str, help="Comma-separated list of extra components to include.")
    parser_build.add_argument("--exclude", type=str, help="Comma-separated list of components to exclude.")
    parser_build.add_argument("--force", action="store_true", help="Overwrite an existing quantconnect/ folder.")
    parser_build.add_argument("--commit", action="store_true", help="After a successful build, commit the quantconnect/ folder.")
    parser_build.add_argument("--message", type=str, default=f"build(qc): {datetime.now(timezone.utc).isoformat()}", help="Custom commit message.")

    # Clean command
    subparsers.add_parser("clean", help="Remove the quantconnect/ folder.")

    # List command
    subparsers.add_parser("list", help="List all available components in the registry.")

    args = parser.parse_args()

    try:
        if args.command == "build":
            sys.exit(handle_build(args))
        elif args.command == "clean":
            sys.exit(handle_clean(args))
        elif args.command == "list":
            sys.exit(handle_list(args))
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)


def handle_build(args):
    """Handler for the 'build' command. Returns an exit code."""
    include = args.include.split(',') if args.include else []
    exclude = args.exclude.split(',') if args.exclude else []

    result = deploy_core.build_quantconnect(
        root_dir=args.root, include=include, exclude=exclude,
        dry_run=args.dry_run, force=args.force
    )

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("=== Build Summary ===")
        print(f"Mode: {'Dry Run' if result['dry_run'] else 'Live Build'}")
        print(f"Timestamp: {result['timestamp']}")
        print(f"Success: {result['success']}")
        print("\nCopied Files:")
        for item in result["copied"]:
            print(f"  - {item}")
        if result["skipped"]:
            print("\nSkipped Files (Not Found):")
            for item in result["skipped"]:
                print(f"  - {item}")
        if result["warnings"]:
            print("\nWarnings:")
            for warning in result["warnings"]:
                print(f"  - {warning}")

    if not result["success"]:
        return 2  # Missing files or other build error

    if args.commit and not args.dry_run:
        print("\n--- Committing Build ---")
        try:
            subprocess.run(["git", "add", "quantconnect/"], check=True)
            subprocess.run(["git", "commit", "-m", args.message], check=True)
            print("✅ Successfully committed build files.")
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"❌ Commit failed: {e}", file=sys.stderr)
            return 3 # Commit failed

    return 0


def handle_clean(args):
    """Handler for the 'clean' command. Returns an exit code."""
    was_cleaned = deploy_core.clean_quantconnect(args.root)
    if was_cleaned:
        print(f"Successfully removed '{args.root / 'quantconnect'}'")
    else:
        print(f"Directory '{args.root / 'quantconnect'}' not found. Nothing to do.")
    return 0


def handle_list(args):
    """Handler for the 'list' command. Returns an exit code."""
    print("Available Components:")
    print("-" * 80)
    for name, details in deploy_core.list_components().items():
        req = "yes" if details.get('required') else "no"
        print(f"  {name:<25} | Category: {details['category']:<7} | Required: {req:<3} | Source: {details['source']}")
    return 0


if __name__ == "__main__":
    main()