from __future__ import annotations
import argparse, json, os, subprocess, sys
from pathlib import Path
from typing import Iterable, Dict, Any, List

ROOT = Path(__file__).resolve().parents[2]
SHIMS = ROOT / "tools" / "ci" / "shims"

RUNNER_CODE = r"""
import os, runpy, sys
shim = sys.argv[2]
if shim and shim not in sys.path:
    sys.path.insert(0, shim)
os.environ.setdefault("CI_SANDBOX", "1")
target = sys.argv[1]
try:
    runpy.run_path(target, run_name="__main__")
    print("__OK__")
except SystemExit as e:
    if int(getattr(e, 'code', 0) or 0) == 0:
        print("__OK__")
    else:
        print("__ERR__ SystemExit:", e)
except Exception as e:
    import traceback; traceback.print_exc()
    print("__ERR__", e)
"""

def iter_py_files(bases: Iterable[Path]) -> Iterable[Path]:
    seen=set()
    for base in bases:
        if not base.exists(): continue
        for p in base.rglob("*.py"):
            if "__pycache__" in p.parts: continue
            if p.name == "__init__.py":  # needs package context; skip per-file run
                continue
            rp=p.resolve()
            if rp in seen: continue
            seen.add(rp); yield p

def main():
    ap=argparse.ArgumentParser(description="Subprocess import/exec smoke test per file.")
    ap.add_argument("--paths", type=str, default="src,config")
    ap.add_argument("--timeout", type=int, default=15)
    ap.add_argument("--json", action="store_true")
    args=ap.parse_args()

    roots=[ROOT/p.strip() for p in args.paths.split(",") if p.strip()]
    tmp = ROOT / ".tmp_ci_runner.py"
    tmp.write_text(RUNNER_CODE, encoding="utf-8")

    results: List[Dict[str, Any]]=[]; errors=0
    for f in iter_py_files(roots):
        cmd=[sys.executable, str(tmp), str(f), str(SHIMS)]
        try:
            p=subprocess.run(cmd, cwd=str(ROOT), text=True, capture_output=True, timeout=args.timeout)
            ok="__OK__" in (p.stdout or "")
            results.append({"file": str(f), "returncode": p.returncode, "ok": ok,
                            "stdout": (p.stdout or "")[-1000:], "stderr": (p.stderr or "")[-1000:]})
            if not ok: errors+=1
        except subprocess.TimeoutExpired:
            results.append({"file": str(f), "returncode": None, "ok": False,
                            "stdout": "", "stderr": f"Timeout after {args.timeout}s"})
            errors+=1

    tmp.unlink(missing_ok=True)
    summary={"checked_files": len(results), "errors": errors, "success": errors==0, "results": results}
    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print(f"Checked: {summary['checked_files']} files")
        if errors:
            print(f"Failures: {errors}")
            for r in results:
                if not r["ok"]:
                    print(f"  - {r['file']} (rc={r['returncode']})")
                    if r["stderr"]:
                        print("      stderr:", r["stderr"].splitlines()[-1][:200])
        print(f"\nSuccess: {summary['success']}")
    return 0 if summary["success"] else 2

if __name__=="__main__":
    raise SystemExit(main())
