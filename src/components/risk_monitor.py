"""
Risk Monitor
Tracks all key metrics, circuit breakers, and generates reports
Phase 1: Observation and logging only
"""

from AlgorithmImports import *
from collections import defaultdict
from datetime import datetime

class RiskMonitor:
    """Monitor risk metrics and generate reports"""

    def __init__(self, algorithm):
        self.algorithm = algorithm
        self.config = algorithm.config

        # Daily tracking
        self.daily_stats = self._InitDailyStats()

        # Circuit breaker states
        self.breakers = {
            'consecutive_stopouts': 0,
            'daily_loss_breach': False,
            'weekly_loss_breach': False,
            'liquidity_crisis': False,
            'correlation_spike': False
        }

        # Trade log
        self.trades_today = []
        self.extremes_detected = []

        # Performance tracking
        self.equity_curve = []
        self.drawdown_history = []

    def _InitDailyStats(self):
        """Initialize daily statistics"""
        return {
            'date': None,
            'extremes_detected': 0,
            'trades_attempted': 0,
            'trades_executed': 0,
            'dominant_regime': 'Unknown',
            'avg_gpm': 0.0,
            'active_avwap_tracks': 0,
            'blocked_trades': defaultdict(int),  # reason -> count
            'regime_changes': 0,
            'vix_level': None,
            'correlation_breakdown': None  # None = not computed
        }

    def Update(self, current_time, regime_state, candidates):
        """
        Update risk metrics

        Args:
            current_time: Current timestamp
            regime_state: Dict from HMMRegime
            candidates: List of (symbol, extreme_info) tuples
        """

        # Update date if new day
        current_date = current_time.date()
        if self.daily_stats['date'] != current_date:
            # New day - reset daily stats
            self.daily_stats = self._InitDailyStats()
            self.daily_stats['date'] = current_date
            self.trades_today = []
            self.extremes_detected = []

        # Update regime tracking
        self.daily_stats['dominant_regime'] = regime_state['dominant_state']
        self.daily_stats['avg_gpm'] = regime_state['gpm']
        self.daily_stats['correlation_breakdown'] = regime_state.get('correlation_breakdown', None)

        # Track extremes
        self.daily_stats['extremes_detected'] += len(candidates)

        for symbol, info in candidates:
            self.extremes_detected.append({
                'time': current_time,
                'symbol': symbol,
                'z_score': info['z_score'],
                'vol_anomaly': info['vol_anomaly'],
                'direction': info['direction']
            })

        # Update A-VWAP track count
        self.daily_stats['active_avwap_tracks'] = self.algorithm.avwap_tracker.GetActiveTracks()

        # Check circuit breakers
        self._CheckCircuitBreakers()

    def _CheckCircuitBreakers(self):
        """Check if any circuit breakers should fire"""

        # Phase 1: Just monitor, don't enforce
        # In later phases, these would halt trading

        # Daily loss check
        if self.algorithm.Portfolio.TotalPortfolioValue < self.config.INITIAL_CAPITAL * 0.95:
            if not self.breakers['daily_loss_breach']:
                self.breakers['daily_loss_breach'] = True
                self.algorithm.Log("⚠️ Circuit Breaker: Daily loss > 5%")
        else:
            self.breakers['daily_loss_breach'] = False

        # Correlation spike (not yet implemented)
        corr = self.daily_stats['correlation_breakdown']
        if corr is not None and corr > 0.85:
            if not self.breakers['correlation_spike']:
                self.breakers['correlation_spike'] = True
                self.algorithm.Log("⚠️ Circuit Breaker: Correlation spike > 0.85")
        elif corr is not None:
            self.breakers['correlation_spike'] = False
        # If corr is None, preserve previous breaker state (not computed yet)

    def LogBlockedTrade(self, symbol, reason):
        """Log a trade that was blocked and why"""
        self.daily_stats['blocked_trades'][reason] += 1
        self.algorithm.Log(f"❌ Trade Blocked: {symbol} - {reason}")

    def LogTrade(self, symbol, direction, size, price, reason):
        """Log a trade execution"""
        trade = {
            'time': self.algorithm.Time,
            'symbol': symbol,
            'direction': direction,
            'size': size,
            'price': price,
            'reason': reason
        }
        self.trades_today.append(trade)
        self.daily_stats['trades_executed'] += 1

        self.algorithm.Log(f"✅ Trade Executed: {direction} {size} {symbol} @ ${price:.2f} ({reason})")

    def GetDailySummary(self):
        """Generate daily summary report"""
        # Format correlation value clearly
        corr = self.daily_stats['correlation_breakdown']
        corr_str = "not computed" if corr is None else f"{corr:.2f}"

        summary = {
            'extremes_detected': self.daily_stats['extremes_detected'],
            'trades_attempted': self.daily_stats['trades_attempted'],
            'trades_executed': self.daily_stats['trades_executed'],
            'dominant_regime': self.daily_stats['dominant_regime'],
            'active_avwap_tracks': self.daily_stats['active_avwap_tracks'],
            'correlation_breakdown': corr_str,  # Show "not computed" vs numeric value
            'blocked_trades': dict(self.daily_stats['blocked_trades']),
            'circuit_breakers_active': self._GetActiveBreakers()
        }

        return summary

    def _GetActiveBreakers(self):
        """Get list of active circuit breakers"""
        active = []
        for breaker, is_active in self.breakers.items():
            if is_active:
                active.append(breaker)
        return active

    def GetExtremeSummary(self):
        """Get summary of detected extremes today"""
        if not self.extremes_detected:
            return "No extremes detected today"

        summary = f"\n{'='*60}\n"
        summary += f"EXTREMES DETECTED TODAY: {len(self.extremes_detected)}\n"
        summary += f"{'='*60}\n"

        for ext in self.extremes_detected[-10:]:  # Last 10
            summary += f"{ext['time'].strftime('%H:%M')} | {ext['symbol']:6s} | "
            summary += f"Z={ext['z_score']:+.2f} | Vol={ext['vol_anomaly']:.1f}x | "
            summary += f"{ext['direction']:>4s}\n"

        return summary

    def CalculateDrawdown(self):
        """Calculate current drawdown"""
        if not self.equity_curve:
            return 0.0

        peak = max(self.equity_curve)
        current = self.algorithm.Portfolio.TotalPortfolioValue

        if peak > 0:
            dd = (current - peak) / peak
            return dd
        return 0.0

    def UpdateEquityCurve(self):
        """Update equity curve for drawdown calculation"""
        self.equity_curve.append(self.algorithm.Portfolio.TotalPortfolioValue)

        # Calculate current drawdown
        dd = self.CalculateDrawdown()
        self.drawdown_history.append({
            'time': self.algorithm.Time,
            'drawdown': dd
        })

        # Keep only last 252 days (1 year)
        if len(self.equity_curve) > 252:
            self.equity_curve = self.equity_curve[-252:]
            self.drawdown_history = self.drawdown_history[-252:]

    def GetDrawdownLadderMultiplier(self):
        """
        Get position size multiplier based on drawdown ladder
        Phase 1: Just observe, don't apply
        """
        dd = abs(self.CalculateDrawdown())

        for i, threshold in enumerate(self.config.DD_THRESHOLDS):
            if dd >= threshold:
                multiplier = self.config.DD_MULTIPLIERS[i]
                if multiplier < 1.0:
                    self.algorithm.Log(f" Drawdown {dd:.1%} -> Size Multiplier {multiplier:.2f}")
                return multiplier

        return 1.0  # No drawdown scaling

    def GenerateWeeklyReport(self):
        """Generate weekly performance report"""
        report = f"\n{'='*60}\n"
        report += f"WEEKLY REPORT - {self.algorithm.Time.strftime('%Y-%m-%d')}\n"
        report += f"{'='*60}\n"

        # Performance metrics
        report += f"Portfolio Value: ${self.algorithm.Portfolio.TotalPortfolioValue:,.2f}\n"
        report += f"Cash: ${self.algorithm.Portfolio.Cash:,.2f}\n"
        report += f"Current Drawdown: {self.CalculateDrawdown():.2%}\n"

        # Trading activity
        report += f"\nTrading Activity:\n"
        report += f"  Extremes Detected: {self.daily_stats['extremes_detected']}\n"
        report += f"  Trades Executed: {self.daily_stats['trades_executed']}\n"

        # Circuit breakers
        active_breakers = self._GetActiveBreakers()
        if active_breakers:
            report += f"\n⚠️ Active Circuit Breakers:\n"
            for breaker in active_breakers:
                report += f"  - {breaker}\n"
        else:
            report += f"\n✅ No active circuit breakers\n"

        report += f"{'='*60}\n"

        return report
