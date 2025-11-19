from AlgorithmImports import *

FALLBACK_TICKERS = ["UNH", "SPY", "SOFI", "TSLA"]

class UniverseFilter:
    """Handle coarse and fine universe selection"""

    def __init__(self, algorithm, config=None):
        self.algorithm = algorithm
        self.config = config or getattr(algorithm, "config", None)
        self.current_universe = set()
        self.last_rebalance = None

    def CoarseFilter(self, coarse):
        selected = [
            x for x in coarse
            if x.HasFundamentalData
            and x.Price >= self.config.MIN_PRICE
            and x.Price <= self.config.MAX_PRICE
            and x.DollarVolume > self.config.MIN_DOLLAR_VOLUME
            and x.Symbol.Value not in self.config.BLACKLIST
        ]

        selected = sorted(selected, key=lambda x: x.DollarVolume, reverse=True)
        selected = selected[: self.config.UNIVERSE_SIZE]

        self.algorithm.Log(f"Coarse Filter: {len(selected)} symbols passed")

        # If everything collapses, still make sure we have *something*:
        if not selected:
            self.algorithm.Log(
                "CoarseFilter: EMPTY – using static fallback tickers",
                LogLevel.Warning,
            )
            return [
                Symbol.Create(t, SecurityType.Equity, Market.USA)
                for t in FALLBACK_TICKERS
            ]

        return [x.Symbol for x in selected]

    def FineFilter(self, fine):
        selected = []

        for f in fine:
            if not f.HasFundamentalData:
                continue

            # common stock: security type string
            if f.SecurityReference.SecurityType != "ST00000001":
                continue

            exchange = f.CompanyReference.PrimaryExchangeID
            if exchange not in ["NYS", "NAS"]:
                continue

            if not f.CompanyProfile.HeadquarterCity:
                continue

            selected.append(f.Symbol)

        if not selected:
            # Again: hard fallback
            self.algorithm.Log(
                "FineFilter: EMPTY – using static fallback tickers",
                LogLevel.Warning,
            )
            selected = [
                Symbol.Create(t, SecurityType.Equity, Market.USA)
                for t in FALLBACK_TICKERS
            ]

        self.algorithm.Log(f"Fine Filter: {len(selected)} symbols passed")
        self.current_universe = set(selected)
        return selected
