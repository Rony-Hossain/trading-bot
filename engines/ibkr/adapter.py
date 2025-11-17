# engines/ibkr/adapter.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from ib_insync import IB, Stock
from broker_api import BrokerAPI, Order

class IBKRBroker(BrokerAPI):
    def __init__(self, ib: IB):
        self.ib = ib

    # --- account/time ---
    def now(self):
        return self.ib.reqCurrentTime()

    def cash(self) -> float:
        vals = {v.tag: v.value for v in self.ib.accountValues()}
        try:
            return float(vals.get("AvailableFunds", "0"))
        except Exception:
            return 0.0

    def equity(self) -> float:
        vals = {v.tag: v.value for v in self.ib.accountValues()}
        try:
            return float(vals.get("NetLiquidation", "0"))
        except Exception:
            return 0.0

    # --- positions ---
    def get_position(self, symbol: str) -> float:
        for p in self.ib.positions():
            if p.contract.symbol == symbol:
                return float(p.position)
        return 0.0

    # --- orders ---
    def submit_order(self, order: Order):
        c = Stock(order.symbol, 'SMART', 'USD')
        side = "BUY" if order.side == "buy" else "SELL"
        if order.order_type == "limit" and order.limit_price is not None:
            ib_order = self.ib.limitOrder(side, int(order.qty), float(order.limit_price))
        else:
            ib_order = self.ib.marketOrder(side, int(order.qty))
        trade = self.ib.placeOrder(c, ib_order)
        return trade.order.orderId

    def cancel(self, order_id):
        for t in self.ib.trades():
            if t.order.orderId == order_id:
                self.ib.cancelOrder(t.order)
                break

    # --- logging ---
    def log(self, *a, **k): print("[IBKR]", *a)
    def debug(self, *a, **k): print("[IBKR:DBG]", *a)
    def error(self, *a, **k): print("[IBKR:ERR]", *a)
