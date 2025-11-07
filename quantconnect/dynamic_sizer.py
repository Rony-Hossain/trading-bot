"""
Dynamic Position Sizer - Phase 2 (Enhanced with ATR)

Kelly-inspired position sizing based on edge quality and volatility.

Formula:
base_risk / ATR_pct * edge_mult * regime_mult * dd_mult * pvs_mult

Multipliers:
- Edge: 1x to 2x (based on |Z|)
- Regime: 0.3 to 1.0 (from HMM GPM)
- Drawdown: 0.0 to 1.0 (from DD ladder)
- PVS: 0.0 to 1.0 (from psychological state)
- ATR: Risk-invariant across different volatility stocks

Usage:
    from dynamic_sizer import DynamicSizer

    sizer = DynamicSizer(algorithm)
    size = sizer.CalculateSize(symbol, z_score, regime, dd, pvs)
"""

from AlgorithmImports import *
import numpy as np

class DynamicSizer:
    """Dynamic position sizing based on multiple factors including volatility"""

    def __init__(self, algorithm):
        self.algorithm = algorithm
        self.config = algorithm.config
        self.logger = algorithm.logger if hasattr(algorithm, 'logger') else None

        # Base risk amount (in dollars)
        self.base_risk = self.config.BASE_POSITION_SIZE if hasattr(self.config, 'BASE_POSITION_SIZE') else 5.0
        self.min_size = self.config.MIN_POSITION_SIZE if hasattr(self.config, 'MIN_POSITION_SIZE') else 2.50
        self.max_size = self.config.MAX_POSITION_SIZE if hasattr(self.config, 'MAX_POSITION_SIZE') else 20.0

        # ATR configuration
        self.atr_period = 20
        self.atr_cache = {}  # symbol -> (atr, timestamp)
        
    def GetATR(self, symbol, period=20):
        """
        Calculate Average True Range for a symbol

        Args:
            symbol: Trading symbol
            period: ATR period (default 20)

        Returns:
            float: ATR value, or 0 if unable to calculate
        """
        try:
            # Check cache (valid for 1 hour)
            if symbol in self.atr_cache:
                cached_atr, cached_time = self.atr_cache[symbol]
                elapsed = (self.algorithm.Time - cached_time).total_seconds()
                if elapsed < 3600:  # 1 hour cache
                    return cached_atr

            # Get historical data
            history = self.algorithm.History(symbol, period + 1, Resolution.Daily)

            if history.empty or len(history) < period:
                return 0

            # Calculate True Range
            high = history['high'].values
            low = history['low'].values
            close = history['close'].values

            tr_list = []
            for i in range(1, len(high)):
                tr = max(
                    high[i] - low[i],
                    abs(high[i] - close[i-1]),
                    abs(low[i] - close[i-1])
                )
                tr_list.append(tr)

            if not tr_list:
                return 0

            # ATR = average of TR
            atr = np.mean(tr_list[-period:])

            # Cache result
            self.atr_cache[symbol] = (atr, self.algorithm.Time)

            return atr

        except Exception as e:
            if self.logger:
                self.logger.error(f"ATR calculation error for {symbol}: {str(e)}", component="DynamicSizer")
            return 0

    def CalculateSize(self, symbol, z_score, gpm, dd_mult, pvs_mult, use_atr=True):
        """
        Calculate position size with ATR-based volatility adjustment

        Args:
            symbol: Trading symbol
            z_score: Signal Z-score
            gpm: Global Position Multiplier (regime)
            dd_mult: Drawdown multiplier
            pvs_mult: PVS multiplier
            use_atr: Use ATR-based sizing (default True)

        Returns:
            float: Position size in dollars
        """

        # Get current price
        if symbol not in self.algorithm.Securities:
            return 0

        price = self.algorithm.Securities[symbol].Price
        if price <= 0:
            return 0

        # Calculate base size
        if use_atr and self.config.version >= 2 and self.config.ENABLE_DYNAMIC_SIZING:
            # ATR-based sizing: risk_amount / (ATR / price)
            atr = self.GetATR(symbol, self.atr_period)

            if atr > 0:
                # ATR as percentage of price
                atr_pct = atr / price

                # Size = base_risk / atr_pct
                # This makes risk consistent across different volatility stocks
                # High volatility = smaller position, Low volatility = larger position
                base_size = self.base_risk / max(atr_pct, 0.01)  # Prevent division by very small ATR

                if self.logger:
                    self.logger.debug(
                        f"ATR sizing for {symbol}: price=${price:.2f}, ATR=${atr:.2f} ({atr_pct:.2%}), "
                        f"base=${base_size:.2f}",
                        component="DynamicSizer"
                    )
            else:
                # Fallback to fixed sizing if ATR unavailable
                base_size = self.base_risk
                if self.logger:
                    self.logger.warning(
                        f"ATR unavailable for {symbol}, using fixed base: ${base_size:.2f}",
                        component="DynamicSizer"
                    )
        else:
            # Fixed dollar sizing (v1 or ATR disabled)
            base_size = self.base_risk

        # Edge multiplier (1x to 2x based on signal strength)
        edge_mult = min(abs(z_score) / 2.0, 2.0)

        # Combine all multipliers
        total_mult = edge_mult * gpm * dd_mult * pvs_mult

        # Calculate final size
        size = base_size * total_mult

        # Apply caps
        size = max(self.min_size, min(size, self.max_size))

        return size
