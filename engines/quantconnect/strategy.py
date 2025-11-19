# engines/quantconnect/strategy.py

from AlgorithmImports import *
from config import Config
# CoreStrategy import: source vs. flattened dist
try:
    # When running from your repo (src/ layout)
    from src.core_strategy import ExtremeAwareCore
except ImportError:
    # When running from QC/dist (flat files)
    from core_strategy import ExtremeAwareCore

# Host adapter import: source vs. flattened dist
try:
    # Source layout
    from engines.quantconnect.host import QCAlgoHost
except ImportError:
    # Flat dist layout
    from host import QCAlgoHost


class ExtremeAwareStrategy(QCAlgorithm):
    """
    QuantConnect entrypoint.

    Thin wrapper that:
      - creates Config
      - wraps self in QCAlgoHost
      - hands everything to ExtremeAwareCore
    """

    def Initialize(self) -> None:
        # 1) Build config – THIS is the only place you pick version/mode for QC
        config = Config(
            version=2,          # 1 = basic, 2 = advanced
            trading_enabled=True,
        )

        # 2) Wrap QCAlgorithm in host adapter
        host = QCAlgoHost(self)

        # 3) Build core app (platform-agnostic) and initialize
        self.app = ExtremeAwareCore(self, config, host=host)
        self.app.initialize()

    # ---- Universe selection passthroughs ----

    def SelectCoarse(self, coarse):
        return self.app.select_coarse(coarse)

    def SelectFine(self, fine):
        return self.app.select_fine(fine)

    # ---- Data + scheduled events passthroughs ----

    def OnData(self, data: Slice) -> None:
        self.app.on_data(data)

    def HourlyScan(self) -> None:
        self.app.hourly_scan()

    def OnMarketOpen(self) -> None:
        self.app.on_market_open()

    def OnMarketClose(self) -> None:
        self.app.on_market_close()

    def OnEndOfDay(self) -> None:
        self.app.on_end_of_day()

    def OnEndOfAlgorithm(self) -> None:
        self.app.on_end_of_algorithm()