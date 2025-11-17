# engines/backtrader/broker.py
from __future__ import annotations
import backtrader as bt
from broker_api import BrokerAPI, Order

class BTBroker(BrokerAPI):
    def __init__(self, cerebro: bt.Cerebro, strategy):
        self.cerebro = cerebro
        self.strategy = strategy
    def now(self): return self.strategy.data.datetime.datetime(0)
    def cash(self) -> float: return float(self.cerebro.broker.getcash())
    def equity(self) -> float: return float(self.cerebro.broker.getvalue())
    def get_position(self, symbol: str) -> float:
        pos = self.strategy.getpositionbyname(symbol)
        return float(pos.size) if pos else 0.0
    def submit_order(self, order: Order):
        data = getattr(self.strategy, f"data_{order.symbol}")
        if order.side == "buy":
            o = self.strategy.buy(data=data, size=int(order.qty), price=order.limit_price) if order.order_type=="limit" else self.strategy.buy(data=data, size=int(order.qty))
        else:
            o = self.strategy.sell(data=data, size=int(order.qty), price=order.limit_price) if order.order_type=="limit" else self.strategy.sell(data=data, size=int(order.qty))
        return o.ref
    def cancel(self, order_id): self.strategy.cancel(order_id)
    def log(self, *a, **k): print("[BT]", *a)
    def debug(self, *a, **k): print("[BT:DBG]", *a)
    def error(self, *a, **k): print("[BT:ERR]", *a)
