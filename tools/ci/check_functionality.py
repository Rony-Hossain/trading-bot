from __future__ import annotations
import argparse, json, os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SHIMS = ROOT / "tools" / "ci" / "shims"

SMOKE_QC = r"""
import types, importlib.util, sys, os
os.environ.setdefault("CI_SANDBOX", "1")
def load_module_from_path(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore
    return mod
class DummyData(dict): pass
class DummyAlgo:
    def __init__(self):
        self.Portfolio = types.SimpleNamespace(TotalPortfolioValue=100000)
        self.config = types.SimpleNamespace()
        self.Log = print; self.Debug = print; self.Error = print
m = load_module_from_path("qc_main", sys.argv[1])
ok=True; missing=[]
for fn in ("Initialize","OnData"):
    if not hasattr(m, fn):
        ok=False; missing.append(fn)
if not ok:
    print("__ERR__ missing:", ",".join(missing))
else:
    algo=DummyAlgo()
    try: m.Initialize()
    except TypeError: m.Initialize(algo)
    try: m.OnData(DummyData())
    except TypeError: m.OnData(algo, DummyData())
    print("__OK__")
"""

SMOKE_GENERIC = r"""
import importlib.util, sys, os
os.environ.setdefault("CI_SANDBOX", "1")
spec = importlib.util.spec_from_file_location("entry", sys.argv[1])
mod  = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)  # type: ignore
if hasattr(mod, "main"): mod.main()
print("__OK__")
"""

# def run_tests(root: Path) -> tuple[bool,str]:
#     try:
#         p = subprocess.run([sys.executable,"-m","pytest","-q","tools/tests"],
#                            cwd=str(root), text=True, capture_output=True)
#         if p.returncode == 0: return True, p.stdout.strip() or "pytest: ok"
#         if "pytest" in (p.stdout+p.stderr).lower():
#             return False, (p.stdout+"\n"+p.stderr)[-2000:]
#     except Exception: pass
#     try:
#         p = subprocess.run([sys.executable,"-m","unittest","discover","-s","tools/tests"],
#                            cwd=str(root), text=True, capture_output=True)
#         if p.returncode == 0: return True, p.stdout.strip() or "unittest: ok"
#         return False, (p.stdout+"\n"+p.stderr)[-2000:]
#     except Exception as e:
#         return False, f"could not run tests: {e}"

def run_tests(root: Path) -> tuple[bool, str]:
    """
    Run the project's unit tests.

    Priority:
      1) pytest tests/
      2) unittest discover -s tests

    Returns (ok, log_excerpt).
    """
    test_dir = "tests"

    # Try pytest quietly first
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", test_dir],
            cwd=str(root),
            text=True,
            capture_output=True,
        )
        if proc.returncode == 0:
            return True, proc.stdout.strip() or "pytest: ok"

        # If pytest actually ran but tests failed, surface that
        if "pytest" in (proc.stderr or "").lower() or "pytest" in (proc.stdout or "").lower():
            return False, (proc.stdout + "\n" + proc.stderr)[-2000:]
    except Exception:
        # Fall through to unittest
        pass

    # Fallback: unittest discover
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", test_dir],
            cwd=str(root),
            text=True,
            capture_output=True,
        )
        if proc.returncode == 0:
            return True, proc.stdout.strip() or "unittest: ok"
        return False, (proc.stdout + "\n" + proc.stderr)[-2000:]
    except Exception as e:
        return False, f"unit test run failed to start: {e}"


def smoke_file(harness_code: str, target: Path, timeout: int=20):
    runner = ROOT / ".tmp_smoke.py"
    runner.write_text(harness_code, encoding="utf-8")
    try:
        env=os.environ.copy()
        env["PYTHONPATH"]=str(SHIMS)+os.pathsep+env.get("PYTHONPATH","")
        p = subprocess.run([sys.executable, str(runner), str(target)],
                           cwd=str(ROOT), text=True, capture_output=True, timeout=timeout, env=env)
        ok="__OK__" in (p.stdout or "")
        return ok, (p.stdout or "")[-1000:], (p.stderr or "")[-1000:]
    except subprocess.TimeoutExpired:
        return False, "", "Timeout"
    finally:
        runner.unlink(missing_ok=True)

def main():
    ap=argparse.ArgumentParser(description="Functionality checks: tests + platform smoke.")
    ap.add_argument("--platform", type=str, default="quantconnect",
                    choices=["quantconnect","backtrader","zipline","freqtrade"])
    ap.add_argument("--timeout", type=int, default=20)
    ap.add_argument("--json", action="store_true")
    args=ap.parse_args()

    ok_t, log_t = run_tests(ROOT)
    target = ROOT / "src" / "main.py"
    harness = SMOKE_QC if args.platform=="quantconnect" else SMOKE_GENERIC
    if not target.exists():
        ok_s, out_s, err_s = False, "", f"{target} not found"
    else:
        ok_s, out_s, err_s = smoke_file(harness, target, timeout=args.timeout)

    res={"tests_ok": ok_t, "tests_log": log_t, "smoke_ok": ok_s,
         "smoke_stdout": out_s, "smoke_stderr": err_s, "success": ok_t and ok_s}

    if args.json:
        print(json.dumps(res, indent=2))
    else:
        print("== Unit Tests =="); print(log_t)
        print("\n== Smoke =="); print(f"Target: {target}")
        print("stdout:", out_s.strip()[-200:]); print("stderr:", err_s.strip()[-200:])
        print(f"\nSuccess: {res['success']}")
    return 0 if res["success"] else 2

if __name__=="__main__":
    raise SystemExit(main())
