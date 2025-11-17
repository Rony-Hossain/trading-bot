from AlgorithmImports import *
from collections import defaultdict
from datetime import datetime, date


class RiskMonitor:
    """Monitor risk metrics and generate reports."""

    def __init__(self, algorithm):
        self.algorithm = algorithm
        self.config = algorithm.config

        # Daily tracking
        self.daily_stats = self._InitDailyStats()

        # Circuit breaker states
        self.breakers = {
            "consecutive_stopouts": 0,
            "daily_loss_breach": False,
            "weekly_loss_breach": False,
            "liquidity_crisis": False,
            "correlation_spike": False,
            "global_dd_halt": False,  # set when drawdown exceeds MAX_TOTAL_DRAWDOWN_PCT
        }

        # Trade / signal logs
        self.trades_today = []
        self.extremes_detected = []

        # Performance tracking
        self.equity_curve = []
        self.drawdown_history = []

        # Baselines for daily / weekly loss
        self.start_of_day_equity: float | None = None
        self.start_of_week_equity: float | None = None
        self.current_week_start: date | None = None

    # --------------------------------------------------------------------- #
    #   INTERNAL STATE INIT
    # --------------------------------------------------------------------- #
    def _InitDailyStats(self):
        """Initialize daily statistics."""
        return {
            "date": None,
            "extremes_detected": 0,
            "trades_attempted": 0,
            "trades_executed": 0,
            "dominant_regime": "Unknown",
            "avg_gpm": 0.0,
            "active_avwap_tracks": 0,
            "blocked_trades": defaultdict(int),  # reason -> count
            "regime_changes": 0,
            "vix_level": None,
            "correlation_breakdown": None,  # None = not computed
            "current_drawdown_pct": 0.0,
            "daily_loss_pct": 0.0,
            "weekly_loss_pct": 0.0,
        }

    def _OnNewDay(self, current_date: date):
        """Handle daily rollover: reset daily stats and baselines where needed."""
        self.daily_stats = self._InitDailyStats()
        self.daily_stats["date"] = current_date
        self.trades_today = []
        self.extremes_detected = []

        equity = self.algorithm.Portfolio.TotalPortfolioValue
        self.start_of_day_equity = equity
        self.daily_stats["daily_loss_pct"] = 0.0

        # Reset daily breaker
        self.breakers["daily_loss_breach"] = False

        # New week if Monday or first time
        if self.current_week_start is None or current_date.weekday() == 0:
            self.current_week_start = current_date
            self.start_of_week_equity = equity
            self.daily_stats["weekly_loss_pct"] = 0.0
            self.breakers["weekly_loss_breach"] = False

    # --------------------------------------------------------------------- #
    #   MAIN UPDATE
    # --------------------------------------------------------------------- #
    def Update(self, current_time, regime_state, candidates):
        """
        Update risk metrics.

        Args:
            current_time: Current timestamp (algorithm.Time)
            regime_state: Dict from HMMRegime
            candidates: List of (symbol, extreme_info) tuples
        """
        current_date = current_time.date()

        # Detect new day
        if self.daily_stats["date"] != current_date:
            self._OnNewDay(current_date)

        # Update regime tracking
        self.daily_stats["dominant_regime"] = regime_state["dominant_state"]
        self.daily_stats["avg_gpm"] = regime_state["gpm"]
        self.daily_stats["correlation_breakdown"] = regime_state.get(
            "correlation_breakdown", None
        )

        # Track extremes
        self.daily_stats["extremes_detected"] += len(candidates)

        for symbol, info in candidates:
            self.extremes_detected.append(
                {
                    "time": current_time,
                    "symbol": symbol,
                    "z_score": info["z_score"],
                    "vol_anomaly": info["vol_anomaly"],
                    "direction": info["direction"],
                }
            )

        # Update A-VWAP track count
        self.daily_stats["active_avwap_tracks"] = (
            self.algorithm.avwap_tracker.GetActiveTracks()
            if hasattr(self.algorithm, "avwap_tracker")
            else 0
        )

        # Update equity / drawdown time series
        self.UpdateEquityCurve()

        # Update loss-based circuit breakers (daily / weekly)
        self._UpdateLossBreakers()

        # Check correlation and other circuit breakers
        self._CheckCircuitBreakers()

    # --------------------------------------------------------------------- #
    #   CIRCUIT BREAKERS
    # --------------------------------------------------------------------- #
    def _UpdateLossBreakers(self):
        """Update daily and weekly loss breakers based on config thresholds."""
        equity = self.algorithm.Portfolio.TotalPortfolioValue

        # Daily loss
        if self.start_of_day_equity:
            daily_loss = (equity - self.start_of_day_equity) / self.start_of_day_equity
            self.daily_stats["daily_loss_pct"] = daily_loss

            if daily_loss <= -self.config.CB_DAILY_LOSS:
                if not self.breakers["daily_loss_breach"]:
                    self.breakers["daily_loss_breach"] = True
                    self.algorithm.Log(
                        f"Circuit Breaker: Daily loss {daily_loss:.2%} "
                        f"<= -{self.config.CB_DAILY_LOSS:.2%}"
                    )

        # Weekly loss
        if self.start_of_week_equity:
            weekly_loss = (
                equity - self.start_of_week_equity
            ) / self.start_of_week_equity
            self.daily_stats["weekly_loss_pct"] = weekly_loss

            if weekly_loss <= -self.config.CB_WEEKLY_LOSS:
                if not self.breakers["weekly_loss_breach"]:
                    self.breakers["weekly_loss_breach"] = True
                    self.algorithm.Log(
                        f"Circuit Breaker: Weekly loss {weekly_loss:.2%} "
                        f"<= -{self.config.CB_WEEKLY_LOSS:.2%}"
                    )

    def _CheckCircuitBreakers(self):
        """Check non-loss-based circuit breakers (correlation, liquidity, etc.)."""

        # Correlation spike (if correlation_breakdown is provided)
        corr = self.daily_stats["correlation_breakdown"]
        if corr is not None:
            if corr > self.config.CORR_MARKET_NEUTRAL:
                if not self.breakers["correlation_spike"]:
                    self.breakers["correlation_spike"] = True
                    self.algorithm.Log(
                        f"Circuit Breaker: Correlation spike {corr:.2f} "
                        f"> {self.config.CORR_MARKET_NEUTRAL:.2f}"
                    )
            else:
                self.breakers["correlation_spike"] = False
        # Liquidity crisis is something you can set from outside if you detect it
        # (e.g. via HealthMonitor or a dedicated liquidity checker).

    # --------------------------------------------------------------------- #
    #   LOGGING HELPERS
    # --------------------------------------------------------------------- #
    def LogBlockedTrade(self, symbol, reason: str):
        """Log a trade that was blocked and why."""
        self.daily_stats["blocked_trades"][reason] += 1
        self.algorithm.Log(f"Trade Blocked: {symbol} - {reason}")

    def LogTrade(self, symbol, direction, size, price, reason):
        """Log a trade execution."""
        trade = {
            "time": self.algorithm.Time,
            "symbol": symbol,
            "direction": direction,
            "size": size,
            "price": price,
            "reason": reason,
        }
        self.trades_today.append(trade)
        self.daily_stats["trades_executed"] += 1

        self.algorithm.Log(
            f"Trade Executed: {direction} {size} {symbol} @ ${price:.2f} ({reason})"
        )

    # --------------------------------------------------------------------- #
    #   SUMMARIES
    # --------------------------------------------------------------------- #
    def GetDailySummary(self):
        """Generate daily summary report."""
        corr = self.daily_stats["correlation_breakdown"]
        corr_str = "not computed" if corr is None else f"{corr:.2f}"

        summary = {
            "extremes_detected": self.daily_stats["extremes_detected"],
            "trades_attempted": self.daily_stats["trades_attempted"],
            "trades_executed": self.daily_stats["trades_executed"],
            "dominant_regime": self.daily_stats["dominant_regime"],
            "active_avwap_tracks": self.daily_stats["active_avwap_tracks"],
            "correlation_breakdown": corr_str,
            "blocked_trades": dict(self.daily_stats["blocked_trades"]),
            "circuit_breakers_active": self._GetActiveBreakers(),
            "current_drawdown_pct": self.daily_stats["current_drawdown_pct"],
            "daily_loss_pct": self.daily_stats["daily_loss_pct"],
            "weekly_loss_pct": self.daily_stats["weekly_loss_pct"],
        }
        return summary

    def _GetActiveBreakers(self):
        """Get list of active circuit breakers."""
        return [k for k, v in self.breakers.items() if v]

    def GetExtremeSummary(self):
        """Get summary of detected extremes today."""
        if not self.extremes_detected:
            return "No extremes detected today"

        summary = f"\n{'=' * 60}\n"
        summary += f"EXTREMES DETECTED TODAY: {len(self.extremes_detected)}\n"
        summary += f"{'=' * 60}\n"

        for ext in self.extremes_detected[-10:]:  # Last 10
            summary += f"{ext['time'].strftime('%H:%M')} | {ext['symbol']:6s} | "
            summary += f"Z={ext['z_score']:+.2f} | Vol={ext['vol_anomaly']:.1f}x | "
            summary += f"{ext['direction']:>4s}\n"

        return summary

    # --------------------------------------------------------------------- #
    #   DRAWDOWN & RISK MULTIPLIERS
    # --------------------------------------------------------------------- #
    def CalculateDrawdown(self) -> float:
        """Calculate current peak-to-trough drawdown (negative number)."""
        if not self.equity_curve:
            return 0.0

        peak = max(self.equity_curve)
        current = self.algorithm.Portfolio.TotalPortfolioValue
        if peak <= 0:
            return 0.0

        dd = (current - peak) / peak
        return dd

    def UpdateEquityCurve(self):
        """Update equity curve for drawdown calculation."""
        equity = self.algorithm.Portfolio.TotalPortfolioValue
        self.equity_curve.append(equity)

        dd = self.CalculateDrawdown()
        self.drawdown_history.append({"time": self.algorithm.Time, "drawdown": dd})
        self.daily_stats["current_drawdown_pct"] = dd

        # Keep only last 252 days (approx 1 year)
        if len(self.equity_curve) > 252:
            self.equity_curve = self.equity_curve[-252:]
            self.drawdown_history = self.drawdown_history[-252:]

    def GetDrawdownLadderMultiplier(self) -> float:
        """
        Get position size multiplier based on drawdown ladder.

        Uses DD_THRESHOLDS / DD_MULTIPLIERS from config.
        """
        dd = abs(self.CalculateDrawdown())

        for i, threshold in enumerate(self.config.DD_THRESHOLDS):
            if dd >= threshold:
                multiplier = self.config.DD_MULTIPLIERS[i]
                if multiplier < 1.0:
                    self.algorithm.Log(
                        f"Drawdown {dd:.1%} -> Size Multiplier {multiplier:.2f}"
                    )
                return multiplier

        return 1.0  # No drawdown scaling

    def ShouldHaltTrading(self) -> bool:
        """
        Hard gate: return True if we must stop opening NEW positions.

        Logic:
        - Total peak-to-trough drawdown >= MAX_TOTAL_DRAWDOWN_PCT
        - OR daily_loss_breach / weekly_loss_breach
        - OR liquidity_crisis / correlation_spike flags set by other components
        """
        # 1) Drawdown-based kill switch
        current_dd = abs(self.CalculateDrawdown())
        if current_dd >= self.config.MAX_TOTAL_DRAWDOWN_PCT:
            if not self.breakers.get("global_dd_halt", False):
                self.breakers["global_dd_halt"] = True
                self.algorithm.Log(
                    f"RISK HALT (RiskMonitor): drawdown {current_dd:.1%} "
                    f">= {self.config.MAX_TOTAL_DRAWDOWN_PCT:.1%}"
                )
            return True

        # 2) Circuit breakers (loss / liquidity / correlation)
        if self.breakers.get("daily_loss_breach", False):
            return True
        if self.breakers.get("weekly_loss_breach", False):
            return True
        if self.breakers.get("liquidity_crisis", False):
            return True
        if self.breakers.get("correlation_spike", False):
            return True

        # Reset global DD halt if we've recovered
        self.breakers["global_dd_halt"] = False
        return False

    def GetRiskMultiplier(self) -> float:
        """
        Soft risk multiplier to feed into position sizing.

        For now this just reuses the drawdown ladder:
        - <10% DD -> 1.0x
        - ≥10% DD -> 0.75x
        - ≥20% DD -> 0.5x
        - ≥30% DD -> 0.25x
        - ≥40% DD -> 0.0x
        """
        return self.GetDrawdownLadderMultiplier()

    # --------------------------------------------------------------------- #
    #   WEEKLY REPORT
    # --------------------------------------------------------------------- #
    def GenerateWeeklyReport(self):
        """Generate weekly performance report."""
        report = f"\n{'=' * 60}\n"
        report += f"WEEKLY REPORT - {self.algorithm.Time.strftime('%Y-%m-%d')}\n"
        report += f"{'=' * 60}\n"

        # Performance metrics
        report += (
            f"Portfolio Value: ${self.algorithm.Portfolio.TotalPortfolioValue:,.2f}\n"
        )
        report += f"Cash: ${self.algorithm.Portfolio.Cash:,.2f}\n"
        report += f"Current Drawdown: {self.CalculateDrawdown():.2%}\n"

        # Trading activity
        report += f"\nTrading Activity:\n"
        report += f"  Extremes Detected: {self.daily_stats['extremes_detected']}\n"
        report += f"  Trades Executed: {self.daily_stats['trades_executed']}\n"

        # Circuit breakers
        active_breakers = self._GetActiveBreakers()
        if active_breakers:
            report += f"\n Active Circuit Breakers:\n"
            for breaker in active_breakers:
                report += f"  - {breaker}\n"
        else:
            report += f"\nNo active circuit breakers\n"

        report += f"{'=' * 60}\n"
        return report
