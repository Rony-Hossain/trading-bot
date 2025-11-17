"""
PVS Monitor - Personal Volatility Score
Psychological Governor for Phase 2

Tracks emotional/psychological state to prevent emotional trading.

Components:
- Fear: Consecutive losses, volatility spikes, large losses
- Fatigue: Overtrading, time pressure, late hours
- Confidence: Rule violations, revenge trading, off-strategy

PVS Scale:
- 0-6: Normal (no adjustment)
- 7-9: Warning (0.5x size)
- >9: Critical (halt new entries)

Usage:
    from pvs_monitor import PVSMonitor

    pvs = PVSMonitor(algorithm)
    score = pvs.GetPVS()
    multiplier = pvs.GetSizeMultiplier()
"""

from AlgorithmImports import *
from collections import deque
from datetime import datetime, timedelta

class PVSMonitor:
    """
    Personal Volatility Score - Psychological governance
    """

    def __init__(self, algorithm):
        self.algorithm = algorithm
        self.logger = algorithm.logger if hasattr(algorithm, 'logger') else None
        self.alert_manager = algorithm.alert_manager if hasattr(algorithm, 'alert_manager') else None

        # PVS thresholds
        self.pvs_warning = 7
        self.pvs_halt = 9

        # Small capital multiplier (more sensitive for <$5k)
        self.small_capital_threshold = 5000
        self.small_capital_mult = 1.5

        # Component scores
        self.fear_score = 0.0
        self.fatigue_score = 0.0
        self.confidence_score = 0.0

        # Tracking
        self.recent_trades = deque(maxlen=50)
        self.consecutive_losses = 0
        self.recent_loss_streak = 0
        self.trades_this_hour = deque(maxlen=10)
        self.rule_violations_today = 0
        self.trading_hours_today = 0

        # Historical
        self.pvs_history = deque(maxlen=100)
        self.last_pvs_alert = None

        # Market conditions
        self.last_vix_check = None
        self.high_vix_flag = False

        if self.logger:
            self.logger.info("PVSMonitor initialized", component="PVSMonitor")

    def Update(self, portfolio_value, vix_level=None):
        """
        Update PVS score based on current state

        Args:
            portfolio_value: Current portfolio value
            vix_level: Optional VIX level for fear component

        Returns:
            dict with PVS info
        """

        # Calculate each component
        self.fear_score = self._CalculateFear(portfolio_value, vix_level)
        self.fatigue_score = self._CalculateFatigue()
        self.confidence_score = self._CalculateConfidence()

        # Calculate total PVS
        raw_pvs = (self.fear_score + self.fatigue_score + self.confidence_score) / 3

        # Apply small capital multiplier if needed
        if portfolio_value < self.small_capital_threshold:
            raw_pvs *= self.small_capital_mult

        # Cap at 10
        pvs = min(raw_pvs, 10.0)

        # Store history
        self.pvs_history.append({
            'timestamp': self.algorithm.Time,
            'pvs': pvs,
            'fear': self.fear_score,
            'fatigue': self.fatigue_score,
            'confidence': self.confidence_score
        })

        # Alert on high PVS
        if pvs >= self.pvs_warning:
            self._AlertHighPVS(pvs)

        return {
            'pvs': pvs,
            'fear': self.fear_score,
            'fatigue': self.fatigue_score,
            'confidence': self.confidence_score,
            'should_halt': pvs > self.pvs_halt,
            'size_multiplier': self._GetSizeMultiplier(pvs)
        }

    def _CalculateFear(self, portfolio_value, vix_level):
        """
        Calculate fear component

        Factors:
        - Consecutive losses
        - Large intraday loss
        - VIX spike
        - Recent volatility
        """

        fear = 0.0

        # 1. Consecutive losses (max +3)
        if self.consecutive_losses >= 5:
            fear += 3.0
        elif self.consecutive_losses >= 3:
            fear += 2.0
        elif self.consecutive_losses >= 2:
            fear += 1.0

        # 2. Large intraday loss (max +2)
        if len(self.recent_trades) > 0:
            # Get today's P&L
            today_start = self.algorithm.Time.replace(hour=9, minute=30, second=0)
            today_trades = [t for t in self.recent_trades if t['timestamp'] >= today_start]

            if today_trades:
                today_pnl = sum(t.get('pnl', 0) for t in today_trades)
                loss_pct = today_pnl / portfolio_value if portfolio_value > 0 else 0

                if loss_pct < -0.05:  # >5% loss
                    fear += 2.0
                elif loss_pct < -0.03:  # >3% loss
                    fear += 1.0

        # 3. VIX spike (max +1)
        if vix_level is not None:
            self.last_vix_check = vix_level
            if vix_level > 30:
                fear += 1.0
                self.high_vix_flag = True
            else:
                self.high_vix_flag = False

        # 4. Recent loss streak intensity (max +1)
        if self.recent_loss_streak >= 4:
            fear += 1.0
        elif self.recent_loss_streak >= 3:
            fear += 0.5

        return min(fear, 7.0)  # Cap at 7

    def _CalculateFatigue(self):
        """
        Calculate fatigue component

        Factors:
        - Trades per hour
        - Consecutive hours trading
        - Late hours trading
        - Decision quality decline
        """

        fatigue = 0.0

        # 1. Trades per hour (max +2)
        hour_ago = self.algorithm.Time - timedelta(hours=1)
        recent_hour_trades = [t for t in self.trades_this_hour if t >= hour_ago]

        if len(recent_hour_trades) > 5:
            fatigue += 2.0
        elif len(recent_hour_trades) > 3:
            fatigue += 1.0

        # 2. Consecutive hours trading (max +2)
        if self.trading_hours_today > 5:
            fatigue += 2.0
        elif self.trading_hours_today > 3:
            fatigue += 1.0

        # 3. Late hours (after 3pm) (max +1)
        current_hour = self.algorithm.Time.hour
        if current_hour >= 15:
            fatigue += 1.0

        # 4. Number of trades today (max +1)
        today_trades = len([t for t in self.recent_trades
                           if t['timestamp'].date() == self.algorithm.Time.date()])

        if today_trades > 5:
            fatigue += 1.0
        elif today_trades > 3:
            fatigue += 0.5

        return min(fatigue, 6.0)  # Cap at 6

    def _CalculateConfidence(self):
        """
        Calculate confidence component (inverse - higher is worse)

        Factors:
        - Rule violations
        - Revenge trading detected
        - Off-strategy trades
        - Impulsive decisions
        """

        confidence = 0.0

        # 1. Rule violations today (max +3)
        if self.rule_violations_today >= 3:
            confidence += 3.0
        elif self.rule_violations_today >= 1:
            confidence += self.rule_violations_today

        # 2. Revenge trading detection (max +2)
        # Defined as: trade within 15 min of a loss
        if len(self.recent_trades) >= 2:
            last_trade = self.recent_trades[-1]
            prev_trade = self.recent_trades[-2]

            if prev_trade.get('pnl', 0) < 0:  # Previous was a loss
                time_diff = (last_trade['timestamp'] - prev_trade['timestamp']).total_seconds() / 60

                if time_diff < 15:  # Traded within 15 min
                    confidence += 2.0  # Likely revenge trade
                elif time_diff < 30:
                    confidence += 1.0  # Possibly revenge trade

        # 3. Off-strategy indicator (max +2)
        # Check if recent trades deviated from plan
        # (Would need more context - for now, check if too many quick trades)
        if len(self.recent_trades) >= 3:
            last_3 = list(self.recent_trades)[-3:]
            times = [t['timestamp'] for t in last_3]

            if len(times) == 3:
                span = (times[-1] - times[0]).total_seconds() / 60
                if span < 30:  # 3 trades in 30 minutes
                    confidence += 1.0

        return min(confidence, 7.0)  # Cap at 7

    def _GetSizeMultiplier(self, pvs):
        """Get position size multiplier based on PVS"""

        if pvs >= self.pvs_halt:
            return 0.0  # Halt
        elif pvs >= self.pvs_warning:
            return 0.5  # Half size
        else:
            return 1.0  # Normal

    def GetPVS(self):
        """Get current PVS score"""

        if not self.pvs_history:
            return 0.0

        return self.pvs_history[-1]['pvs']

    def GetSizeMultiplier(self):
        """Get current size multiplier"""

        pvs = self.GetPVS()
        return self._GetSizeMultiplier(pvs)

    def ShouldHalt(self):
        """Check if should halt new entries"""

        pvs = self.GetPVS()
        return pvs > self.pvs_halt

    def RecordTrade(self, symbol, pnl, was_winner, timestamp=None):
        """
        Record a trade for PVS calculation

        Args:
            symbol: Symbol traded
            pnl: P&L of trade
            was_winner: True if profitable
            timestamp: Trade timestamp
        """

        timestamp = timestamp or self.algorithm.Time

        trade = {
            'timestamp': timestamp,
            'symbol': str(symbol),
            'pnl': pnl,
            'was_winner': was_winner
        }

        self.recent_trades.append(trade)
        self.trades_this_hour.append(timestamp)

        # Update consecutive losses
        if was_winner:
            self.consecutive_losses = 0
        else:
            self.consecutive_losses += 1
            self.recent_loss_streak = max(self.recent_loss_streak, self.consecutive_losses)

    def RecordRuleViolation(self, violation_type, description):
        """Record a rule violation"""

        self.rule_violations_today += 1

        if self.logger:
            self.logger.warning(f"Rule violation: {violation_type} - {description}",
                              component="PVSMonitor")

    def ResetDaily(self):
        """Reset daily counters (call at market open)"""

        self.rule_violations_today = 0
        self.trading_hours_today = 0
        self.recent_loss_streak = 0

        if self.logger:
            self.logger.info("PVS daily reset", component="PVSMonitor")

    def _AlertHighPVS(self, pvs):
        """Alert when PVS is high"""

        # Rate limit alerts (once per hour)
        if self.last_pvs_alert:
            time_since = (self.algorithm.Time - self.last_pvs_alert).total_seconds() / 60
            if time_since < 60:
                return

        self.last_pvs_alert = self.algorithm.Time

        # Determine severity
        if pvs > self.pvs_halt:
            level = 'critical'
            message = f"PVS CRITICAL: {pvs:.1f}/10 - NEW ENTRIES HALTED"
        elif pvs >= self.pvs_warning:
            level = 'warning'
            message = f"PVS Warning: {pvs:.1f}/10 - Position sizes reduced to 0.5x"
        else:
            return

        if self.logger:
            if level == 'critical':
                self.logger.critical(message, component="PVSMonitor")
            else:
                self.logger.warning(message, component="PVSMonitor")

        # Send alert
        if self.alert_manager:
            details = {
                'pvs': pvs,
                'fear': self.fear_score,
                'fatigue': self.fatigue_score,
                'confidence': self.confidence_score,
                'consecutive_losses': self.consecutive_losses
            }

            self.alert_manager.send_alert(level, message, component='PVSMonitor', details=details)

    def GetPVSInfo(self):
        """Get detailed PVS information"""

        pvs = self.GetPVS()

        return {
            'pvs': pvs,
            'pvs_level': self._GetPVSLevel(pvs),
            'components': {
                'fear': self.fear_score,
                'fatigue': self.fatigue_score,
                'confidence': self.confidence_score
            },
            'factors': {
                'consecutive_losses': self.consecutive_losses,
                'trades_this_hour': len(self.trades_this_hour),
                'trades_today': len([t for t in self.recent_trades
                                    if t['timestamp'].date() == self.algorithm.Time.date()]),
                'rule_violations': self.rule_violations_today,
                'high_vix': self.high_vix_flag
            },
            'action': {
                'should_halt': self.ShouldHalt(),
                'size_multiplier': self.GetSizeMultiplier()
            }
        }

    def _GetPVSLevel(self, pvs):
        """Get PVS level description"""

        if pvs > 9:
            return 'CRITICAL'
        elif pvs >= 7:
            return 'WARNING'
        elif pvs >= 5:
            return 'ELEVATED'
        else:
            return 'NORMAL'

    def GetSummary(self):
        """Get summary for logging"""

        info = self.GetPVSInfo()

        summary = f"PVS: {info['pvs']:.1f}/10 ({info['pvs_level']}) | "
        summary += f"Fear: {info['components']['fear']:.1f} | "
        summary += f"Fatigue: {info['components']['fatigue']:.1f} | "
        summary += f"Confidence: {info['components']['confidence']:.1f}"

        if info['action']['should_halt']:
            summary += " |  HALT"
        elif info['action']['size_multiplier'] < 1.0:
            summary += f" | Size: {info['action']['size_multiplier']:.1f}x"

        return summary
