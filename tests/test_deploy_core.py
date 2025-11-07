from pathlib import Path
import sys

import pytest

from tools import deploy_core


def test_registry_contains_core_components():
    registry = deploy_core.list_components()
    assert isinstance(registry, dict)
    # core keys expected
    assert "main" in registry
    assert "config" in registry


def test_build_dry_run_minimal(repo_root: Path, tmp_path: Path, monkeypatch):
    # Create minimal files required by the registry for a dry-run copy
    # We'll monkeypatch the registry to point to our tmp files so the test is hermetic.
    tmp_src = tmp_path / "src" / "components"
    tmp_src.mkdir(parents=True)
    # Create fake component files
    (tmp_src / "logger.py").write_text("# logger stub")
    (tmp_path / "src" / "main.py").write_text("# main stub")
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "config.py").write_text("# config stub")

    # Monkeypatch registry to use our tmp files
    original_registry = dict(deploy_core.COMPONENT_REGISTRY)
    try:
        deploy_core.COMPONENT_REGISTRY.clear()
        deploy_core.COMPONENT_REGISTRY.update({
            "main": {"source": "src/main.py", "category": "CORE", "required": True},
            "config": {"source": "config/config.py", "category": "CORE", "required": True},
            "logger": {"source": "src/components/logger.py", "category": "INFRA", "required": True},
        })

        result = deploy_core.build_quantconnect(root_dir=tmp_path, dry_run=True)
        assert result["dry_run"] is True
        # In dry-run we expect copied list to contain the destinaton paths
        assert len(result["copied"]) == 3
        assert any("main.py" in p for p in result["copied"]) 
    finally:
        deploy_core.COMPONENT_REGISTRY.clear()
        deploy_core.COMPONENT_REGISTRY.update(original_registry)
