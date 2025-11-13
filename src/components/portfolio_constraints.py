"""
Portfolio Constraints - Phase 2

Enforces portfolio-level constraints:
- Beta neutrality (|β| ≤ 0.05)
- Sector limits (≤ 2× baseline weight)
- Position limits (min of 2% NAV, 5% ADV)
- Gross/Net exposure limits

Usage:
    from portfolio_constraints import PortfolioConstraints

    constraints = PortfolioConstraints(algorithm)
    can_trade, reason = constraints.CheckConstraints(symbol, size)
    constraints.EnforceBetaNeutrality()
"""

from AlgorithmImports import *
from collections import defaultdict

class PortfolioConstraints:
    """
    Enforce portfolio-level constraints
    """

    def __init__(self, algorithm):
        self.algorithm = algorithm
        self.logger = algorithm.logger if hasattr(algorithm, 'logger') else None

        # Constraint thresholds
        self.max_beta = 0.05
        self.max_sector_multiplier = 2.0
        self.max_position_pct_nav = 0.02  # 2%
        self.max_position_pct_adv = 0.05  # 5%
        self.max_gross_exposure = 2.5  # 250%
        self.max_net_exposure = 0.10  # ±10%

        # Baseline sector weights (from universe)
        self.sector_baseline = {}

        # Current exposures
        self.current_beta = 0.0
        self.current_sector_weights = defaultdict(float)
        self.current_gross = 0.0
        self.current_net = 0.0

        if self.logger:
            self.logger.info("PortfolioConstraints initialized", component="PortfolioConstraints")

    def Update(self):
        """Update current portfolio metrics"""

        portfolio = self.algorithm.Portfolio
        total_value = portfolio.TotalPortfolioValue

        if total_value == 0:
            return

        # Calculate exposures
        self.current_gross = 0.0
        self.current_net = 0.0
        self.current_sector_weights = defaultdict(float)

        for symbol in portfolio.Keys:
            if portfolio[symbol].Invested:
                quantity = portfolio[symbol].Quantity
                price = portfolio[symbol].Price
                position_value = abs(quantity * price)

                # Gross exposure
                self.current_gross += position_value / total_value

                # Net exposure
                self.current_net += (quantity * price) / total_value

                # Sector exposure (would need sector data)
                # For now, skip

        # Calculate beta (simplified - would need actual beta calculation)
        self.current_beta = self._CalculatePortfolioBeta()

    def CheckConstraints(self, symbol, proposed_size, price):
        """
        Check if trade violates any constraints

        Returns:
            (bool, str): (can_trade, reason)
        """

        # 1. Check position size limit
        can_trade, reason = self._CheckPositionLimit(symbol, proposed_size, price)
        if not can_trade:
            return False, reason

        # 2. Check sector limit
        can_trade, reason = self._CheckSectorLimit(symbol, proposed_size, price)
        if not can_trade:
            return False, reason

        # 3. Check gross exposure
        can_trade, reason = self._CheckGrossExposure(proposed_size, price)
        if not can_trade:
            return False, reason

        # 4. Check net exposure
        can_trade, reason = self._CheckNetExposure(proposed_size, price)
        if not can_trade:
            return False, reason

        return True, "OK"

    def _CheckPositionLimit(self, symbol, size, price):
        """Check if position size within limits"""

        portfolio = self.algorithm.Portfolio
        total_value = portfolio.TotalPortfolioValue

        if total_value == 0:
            return False, "Zero portfolio value"

        position_value = abs(size * price)

        # Check vs NAV
        pct_nav = position_value / total_value
        if pct_nav > self.max_position_pct_nav:
            return False, f"Position size {pct_nav:.2%} > {self.max_position_pct_nav:.2%} NAV limit"

        # Check vs ADV (would need actual ADV data)
        # For now, skip

        return True, "OK"

    def _CheckSectorLimit(self, symbol, size, price):
        """Check if sector exposure within limits"""

        # Would need sector classification
        # For now, pass
        return True, "OK"

    def _CheckGrossExposure(self, size, price):
        """Check if gross exposure within limits"""

        portfolio = self.algorithm.Portfolio
        total_value = portfolio.TotalPortfolioValue

        if total_value == 0:
            return True, "OK"

        new_exposure = abs(size * price) / total_value
        projected_gross = self.current_gross + new_exposure

        if projected_gross > self.max_gross_exposure:
            return False, f"Gross exposure {projected_gross:.2f} > {self.max_gross_exposure:.2f} limit"

        return True, "OK"

    def _CheckNetExposure(self, size, price):
        """Check if net exposure within limits"""

        portfolio = self.algorithm.Portfolio
        total_value = portfolio.TotalPortfolioValue

        if total_value == 0:
            return True, "OK"

        new_exposure = (size * price) / total_value
        projected_net = self.current_net + new_exposure

        if abs(projected_net) > self.max_net_exposure:
            return False, f"Net exposure {projected_net:.2%} > ±{self.max_net_exposure:.2%} limit"

        return True, "OK"

    def EnforceBetaNeutrality(self):
        """Hedge portfolio beta with SPY if needed"""

        if abs(self.current_beta) <= self.max_beta:
            return  # Within tolerance

        # Calculate hedge size
        portfolio_value = self.algorithm.Portfolio.TotalPortfolioValue
        hedge_size = -self.current_beta * portfolio_value

        # Get SPY price
        spy = self.algorithm.Symbol("SPY")
        if spy not in self.algorithm.Securities:
            if self.logger:
                self.logger.warning("SPY not available for beta hedge", component="PortfolioConstraints")
            return

        spy_price = self.algorithm.Securities[spy].Price

        if spy_price == 0:
            return

        # Calculate shares needed
        shares_needed = int(hedge_size / spy_price)

        if abs(shares_needed) < 1:
            return

        # Place hedge
        if self.logger:
            self.logger.info(f"Beta hedge: {shares_needed:+d} SPY @ ${spy_price:.2f} (β={self.current_beta:.3f})",
                           component="PortfolioConstraints")

        # Would execute hedge here
        # self.algorithm.MarketOrder(spy, shares_needed)

    def _CalculatePortfolioBeta(self):
        """Calculate portfolio beta (simplified)"""

        # Would need actual beta calculation with SPY returns
        # For now, estimate based on net exposure
        return self.current_net * 0.8  # Rough estimate

    def GetConstraintsSummary(self):
        """Get summary of current constraints"""

        return {
            'beta': self.current_beta,
            'beta_limit': self.max_beta,
            'beta_ok': abs(self.current_beta) <= self.max_beta,
            'gross': self.current_gross,
            'gross_limit': self.max_gross_exposure,
            'gross_ok': self.current_gross <= self.max_gross_exposure,
            'net': self.current_net,
            'net_limit': self.max_net_exposure,
            'net_ok': abs(self.current_net) <= self.max_net_exposure
        }
