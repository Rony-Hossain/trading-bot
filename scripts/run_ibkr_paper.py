# scripts/run_ibkr_paper.py
from __future__ import annotations
import os, datetime as dt
from ib_insync import IB, Stock
from engines.ibkr.adapter import IBKRBroker
from broker_api import Order
from core_strategy import CoreStrategy, CoreContext
from config import Config

SYMBOLS = os.getenv("IBKR_SYMBOLS", "SPY").split(",")
HOST = os.getenv("IBKR_HOST", "127.0.0.1")
PORT = int(os.getenv("IBKR_PORT", "7497"))         # TWS paper default
CLIENT_ID = int(os.getenv("IBKR_CLIENT_ID", "7"))
BAR_SECONDS = int(os.getenv("BAR_SECONDS", "60"))
MARKET_DATA_TYPE = int(os.getenv("IBKR_MDT", "3"))  # 1=real,3=delayed

def floor_to_bucket(ts: dt.datetime, seconds: int) -> dt.datetime:
    q = (ts.second // seconds) * seconds
    return ts.replace(second=q, microsecond=0)

def main():
    ib = IB()
    ib.connect(HOST, PORT, clientId=CLIENT_ID)
    ib.reqMarketDataType(MARKET_DATA_TYPE)

    broker = IBKRBroker(ib)
    cfg = Config(version=2, trading_enabled=False)
    core = CoreStrategy(cfg)
    ctx = CoreContext(broker=broker, state={})
    core.on_start(ctx)

    contracts = {sym: Stock(sym, 'SMART', 'USD') for sym in SYMBOLS}
    tickers = {sym: ib.reqMktData(c) for sym, c in contracts.items()}

    buckets = {}  # (sym, minute) -> bar dict
    last_flush = dt.datetime.utcnow()

    print(f"Connected to IBKR. Watching: {', '.join(SYMBOLS)}")
    while True:
        ib.sleep(0.25)  # let ib_insync event loop spin
        now = dt.datetime.utcnow()
        for sym, t in tickers.items():
            price = t.last if t.last is not None else t.marketPrice()
            vol = t.lastSize or 0
            if not price:
                continue
            minute = floor_to_bucket(now, BAR_SECONDS)
            key = (sym, minute)
            b = buckets.get(key)
            if not b:
                buckets[key] = {
                    "symbol": sym, "ts": minute,
                    "open": float(price), "high": float(price),
                    "low": float(price), "close": float(price),
                    "volume": int(vol) if vol else 0,
                }
            else:
                b["high"] = max(b["high"], float(price))
                b["low"] = min(b["low"], float(price))
                b["close"] = float(price)
                if vol: b["volume"] += int(vol)

        # flush finished buckets
        cutoff = floor_to_bucket(now, BAR_SECONDS)
        done = [k for k in buckets if k[1] < cutoff]
        for k in sorted(done, key=lambda x: x[1]):
            bar = buckets.pop(k)
            try:
                core.on_bar(ctx, bar)
            except Exception as e:
                broker.error(f"on_bar({bar['symbol']}) failed: {e}")

if __name__ == "__main__":
    main()
