# engines/backtrader/strategy.py
from __future__ import annotations
import backtrader as bt
from core_strategy import CoreStrategy, CoreContext
from config import Config
from engines.backtrader.broker import BTBroker

class BTWrapper(bt.Strategy):
    params = (("symbols", ["SPY"]),)
    def __init__(self):
        self.broker_api = BTBroker(self.cerebro, self)
        self.core = CoreStrategy(Config(version=2, trading_enabled=False))
        self.ctx = CoreContext(broker=self.broker_api, state={})
        for d in self.datas:
            setattr(self, f"data_{d._name}", d)
        self.core.on_start(self.ctx)
    def next(self):
        for d in self.datas:
            bar = {
                "symbol": d._name,
                "ts": self.data.datetime.datetime(0),
                "open": float(d.open[0]), "high": float(d.high[0]),
                "low": float(d.low[0]), "close": float(d.close[0]),
                "volume": int(d.volume[0]) if len(d.volume) else 0,
            }
            self.core.on_bar(self.ctx, bar)
    def stop(self):
        self.core.on_end(self.ctx)
