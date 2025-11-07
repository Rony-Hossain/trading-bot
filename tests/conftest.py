from pathlib import Path
import pytest


@pytest.fixture
def repo_root(tmp_path: Path) -> Path:
    """Return a temporary repo root for test use.

    Tests can create small files under this path and call into deploy_core.build_quantconnect
    without touching the real repository.
    """
    return tmp_path
