# tools/qc_init_smoke.py
from __future__ import annotations

import importlib
import inspect
import sys
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]


def _install_algorithmimports_shim() -> ModuleType:
    """
    Install the local AlgorithmImports shim (tools/ci/shims/AlgorithmImports.py)
    as the 'AlgorithmImports' module so that dist/quantconnect code can import it.
    """
    try:
        from tools.ci.shims import AlgorithmImports as shim  # type: ignore
    except Exception as e:
        raise RuntimeError(
            "Could not import tools.ci.shims.AlgorithmImports; "
            "qc_init_smoke requires the shim."
        ) from e

    # Make it visible as 'AlgorithmImports'
    sys.modules.setdefault("AlgorithmImports", shim)
    return shim


def run_qc_init_smoke(dist_root: Path | None = None) -> None:
    """
    Smoke-test the QC deployment in dist/quantconnect by:

      - adding dist/quantconnect to sys.path
      - installing the AlgorithmImports shim
      - importing main.py
      - finding the QCAlgorithm subclass
      - instantiating it and calling Initialize()

    This is meant to run **locally**, not inside QuantConnect.
    """
    dist_root = Path(dist_root or ROOT / "dist" / "quantconnect")

    if not dist_root.exists():
        raise FileNotFoundError(
            f"dist root {dist_root} does not exist. "
            "Run `python -m tools.deploy_cli build --platform quantconnect` first."
        )

    # Make dist/quantconnect importable
    sys.path.insert(0, str(dist_root))

    # Install our shim as AlgorithmImports so `from AlgorithmImports import *` works
    shim = _install_algorithmimports_shim()
    QCAlgorithm = getattr(shim, "QCAlgorithm", None)
    if QCAlgorithm is None:
        raise RuntimeError("AlgorithmImports shim does not define QCAlgorithm")

    try:
        main_mod = importlib.import_module("main")
    except Exception as e:
        raise RuntimeError(f"Failed to import main.py from dist: {e!r}") from e

    # Find the QCAlgorithm subclass in main.py (e.g., ExtremeAwareStrategy)
    algo_cls = None
    for _, obj in inspect.getmembers(main_mod, inspect.isclass):
        if issubclass(obj, QCAlgorithm) and obj is not QCAlgorithm:
            algo_cls = obj
            break

    if algo_cls is None:
        raise RuntimeError(
            "No QCAlgorithm subclass found in dist/quantconnect/main.py "
            "(after loading AlgorithmImports shim)."
        )

    # Instantiate and call Initialize()
    algo = algo_cls()
    algo.Initialize()

    print(f"QC init smoke OK: {algo_cls.__name__}.Initialize() completed without error.")


if __name__ == "__main__":
    # Allow `python -m tools.qc_init_smoke` from repo root
    try:
        run_qc_init_smoke()
    except Exception as e:
        # Non-zero exit + readable message
        print(f"QC init smoke FAILED: {e}")
        raise
