"""
Unit tests for the deploy_core build functions.
"""
import sys
from pathlib import Path

# Add project root to path to allow absolute imports
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools import deploy_core


def create_dummy_files(root: Path):
    """Creates dummy source files for testing."""
    for name, details in deploy_core.COMPONENT_REGISTRY.items():
        source_path = root / details["source"]
        source_path.parent.mkdir(parents=True, exist_ok=True)
        source_path.write_text(f"# Dummy file for {name}")


def test_build_dry_run(tmp_path):
    """
    Tests that a dry-run build returns the correct file list
    without writing anything to disk.
    """
    # Setup
    root_dir = tmp_path
    create_dummy_files(root_dir)
    qc_dir = root_dir / "quantconnect"

    # Execute
    result = deploy_core.build_quantconnect(root_dir=root_dir, dry_run=True)

    # Assert
    assert result["success"] is True
    assert result["dry_run"] is True
    assert not qc_dir.exists()  # Nothing should be written

    # Check that core components are in the copy list
    assert any("main.py" in item for item in result["copied"])
    assert any("config.py" in item for item in result["copied"])
    assert any("logger.py" in item for item in result["copied"])