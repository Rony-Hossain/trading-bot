# engines/zipline/adapter.py
from __future__ import annotations
from core_strategy import CoreStrategy, CoreContext
from config import Config

class ZLBroker:
    def __init__(self, context):
        self.context = context
    def now(self): return self.context.get_datetime()
    def cash(self): return float(self.context.portfolio.cash)
    def equity(self): return float(self.context.portfolio.portfolio_value)
    def get_position(self, symbol: str) -> float:
        asset = self.context.symbol(symbol)
        pos = self.context.portfolio.positions.get(asset)
        return float(pos.amount) if pos else 0.0
    def submit_order(self, order):
        asset = self.context.symbol(order.symbol)
        self.context.order(asset, int(order.qty))
        return None
    def cancel(self, order_id): pass
    def log(self, *a, **k): print("[ZL]", *a)
    def debug(self, *a, **k): print("[ZL:DBG]", *a)
    def error(self, *a, **k): print("[ZL:ERR]", *a)

def initialize(context):
    context.broker = ZLBroker(context)
    context.core = CoreStrategy(Config(version=2, trading_enabled=False))
    context.ctx = CoreContext(broker=context.broker, state={})
    context.core.on_start(context.ctx)

def handle_data(context, data):
    sym = "SPY"
    if data.can_trade(sym):
        bar = {
            "symbol": sym,
            "ts": context.get_datetime(),
            "open": float(data.current(sym, 'open')),
            "high": float(data.current(sym, 'high')),
            "low":  float(data.current(sym, 'low')),
            "close":float(data.current(sym, 'price')),
            "volume":int(data.current(sym, 'volume')),
        }
        context.core.on_bar(context.ctx, bar)
