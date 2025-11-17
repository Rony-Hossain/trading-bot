from AlgorithmImports import *


class DynamicSizer:
    """
    Dynamic position sizing based on:
      - Account size (NAV)
      - Configured risk per trade (% of NAV)
      - Z-score (edge)
      - Regime GPM
      - Drawdown ladder multiplier
      - PVS multiplier

    Returns a dollar notional (approx) to use for the trade.
    """

    def __init__(self, algorithm):
        self.algorithm = algorithm
        self.config = algorithm.config

    def _get_nav(self) -> float:
        """Current NAV with a sane fallback."""
        nav = float(self.algorithm.Portfolio.TotalPortfolioValue)
        if nav <= 0:
            # Fallback to INITIAL_CAPITAL if portfolio isn't initialized yet
            nav = float(self.config.INITIAL_CAPITAL)
        return nav

    def CalculateSize(
        self, z_score: float, gpm: float, dd_mult: float, pvs_mult: float
    ) -> float:
        """
        Calculate position size in dollars.

        Args:
            z_score: Signal Z-score (magnitude of edge)
            gpm: Global Position Multiplier (regime, ~0.3–1.0)
            dd_mult: Drawdown-based size multiplier (0.0–1.0)
            pvs_mult: Psychological volatility / PVS-based multiplier (0.0–1.0)
        """
        cfg = self.config
        nav = self._get_nav()

        # ---- 1) Base risk budget in dollars (per trade) -------------------
        # RISK_PER_TRADE_PCT is e.g. 0.001 = 0.1% of NAV
        base_risk_dollars = nav * cfg.RISK_PER_TRADE_PCT

        # Enforce minimum ticket size: we don't want to trade $1 tickets.
        base_risk_dollars = max(base_risk_dollars, cfg.MIN_TICKET_DOLLARS)

        # ---- 2) Edge & regime multipliers ---------------------------------
        # Edge multiplier: scale with |Z|, but keep within [0.5x, 2x]
        edge_mult = abs(z_score) / 2.0  # Z≈2 -> 1.0x, Z≈4 -> 2.0x
        edge_mult = max(0.5, min(edge_mult, 2.0))

        # Regime multiplier: GPM is usually already in a reasonable range;
        # clamp it just to be safe.
        regime_mult = max(0.0, min(gpm, 1.5))

        # Safety: dd_mult and pvs_mult are expected in [0,1].
        dd_mult = max(0.0, min(dd_mult, 1.0))
        pvs_mult = max(0.0, min(pvs_mult, 1.0))

        total_mult = edge_mult * regime_mult * dd_mult * pvs_mult

        # If everything says "no risk", don't magically size up.
        if total_mult <= 0.0:
            return 0.0

        # ---- 3) Raw dollar size ------------------------------------------
        size_dollars = base_risk_dollars * total_mult

        # ---- 4) Apply position-size caps from config ----------------------
        # Hard absolute caps
        size_dollars = max(cfg.MIN_POSITION_SIZE, size_dollars)
        size_dollars = min(size_dollars, cfg.MAX_POSITION_SIZE)

        # Cap by NAV-based limit per symbol
        max_symbol_dollars = nav * cfg.MAX_RISK_PER_SYMBOL_PCT
        size_dollars = min(size_dollars, max_symbol_dollars)

        return float(size_dollars)
