# Minimal QuantConnect stand-in for CI import/smoke only.
class QCAlgorithm:
    def __init__(self):
        self.Portfolio = type("P", (), {"TotalPortfolioValue": 100000})()
        self.Log = print; self.Debug = print; self.Error = print

class Resolution:
    Minute=1; Hour=2; Daily=3

class Symbol(str): pass

def AddEquity(*args, **kwargs): return None
