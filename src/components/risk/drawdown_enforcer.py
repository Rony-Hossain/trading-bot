"""
Drawdown Enforcer - Phase 2

Enforces the drawdown ladder by actually reducing position sizes during drawdowns.

Drawdown Ladder:
- 10% DD → 0.75x size
- 20% DD → 0.50x size
- 30% DD → 0.25x size
- 40% DD → 0.00x (HALT all trading)

Usage:
    from drawdown_enforcer import DrawdownEnforcer

    enforcer = DrawdownEnforcer(algorithm)
    multiplier = enforcer.GetSizeMultiplier(current_dd)
    should_halt = enforcer.ShouldHalt(current_dd)
"""

from AlgorithmImports import *
from collections import deque

class DrawdownEnforcer:
    """
    Enforce drawdown-based position sizing ladder
    """

    def __init__(self, algorithm):
        self.algorithm = algorithm
        self.logger = algorithm.logger if hasattr(algorithm, 'logger') else None
        self.alert_manager = algorithm.alert_manager if hasattr(algorithm, 'alert_manager') else None

        # Drawdown ladder configuration
        self.dd_thresholds = [0.10, 0.20, 0.30, 0.40]
        self.dd_multipliers = [0.75, 0.50, 0.25, 0.00]

        # Tracking
        self.equity_curve = deque(maxlen=252 * 390)  # 1 year of minute bars
        self.peak_value = None
        self.current_drawdown = 0.0
        self.current_multiplier = 1.0
        self.current_rung = 0  # Which rung of the ladder we're on

        # Historical tracking
        self.dd_history = deque(maxlen=252)  # 1 year of daily DD
        self.max_dd_hit = 0.0

        # Alert tracking
        self.last_alert_rung = -1

        if self.logger:
            self.logger.info("DrawdownEnforcer initialized", component="DrawdownEnforcer")

    def Update(self, portfolio_value):
        """
        Update equity curve and calculate current drawdown

        Args:
            portfolio_value: Current portfolio total value

        Returns:
            dict with DD info
        """

        # Update equity curve
        self.equity_curve.append(portfolio_value)

        # Initialize peak if first update
        if self.peak_value is None:
            self.peak_value = portfolio_value

        # Update peak
        if portfolio_value > self.peak_value:
            self.peak_value = portfolio_value

        # Calculate drawdown
        if self.peak_value > 0:
            self.current_drawdown = (portfolio_value - self.peak_value) / self.peak_value
        else:
            self.current_drawdown = 0.0

        # Track max DD
        if abs(self.current_drawdown) > self.max_dd_hit:
            self.max_dd_hit = abs(self.current_drawdown)

        # Determine current ladder rung
        old_rung = self.current_rung
        self.current_rung = self._GetCurrentRung(abs(self.current_drawdown))
        self.current_multiplier = self._GetMultiplierForRung(self.current_rung)

        # Alert on rung change
        if self.current_rung != old_rung and self.current_rung > 0:
            self._AlertRungChange(old_rung, self.current_rung, abs(self.current_drawdown))

        # Store daily DD
        if len(self.dd_history) == 0 or self.dd_history[-1] != self.current_drawdown:
            self.dd_history.append(self.current_drawdown)

        return {
            'current_drawdown': self.current_drawdown,
            'current_rung': self.current_rung,
            'current_multiplier': self.current_multiplier,
            'peak_value': self.peak_value,
            'max_dd_hit': self.max_dd_hit
        }

    def _GetCurrentRung(self, abs_dd):
        """
        Determine which rung of the ladder we're on

        Returns: 0 (no DD), 1 (10%), 2 (20%), 3 (30%), 4 (40%+)
        """
        for i, threshold in enumerate(self.dd_thresholds):
            if abs_dd >= threshold:
                continue
            else:
                return i

        return len(self.dd_thresholds)  # Highest rung

    def _GetMultiplierForRung(self, rung):
        """Get the size multiplier for a given rung"""
        if rung == 0:
            return 1.0
        elif rung <= len(self.dd_multipliers):
            return self.dd_multipliers[rung - 1]
        else:
            return 0.0

    def GetSizeMultiplier(self, current_dd=None):
        """
        Get current position size multiplier based on drawdown

        Args:
            current_dd: Optional specific DD to check (otherwise uses current)

        Returns:
            float: Multiplier (0.0 to 1.0)
        """

        if current_dd is None:
            return self.current_multiplier

        abs_dd = abs(current_dd)
        rung = self._GetCurrentRung(abs_dd)
        return self._GetMultiplierForRung(rung)

    def ShouldHalt(self, current_dd=None):
        """
        Check if trading should be halted due to drawdown

        Returns:
            bool: True if should halt (DD >= 40%)
        """

        if current_dd is None:
            abs_dd = abs(self.current_drawdown)
        else:
            abs_dd = abs(current_dd)

        return abs_dd >= self.dd_thresholds[-1]  # 40%

    def GetDrawdownInfo(self):
        """Get detailed drawdown information"""

        return {
            'current_dd': self.current_drawdown,
            'current_dd_pct': abs(self.current_drawdown) * 100,
            'current_rung': self.current_rung,
            'current_multiplier': self.current_multiplier,
            'peak_value': self.peak_value,
            'current_value': self.equity_curve[-1] if self.equity_curve else 0,
            'max_dd_hit': self.max_dd_hit,
            'should_halt': self.ShouldHalt(),
            'ladder': self._GetLadderStatus()
        }

    def _GetLadderStatus(self):
        """Get status of each ladder rung"""

        abs_dd = abs(self.current_drawdown)

        ladder = []
        for i, (threshold, multiplier) in enumerate(zip(self.dd_thresholds, self.dd_multipliers)):
            status = {
                'rung': i + 1,
                'threshold': threshold,
                'threshold_pct': threshold * 100,
                'multiplier': multiplier,
                'active': abs_dd >= threshold
            }
            ladder.append(status)

        return ladder

    def _AlertRungChange(self, old_rung, new_rung, abs_dd):
        """Alert when moving to a new rung of the ladder"""

        # Only alert once per rung
        if self.last_alert_rung == new_rung:
            return

        self.last_alert_rung = new_rung

        # Get multiplier
        multiplier = self.current_multiplier

        # Determine severity
        if new_rung >= 3:  # 30% or more
            level = 'critical'
        elif new_rung >= 2:  # 20% or more
            level = 'error'
        else:
            level = 'warning'

        # Create message
        message = f"Drawdown Ladder: Rung {new_rung} activated - DD {abs_dd:.2%} → Size {multiplier:.2f}x"

        if self.logger:
            if level == 'critical':
                self.logger.critical(message, component="DrawdownEnforcer")
            elif level == 'error':
                self.logger.error(message, component="DrawdownEnforcer")
            else:
                self.logger.warning(message, component="DrawdownEnforcer")

        # Send alert
        if self.alert_manager:
            self.alert_manager.alert_drawdown(abs_dd, self.dd_thresholds[new_rung - 1])

    def GetRecoveryInfo(self):
        """Get information about recovery from drawdown"""

        if len(self.equity_curve) < 2:
            return None

        # Check if recovering
        current_val = self.equity_curve[-1]
        prev_val = self.equity_curve[-2]

        is_recovering = current_val > prev_val

        # Distance to peak
        distance_to_peak = (self.peak_value - current_val) / self.peak_value if self.peak_value > 0 else 0

        # Estimated bars to recovery (linear extrapolation)
        if is_recovering and prev_val > 0:
            recovery_rate = (current_val - prev_val) / prev_val
            if recovery_rate > 0:
                bars_to_recovery = int(distance_to_peak / recovery_rate)
            else:
                bars_to_recovery = None
        else:
            bars_to_recovery = None

        return {
            'is_recovering': is_recovering,
            'distance_to_peak': distance_to_peak,
            'distance_to_peak_pct': distance_to_peak * 100,
            'bars_to_recovery': bars_to_recovery,
            'recovery_rate': recovery_rate if is_recovering else 0
        }

    def Reset(self):
        """Reset drawdown tracking (use carefully!)"""

        if self.logger:
            self.logger.warning("Drawdown enforcer reset - peak reset to current value",
                              component="DrawdownEnforcer")

        if self.equity_curve:
            self.peak_value = self.equity_curve[-1]

        self.current_drawdown = 0.0
        self.current_rung = 0
        self.current_multiplier = 1.0
        self.last_alert_rung = -1

    def GetSummary(self):
        """Get summary for logging"""

        info = self.GetDrawdownInfo()

        summary = f"DD: {info['current_dd_pct']:.1f}% | "
        summary += f"Rung: {info['current_rung']}/4 | "
        summary += f"Size: {info['current_multiplier']:.2f}x | "
        summary += f"Peak: ${info['peak_value']:,.2f}"

        if info['should_halt']:
            summary += " |  HALTED"

        return summary
