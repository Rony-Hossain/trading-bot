# engines/quantconnect/strategy.py

from AlgorithmImports import *
from config import Config
from src.core_strategy import ExtremeAwareCore
from engines.quantconnect.host import QCAlgoHost


class ExtremeAwareStrategy(QCAlgorithm):
    """
    QuantConnect adapter for the Extreme-Aware core.

    QCAlgorithm lives here.
    All real logic lives in ExtremeAwareCore + components.
    """

    def Initialize(self) -> None:
        # Build config for this run
        config = Config(
            version=2,          # 1 = basic, 2 = advanced
            trading_enabled=False,
        )

        # Wrap QCAlgorithm in the host adapter
        host = QCAlgoHost(self)

        # Create the platform-agnostic core and initialize it
        self.app = ExtremeAwareCore(self, config, host=host)
        self.app.initialize()

    # ------------- Universe selection ------------- #

    def SelectCoarse(self, coarse):
        return self.app.select_coarse(coarse)

    def SelectFine(self, fine):
        return self.app.select_fine(fine)

    # ------------- Data + scheduled events -------- #

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
