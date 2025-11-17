# scripts/run_backtrader.py
import backtrader as bt
import pandas as pd
from engines.backtrader.strategy import BTWrapper

def run(csv_path: str = "data/SPY.csv", symbol="SPY"):
    df = pd.read_csv(csv_path, parse_dates=["Date"])
    df.set_index("Date", inplace=True)
    data = bt.feeds.PandasData(dataname=df, open="Open", high="High", low="Low", close="Close", volume="Volume")
    cerebro = bt.Cerebro()
    cerebro.adddata(data, name=symbol)
    cerebro.addstrategy(BTWrapper, symbols=[symbol])
    cerebro.broker.setcash(100000)
    cerebro.run()
    print("Final Value:", cerebro.broker.getvalue())

if __name__ == "__main__":
    run()
