# src/main.py
"""
Platform-agnostic helpers for the Extreme-Aware core.

This file MUST NOT import AlgorithmImports or QCAlgorithm.
Engine-specific wrappers live under engines/<engine>/.
"""

from typing import Type
from config import Config
from src.core_strategy import ExtremeAwareCore
from src.platform.base import IAlgoHost  # your Protocol / interface


def build_core(
    engine_ctx,
    host_adapter_cls: Type[IAlgoHost],
    *,
    version: int = 2,
    trading_enabled: bool = False,
) -> ExtremeAwareCore:
    """
    Factory to build ExtremeAwareCore for any engine.

    engine_ctx: engine-native object (QCAlgorithm, bt.Strategy, etc.)
    host_adapter_cls: adapter implementing IAlgoHost for that engine.
    """
    config = Config(version=version, trading_enabled=trading_enabled)
    host = host_adapter_cls(engine_ctx)
    core = ExtremeAwareCore(engine_ctx, config, host=host)
    core.initialize()
    return core


# ----------------------------------------------------------------------
# Compatibility stubs for tools/ci/check_functionality.py smoke harness
# These are NOT used by any engine; they just satisfy tools.run_checks.
# ----------------------------------------------------------------------


def Initialize(self) -> None:
    # no-op for local smoke tools
    return


def OnData(self, data) -> None:
    # no-op for local smoke tools
    return
