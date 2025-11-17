# engines/quantconnect/broker.py
from __future__ import annotations
from broker_api import BrokerAPI, Order

class QCBroker(BrokerAPI):
    def __init__(self, algo):
        self.algo = algo

    def now(self):
        return self.algo.Time

    def cash(self) -> float:
        return float(self.algo.Portfolio.Cash)

    def equity(self) -> float:
        return float(self.host.get_portfolio_value())

    def get_position(self, symbol: str) -> float:
        sym = self.algo.Symbol(symbol)
        return float(self.algo.Portfolio[sym].Quantity)

    def submit_order(self, order: Order):
        qty = int(order.qty)
        tag = order.tag
        if order.side == "buy":
            if order.order_type == "limit" and order.limit_price is not None:
                ticket = self.algo.LimitOrder(order.symbol, qty, float(order.limit_price), tag)
            else:
                ticket = self.host.market_order(order.symbol, qty, tag)
        else:
            if order.order_type == "limit" and order.limit_price is not None:
                ticket = self.algo.LimitOrder(order.symbol, -qty, float(order.limit_price), tag)
            else:
                ticket = self.host.market_order(order.symbol, -qty, tag)
        return ticket.OrderId

    def cancel(self, order_id):
        self.algo.Transactions.CancelOrder(order_id)

    def log(self, *a, **k):
        self.host.log_info(" ".join(map(str, a)))

    def debug(self, *a, **k):
        self.algo.Debug(" ".join(map(str, a)))

    def error(self, *a, **k):
        self.algo.Error(" ".join(map(str, a)))
