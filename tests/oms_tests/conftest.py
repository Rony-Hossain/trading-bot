# tests/oms_tests/conftest.py

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Iterator

import pytest


# ---------------------------------------------------------------------------
#  PYTHONPATH / IMPORT SETUP
# ---------------------------------------------------------------------------

# Make sure `src/` is on sys.path so tests can:
#   from order_management_system.connection.monitor import ConnectionPulseMonitor
#
# Layout assumed:
#   project_root/
#       src/
#           order_management_system/
#       tests/
#           oms_tests/
CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[2]      # .../project_root
SRC_ROOT = PROJECT_ROOT / "src"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ---------------------------------------------------------------------------
#  BASIC FIXTURES
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def project_root() -> Path:
    """Path to the project root (one level above src/ and tests/)."""
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def src_root() -> Path:
    """Path to the src/ directory (where order_management_system lives)."""
    return SRC_ROOT


@pytest.fixture
def temp_db_path(tmp_path: Path) -> Path:
    """
    Temporary SQLite file path for tests that need a DB.

    Example usage:
        def test_something(temp_db_path):
            engine = ExecutionEngine(db_path=temp_db_path)
    """
    return tmp_path / "oms_test.db"


@pytest.fixture
def test_logger():
    """
    Super-simple stdout logger; replace later with structlog or your real logger.
    """
    import logging

    logger = logging.getLogger("oms_test_logger")
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler()
        fmt = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        )
        handler.setFormatter(fmt)
        logger.addHandler(handler)
    return logger


# ---------------------------------------------------------------------------
#  OPTIONAL: ASYNCIO SUPPORT (for async adapter tests later)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def event_loop():
    """
    Custom event loop fixture so pytest-asyncio works with session scope.
    Only needed if you start writing `async def test_...` tests.
    """
    import asyncio

    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
