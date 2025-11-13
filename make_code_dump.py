#!/usr/bin/env python3
"""
make_code_dump.py
Cross-platform code dumper: generate a Markdown file with code blocks for a target directory (recursively).

Usage:
  python make_code_dump.py                   # prompts for target
  python make_code_dump.py --target src
  python make_code_dump.py --target src --ext py,ps1,sh,ts,js

Options:
  --target  Directory to dump (will be prompted if omitted)
  --ext     Comma-separated list of file extensions (no dots). Default: py
  --outdir  Output base directory. Default: ./dumps
"""
from __future__ import annotations
import argparse
import datetime as dt
import os
from pathlib import Path
from typing import Dict

# Map file extension -> markdown fence language
LANG_MAP: Dict[str, str] = {
    "py": "python",
    "ps1": "powershell",
    "psm1": "powershell",
    "sh": "bash",
    "bash": "bash",
    "zsh": "bash",
    "js": "javascript",
    "mjs": "javascript",
    "cjs": "javascript",
    "ts": "typescript",
    "tsx": "tsx",
    "jsx": "jsx",
    "json": "json",
    "yml": "yaml",
    "yaml": "yaml",
    "toml": "toml",
    "ini": "",
    "cfg": "",
    "md": "markdown",
    "txt": "",
    "ipynb": "json",
}

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument("--target", type=str, help="Directory to dump")
    p.add_argument("--ext", type=str, default="py",
                   help="Comma-separated list of extensions (no dots). Default: py")
    p.add_argument("--outdir", type=str, default="dumps",
                   help="Base output directory. Default: ./dumps")
    p.add_argument("-h", "--help", action="help", help="Show this help message and exit")
    return p.parse_args()

def prompt_target() -> str:
    try:
        return input("Enter the directory to code-dump (e.g., src or quantconnect): ").strip()
    except EOFError:
        return ""

def fence_language(ext: str) -> str:
    return LANG_MAP.get(ext.lower(), "")

def main():
    args = parse_args()
    target = args.target or prompt_target()
    target = target.rstrip("/\\")
    if not target:
        print("No directory specified. Exiting.")
        return

    base = Path(target)
    if not base.is_dir():
        print(f"Directory not found: {base}")
        return

    # Prepare output paths
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    outdir = Path(args.outdir) / f"py_dumps_{stamp}"
    outdir.mkdir(parents=True, exist_ok=True)
    outfile = outdir / f"{base.name}_code_dump.md"

    # Parse extensions
    exts = [e.strip().lower() for e in args.ext.split(",") if e.strip()]
    exts = list(dict.fromkeys(exts))  # dedupe, order-preserving

    # Header
    header = []
    header.append("# Code Source Dump\n")
    header.append(f"Generated: {dt.datetime.now().isoformat(timespec='seconds')}\n\n")
    header.append(f"_Target directory:_ `{base.as_posix()}`\n")
    header.append(f"_Extensions:_ {', '.join(exts)}\n\n")
    outfile.write_text("".join(header), encoding="utf-8")

    # Collect files deterministically
    files = []
    for p in base.rglob("*"):
        if p.is_file():
            ext = p.suffix[1:].lower()  # drop leading dot
            if ext in exts:
                files.append(p)
    files.sort(key=lambda p: str(p.resolve()).lower())

    print(f"Scanning '{base}': found {len(files)} file(s) with extensions: {', '.join(exts)}")

    # Dump each file
    for f in files:
        abs_path = f.resolve()
        try:
            rel_path = abs_path.relative_to(base.resolve())
        except ValueError:
            # If relative_to fails (symlink outside base), fall back to name
            rel_path = f.name

        ext = f.suffix[1:].lower()
        lang = fence_language(ext)
        fence = f"```{lang}" if lang else "```"

        block_header = []
        block_header.append(f"## {abs_path}\n")
        block_header.append(f"{fence}\n")
        block_header.append(f"# ===== File: {f.name} =====\n")
        block_header.append(f"# Path (relative): {rel_path}\n")
        block_header.append(f"# Path (absolute): {abs_path}\n\n")

        try:
            content = f.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            content = f"# [READ ERROR] {e}\n"

        block_footer = "\n```\n\n"
        with outfile.open("a", encoding="utf-8") as w:
            w.writelines(block_header)
            w.write(content)
            w.write(block_footer)

    print("\nCreated:")
    print(f"  {outfile}")
    print("\nListing directory:")
    for child in sorted(outdir.iterdir()):
        print(f"  {child.name}  ({child.stat().st_size} bytes)")

if __name__ == "__main__":
    main()
