# tools/ci/check_syntax.py
from __future__ import annotations
import argparse, ast, json, sys, py_compile, re
from pathlib import Path
from typing import List, Dict, Any, Iterable

ROOT = Path(__file__).resolve().parents[2]  # repo root (tools/ci/ -> repo)

EMOJI_RE = re.compile(r'[\U0001F300-\U0001FAFF]')
CTRL_RE  = re.compile(r'[\x00-\x08\x0B\x0C\x0E-\x1F]')  # exclude \t,\n,\r

def iter_py_files(bases: Iterable[Path]) -> Iterable[Path]:
    seen = set()
    for base in bases:
        if not base.exists(): continue
        for p in base.rglob("*.py"):
            if "__pycache__" in p.parts: continue
            rp = p.resolve()
            if rp in seen: continue
            seen.add(rp); yield p

def lint_lite(text: str) -> List[str]:
    warns: List[str] = []
    for i, line in enumerate(text.splitlines(), 1):
        if "\t" in line:
            warns.append(f"line {i}: tab indentation found (use spaces)")
        if line.rstrip() != line:
            warns.append(f"line {i}: trailing whitespace")
        if CTRL_RE.search(line):
            warns.append(f"line {i}: non-ASCII control character")
        if EMOJI_RE.search(line):
            warns.append(f"line {i}: emoji detected")
    return warns

def main():
    ap = argparse.ArgumentParser(description="AST + byte-compile syntax checks.")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--fail-on-warn", action="store_true")
    ap.add_argument("--paths", type=str, default="src,config",
                    help="Comma-separated roots to scan.")
    args = ap.parse_args()

    roots = [ROOT / p.strip() for p in args.paths.split(",") if p.strip()]
    errors: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []
    checked = 0

    for f in iter_py_files(roots):
        checked += 1
        txt = f.read_text(encoding="utf-8", errors="replace")
        # AST
        try:
            ast.parse(txt, filename=str(f))
        except SyntaxError as e:
            errors.append({"file": str(f), "phase": "ast", "error": f"{e.__class__.__name__}: {e}"})
            continue
        # byte-compile
        try:
            py_compile.compile(str(f), doraise=True)
        except Exception as e:
            errors.append({"file": str(f), "phase": "py_compile", "error": f"{e}"})
            continue
        # lint-lite
        lints = lint_lite(txt)
        if lints:
            warnings.append({"file": str(f), "phase": "lint-lite", "warnings": lints})

    result = {
        "checked_files": checked,
        "errors": errors,
        "warnings": warnings,
        "success": len(errors) == 0 and (not args.fail_on_warn or not warnings),
    }

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Checked: {checked} files")
        if errors:
            print("\nErrors:")
            for e in errors:
                print(f"  - {e['file']} [{e['phase']}]: {e['error']}")
        if warnings:
            print("\nWarnings:")
            for w in warnings:
                print(f"  - {w['file']} [{w['phase']}]")
                for m in w["warnings"][:5]:
                    print(f"      * {m}")
                if len(w["warnings"]) > 5:
                    print(f"      … {len(w['warnings'])-5} more")
        print(f"\nSuccess: {result['success']}")

    return 0 if result["success"] else 2

if __name__ == "__main__":
    raise SystemExit(main())
