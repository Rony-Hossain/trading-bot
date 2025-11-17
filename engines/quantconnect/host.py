# engines/quantconnect/host.py
from AlgorithmImports import *
from datetime import datetime
from typing import Callable
from src.platform.base import IAlgoHost


class QCAlgoHost(IAlgoHost):
    def __init__(self, algo: QCAlgorithm):
        self.algo = algo

    # --- time & state ---
    @property
    def now(self) -> datetime:
        return self.algo.Time

    def get_portfolio_value(self) -> float:
        return float(self.algo.Portfolio.TotalPortfolioValue)

    def get_cash(self) -> float:
        return float(self.algo.Portfolio.Cash)

    # --- logging ---
    def log_info(self, msg: str, component: str = "") -> None:
        self.algo.Log(f"[INFO][{component}] {msg}" if component else msg)

    def log_warning(self, msg: str, component: str = "") -> None:
        self.algo.Log(f"[WARN][{component}] {msg}" if component else msg)

    def log_error(self, msg: str, component: str = "") -> None:
        self.algo.Log(f"[ERR][{component}] {msg}" if component else msg)

    # --- orders ---
    def market_order(self, symbol, quantity: float) -> None:
        self.algo.MarketOrder(symbol, quantity)

    # --- scheduling (this is where Schedule.On lives) ---
    def schedule_hourly(self, callback: Callable[[], None]) -> None:
        self.algo.Schedule.On(
            self.algo.DateRules.EveryDay(),
            self.algo.TimeRules.Every(timedelta(hours=1)),
            callback,
        )

    def schedule_open(self, callback: Callable[[], None]) -> None:
        self.algo.Schedule.On(
            self.algo.DateRules.EveryDay(),
            self.algo.TimeRules.AfterMarketOpen("SPY", 1),
            callback,
        )

    def schedule_close(self, callback: Callable[[], None]) -> None:
        self.algo.Schedule.On(
            self.algo.DateRules.EveryDay(),
            self.algo.TimeRules.BeforeMarketClose("SPY", 5),
            callback,
        )

    def schedule_eod(self, callback: Callable[[], None]) -> None:
        self.algo.Schedule.On(
            self.algo.DateRules.EveryDay(),
            self.algo.TimeRules.At(16, 5),
            callback,
        )
