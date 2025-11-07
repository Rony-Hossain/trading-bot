"""
Core deployment logic for building QuantConnect packages.

This module provides the central logic for copying, filtering, and packaging
files into a QuantConnect-ready format. It is designed to be imported and used
by CLI tools, UIs, and tests.

Usage:
    from tools import deploy_core
    result = deploy_core.build_quantconnect(root_dir, dry_run=True)
"""
from __future__ import annotations
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any

# Component registry
# All source paths are relative to the repository root (root_dir)
COMPONENT_REGISTRY: Dict[str, Dict[str, Any]] = {
    "main": {
        "source": "src/main.py",
        "category": "CORE",
        "required": True,
        "description": "Algorithm entrypoint"
    },
    "config": {
        "source": "config/config.py",
        "category": "CORE",
        "required": True,
        "description": "Unified configuration system"
    },
    "logger": {
        "source": "src/components/logger.py",
        "category": "INFRA",
        "required": True,
        "description": "Structured logging helper"
    },
    "log_retrieval": {
        "source": "src/components/log_retrieval.py",
        "category": "INFRA",
        "required": True,
        "description": "Log retrieval helper for backtests"
    },
    "universe_filter": {
        "source": "src/components/universe_filter.py",
        "category": "CORE",
        "required": True,
        "description": "Universe filtering logic"
    },
    "extreme_detector": {
        "source": "src/components/extreme_detector.py",
        "category": "STRATEGY",
        "required": True,
        "description": "Detects extreme moves"
    },
    "hmm_regime": {
        "source": "src/components/hmm_regime.py",
        "category": "STRATEGY",
        "required": True,
        "description": "Regime detection (HMM)"
    },
    "avwap_tracker": {
        "source": "src/components/avwap_tracker.py",
        "category": "STRATEGY",
        "required": True,
        "description": "Anchored VWAP tracker"
    },
    "risk_monitor": {
        "source": "src/components/risk_monitor.py",
        "category": "RISK",
        "required": True,
        "description": "Risk and drawdown checks"
    },
    # Missing files reported earlier — include them all so packaging is complete
    "alert_manager": {"source": "src/components/alert_manager.py", "category": "INFRA", "required": True, "description": "Alert system"},
    "backtest_analyzer": {"source": "src/components/backtest_analyzer.py", "category": "INFRA", "required": True, "description": "Backtest analysis utilities"},
    "health_monitor": {"source": "src/components/health_monitor.py", "category": "INFRA", "required": True, "description": "Health checks"},
    "cascade_prevention": {"source": "src/components/cascade_prevention.py", "category": "RISK", "required": True, "description": "Cascade prevention logic"},
    "drawdown_enforcer": {"source": "src/components/drawdown_enforcer.py", "category": "RISK", "required": True, "description": "Enforces drawdown limits"},
    "dynamic_sizer": {"source": "src/components/dynamic_sizer.py", "category": "POSITION", "required": True, "description": "Position sizing"},
    "entry_timing": {"source": "src/components/entry_timing.py", "category": "STRATEGY", "required": True, "description": "Entry timing heuristics"},
    "exhaustion_detector": {"source": "src/components/exhaustion_detector.py", "category": "STRATEGY", "required": True, "description": "Detects exhaustion"},
    "portfolio_constraints": {"source": "src/components/portfolio_constraints.py", "category": "RISK", "required": True, "description": "Portfolio constraints enforcement"},
    "pvs_monitor": {"source": "src/components/pvs_monitor.py", "category": "RISK", "required": True, "description": "PVS monitoring"},
}


def list_components() -> Dict[str, Dict[str, Any]]:
    """Return a copy of the component registry."""
    return {k: dict(v) for k, v in COMPONENT_REGISTRY.items()}


def clean_quantconnect(root_dir: Path) -> bool:
    """Remove the generated `quantconnect/` folder. Returns True if removed."""
    target = Path(root_dir) / "quantconnect"
    if target.exists() and target.is_dir():
        shutil.rmtree(target)
        return True
    return False


def build_quantconnect(
    root_dir: Path,
    include: Optional[List[str]] = None,
    exclude: Optional[List[str]] = None,
    dry_run: bool = True,
    force: bool = False,
) -> Dict[str, Any]:
    """
    Build a flattened `quantconnect/` folder suitable for uploading to QuantConnect.

    Args:
        root_dir: repository root Path
        include: extra component names to include (in addition to required)
        exclude: component names to exclude
        dry_run: if True, do not write files, only simulate
        force: if True, remove existing quantconnect/ before writing

    Returns:
        A dict with keys: root, timestamp, dry_run, success, copied, skipped, warnings
    """
    root_dir = Path(root_dir)
    include = include or []
    exclude = exclude or []

    target = root_dir / "quantconnect"
    timestamp = datetime.utcnow().isoformat() + "Z"
    copied: List[str] = []
    skipped: List[str] = []
    warnings: List[str] = []

    if target.exists():
        if not force:
            warnings.append("quantconnect/ already exists; use force=True to overwrite")
            return {
                "root": str(target),
                "timestamp": timestamp,
                "dry_run": dry_run,
                "success": False,
                "copied": copied,
                "skipped": skipped,
                "warnings": warnings,
            }
        else:
            if not dry_run:
                shutil.rmtree(target)

    # Build set of names to copy: all required plus any included, minus excluded
    names_to_copy = [name for name, d in COMPONENT_REGISTRY.items() if d.get("required")]
    for name in include:
        if name and name not in names_to_copy:
            names_to_copy.append(name)
    names_to_copy = [n for n in names_to_copy if n not in exclude]

    # Ensure target directory exists when not dry-run
    if not dry_run:
        target.mkdir(parents=True, exist_ok=True)

    # Preferred upload order: main, config, others
    upload_order: List[str] = []
    if "main" in names_to_copy:
        upload_order.append("main")
    if "config" in names_to_copy:
        upload_order.append("config")
    for n in names_to_copy:
        if n not in ("main", "config"):
            upload_order.append(n)

    for name in upload_order:
        details = COMPONENT_REGISTRY.get(name)
        if not details:
            skipped.append(name)
            warnings.append(f"Unknown component '{name}' requested")
            continue

        src = root_dir / details["source"]
        if not src.exists():
            skipped.append(details["source"])
            warnings.append(f"Source not found: {details['source']}")
            continue

        dest = target / Path(details["source"]).name
        if dry_run:
            copied.append(str(dest))
            continue

        # Write file
        try:
            shutil.copy2(src, dest)
            copied.append(str(dest))
        except Exception as e:
            warnings.append(f"Failed to copy {src} -> {dest}: {e}")

    # Create UPLOAD_ORDER.txt in target
    if not dry_run:
        order_file = target / "UPLOAD_ORDER.txt"
        try:
            with order_file.open("w", encoding="utf8") as fh:
                for name in upload_order:
                    details = COMPONENT_REGISTRY.get(name)
                    if details:
                        fh.write(f"{Path(details['source']).name}\n")
        except Exception as e:
            warnings.append(f"Failed to write UPLOAD_ORDER.txt: {e}")

    success = len(warnings) == 0 or (len(copied) > 0 and all("Source not found" not in w for w in warnings))

    return {
        "root": str(target),
        "timestamp": timestamp,
        "dry_run": dry_run,
        "success": success,
        "copied": copied,
        "skipped": skipped,
        "warnings": warnings,
    }

