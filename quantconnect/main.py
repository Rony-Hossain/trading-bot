"""
Extreme-Aware Trading Strategy - Unified Main
==============================================

Single main file supporting multiple versions and trading modes.

VERSIONS (Features):
  v1 = Basic features (extreme detection, regime, A-VWAP)
  v2 = All features (v1 + drawdown ladder, PVS, cascade prevention, etc.)

MODES (Trading):
  Observation = Log signals only, no real trades
  Live Trading = Execute real trades

RECOMMENDED PATH:
  Week 1-4:  v1, observation  - Learn basic signals
  Week 5-8:  v2, observation  - Test advanced features
  Week 9+:   v2, live trading - Go live

Set config on line 78:
  Config(version=1, trading_enabled=False)  # v1, observation
  Config(version=2, trading_enabled=False)  # v2, observation
  Config(version=2, trading_enabled=True)   # v2, live trading

Author: AI Trading Systems
Version: 2.0 (Unified)
Date: January 2025
"""

from AlgorithmImports import *
from datetime import timedelta
import numpy as np

# Configuration
import sys
sys.path.append('./config')
from config import Config

# Phase 1 Components
from logger import StrategyLogger
from log_retrieval import LogRetrieval
from universe_filter import UniverseFilter
from extreme_detector import ExtremeDetector
from hmm_regime import HMMRegimeClassifier
from avwap_tracker import AVWAPTracker
from risk_monitor import RiskMonitor

# Part 1 Infrastructure
from alert_manager import AlertManager
from backtest_analyzer import BacktestAnalyzer
from health_monitor import HealthMonitor

# Advanced Components (v2+) (conditionally used)
from drawdown_enforcer import DrawdownEnforcer
from pvs_monitor import PVSMonitor
from exhaustion_detector import ExhaustionDetector
from portfolio_constraints import PortfolioConstraints
from cascade_prevention import CascadePrevention
from dynamic_sizer import DynamicSizer
from entry_timing import EntryTiming


class ExtremeAwareStrategy(QCAlgorithm):
    """
    Unified strategy supporting multiple versions and trading modes

    Usage:
        # v1, observation mode
        config = Config(version=1, trading_enabled=False)

        # v2, observation mode
        config = Config(version=2, trading_enabled=False)

        # v2, live trading
        config = Config(version=2, trading_enabled=True)
    """

    def Initialize(self):
        """Initialize algorithm with phase-aware configuration"""

        # ==================== BASIC SETUP ====================
        self.SetStartDate(2024, 1, 1)
        self.SetCash(1000)
        self.SetBrokerageModel(BrokerageName.InteractiveBrokersBrokerage, AccountType.Margin)

        # ==================== LOAD CONFIGURATION ====================
        # [!] SET YOUR CONFIGURATION HERE
        # Week 1-4:  Config(version=1, trading_enabled=False)  # Learn basics
        # Week 5-8:  Config(version=2, trading_enabled=False)  # Test advanced
        # Week 9+:   Config(version=2, trading_enabled=True)   # Go live

        self.config = Config(version=2, trading_enabled=False)  # [!] CHANGE THIS

        # ==================== LOGGING SYSTEM ====================
        self.logger = StrategyLogger(self)
        self.log_retrieval = LogRetrieval(self.logger)

        config_desc = self.config.GetDescription()
        self.logger.info("="*70, component="Main")
        self.logger.info(f"EXTREME-AWARE STRATEGY - {config_desc.upper()}", component="Main")
        self.logger.info("="*70, component="Main")

        # ==================== INFRASTRUCTURE (ALWAYS ENABLED) ====================

        # Alert System
        alert_config = {
            'enable_email': False,  # Set True when configured
            'enable_sms': False,
            'enable_slack': False,
            'enable_telegram': False,
            'alert_on_circuit_breakers': True,
            'alert_on_errors': True,
            'alert_on_detections': False,  # Too noisy
            'daily_summary_time': '16:05'
        }
        self.alert_manager = AlertManager(self, alert_config)

        # Enhanced Backtesting
        self.backtest_analyzer = BacktestAnalyzer(self)

        # Health Monitoring
        self.health_monitor = HealthMonitor(self)

        # ==================== PHASE 1 COMPONENTS (ALWAYS ENABLED) ====================

        # Universe Filter
        self.universe_filter = UniverseFilter(self)
        self.SetUniverseSelection(
            FineFundamentalUniverseSelectionModel(self.SelectCoarse, self.SelectFine)
        )

        # Extreme Detector
        self.extreme_detector = ExtremeDetector(self)

        # HMM Regime Classifier
        self.hmm_regime = HMMRegimeClassifier(self)

        # A-VWAP Tracker
        self.avwap_tracker = AVWAPTracker(self)

        # Risk Monitor
        self.risk_monitor = RiskMonitor(self)

        self.logger.info("[OK] Core components initialized", component="Main")

        # ==================== ADVANCED COMPONENTS (VERSION 2+) ====================

        if self.config.version >= 2:
            # Drawdown Enforcer
            self.drawdown_enforcer = DrawdownEnforcer(self)

            # PVS Monitor (Psychological)
            self.pvs_monitor = PVSMonitor(self)

            # Exhaustion Detector
            self.exhaustion_detector = ExhaustionDetector(self)

            # Portfolio Constraints
            self.portfolio_constraints = PortfolioConstraints(self)

            # Cascade Prevention
            self.cascade_prevention = CascadePrevention(self)

            # Dynamic Position Sizer
            self.dynamic_sizer = DynamicSizer(self)

            # Entry Timing Protocol
            self.entry_timing = EntryTiming(self)

            self.logger.info("[OK] Advanced components initialized", component="Main")
        else:
            # Stub components for v1 (not used)
            self.drawdown_enforcer = None
            self.pvs_monitor = None
            self.exhaustion_detector = None
            self.portfolio_constraints = None
            self.cascade_prevention = None
            self.dynamic_sizer = None
            self.entry_timing = None

            self.logger.info("ℹ Advanced components disabled (v1 mode)", component="Main")

        # ==================== DATA STRUCTURES ====================

        # Universe tracking
        self.active_symbols = []

        # Data buffers
        self.minute_bars = {}  # symbol -> list of minute bars

        # Detection tracking
        self.pending_entries = {}  # symbol -> entry info
        self.active_positions = {}  # symbol -> position info

        # Performance tracking
        self.trades_today = 0
        self.trades_this_hour = 0
        self.last_hour = None

        # Safety: Symbol cooldowns (prevent rapid re-entry)
        self.symbol_cooldowns = {}  # symbol -> exit_time
        self.COOLDOWN_MINUTES = 60  # Wait 60 min after exit before re-entry

        # Event-driven detection with rate limiting
        self.last_detection_scan = self.Time
        self.DETECTION_INTERVAL_MINUTES = 5  # Check every 5 minutes (rate limit)
        self.detections_this_hour = 0  # Track hourly detection rate
        self.MAX_DETECTIONS_PER_HOUR = 12  # Max 12 detections per hour

        # ==================== SCHEDULING ====================

        # Hourly scans
        self.Schedule.On(
            self.DateRules.EveryDay(),
            self.TimeRules.Every(timedelta(hours=1)),
            self.HourlyScan
        )

        # Market open
        self.Schedule.On(
            self.DateRules.EveryDay(),
            self.TimeRules.AfterMarketOpen("SPY", 1),
            self.OnMarketOpen
        )

        # Market close
        self.Schedule.On(
            self.DateRules.EveryDay(),
            self.TimeRules.BeforeMarketClose("SPY", 5),
            self.OnMarketClose
        )

        # ==================== WARMUP ====================
        self.SetWarmUp(timedelta(days=30))

        self.logger.info(f"Initialization complete - Entering warmup period", component="Main")
        self.logger.info(f"Version: {self.config.version} | Mode: {'OBSERVATION (no trades)' if self.config.OBSERVATION_MODE else 'LIVE TRADING'}",
                        component="Main")
        self.alert_manager.send_alert('info', f'Strategy initialized - {config_desc}', component='Main')

    # ==================== UNIVERSE SELECTION ====================

    def SelectCoarse(self, coarse):
        """Coarse universe filter"""
        if self.IsWarmingUp:
            return []

        return self.universe_filter.CoarseFilter(coarse)

    def SelectFine(self, fine):
        """Fine universe filter"""
        if self.IsWarmingUp:
            return []

        symbols = self.universe_filter.FineFilter(fine)
        self.active_symbols = symbols

        self.logger.info(f"Universe: {len(symbols)} stocks", component="Universe")
        return symbols

    # ==================== DATA HANDLING ====================

    def OnData(self, data):
        """Handle incoming data"""

        if self.IsWarmingUp:
            return

        # Update minute bars
        for symbol in self.active_symbols:
            if symbol in data and data[symbol]:
                bar = data[symbol]

                if symbol not in self.minute_bars:
                    self.minute_bars[symbol] = []

                bar_data = {
                    'time': self.Time,
                    'open': float(bar.Open),
                    'high': float(bar.High),
                    'low': float(bar.Low),
                    'close': float(bar.Close),
                    'volume': float(bar.Volume)
                }

                self.minute_bars[symbol].append(bar_data)

                # Keep last 24 hours
                if len(self.minute_bars[symbol]) > 1440:
                    self.minute_bars[symbol] = self.minute_bars[symbol][-1440:]

                # Update health monitor
                self.health_monitor.update_metrics('bar_received', {
                    'symbol': symbol,
                    'timestamp': self.Time
                })

        # Event-driven detection (rate-limited)
        if self._ShouldCheckForExtremes():
            try:
                self._ScanForExtremes()
            except Exception as e:
                self.logger.error(f"Detection scan error: {str(e)}", component="Main", exception=e)

        # v2+: Check pending entries for timing
        if self.config.version >= 2:
            self._CheckPendingEntries(data)
            self._ManagePositions(data)

    # ==================== SCHEDULED EVENTS ====================

    def OnMarketOpen(self):
        """Market open tasks"""

        self.logger.info("=== MARKET OPEN ===", component="Main")

        # Reset daily counters
        self.trades_today = 0

        # Update systems
        portfolio_value = self.Portfolio.TotalPortfolioValue

        # v2+: Update advanced systems
        if self.config.version >= 2:
            self.pvs_monitor.ResetDaily()
            self.drawdown_enforcer.Update(portfolio_value)
            self.pvs_monitor.Update(portfolio_value)

            self.logger.info(self.drawdown_enforcer.GetSummary(), component="DrawdownEnforcer")
            self.logger.info(self.pvs_monitor.GetSummary(), component="PVSMonitor")

        self.logger.info(f"Portfolio: ${portfolio_value:,.2f}", component="Main")

    def OnMarketClose(self):
        """Market close tasks"""

        self.logger.info("=== MARKET CLOSE ===", component="Main")

        # Update all systems
        portfolio_value = self.Portfolio.TotalPortfolioValue

        # v2+: Update advanced systems
        if self.config.version >= 2:
            self.drawdown_enforcer.Update(portfolio_value)
            self.pvs_monitor.Update(portfolio_value)
            self.portfolio_constraints.Update()

        # Generate reports
        self._GenerateEndOfDayReport()

        # Send daily summary
        self.alert_manager.send_daily_summary()

        # Health check
        health = self.health_monitor.run_health_check(force=True)

        self.logger.info("Market closed - See you tomorrow!", component="Main")

    def HourlyScan(self):
        """Hourly scan for extremes"""

        if self.IsWarmingUp:
            return

        self.logger.info(f"=== HOURLY SCAN: {self.Time.strftime('%H:%M')} ===", component="Main")

        # Track execution time
        import time
        start_time = time.time()

        # Reset hourly counters
        self.trades_this_hour = 0
        self.detections_this_hour = 0  # Reset detection rate limiter
        self.last_hour = self.Time.hour

        # Update systems
        portfolio_value = self.Portfolio.TotalPortfolioValue

        # Check if HMM needs refitting (scheduled)
        if self.hmm_regime.ShouldRefit(self.Time.date()):
            self.hmm_regime.Fit()

        # v2+: Check advanced systems
        should_halt = False
        if self.config.version >= 2:
            dd_info = self.drawdown_enforcer.Update(portfolio_value)
            pvs_info = self.pvs_monitor.Update(portfolio_value)
            self.portfolio_constraints.Update()

            if dd_info['should_halt']:
                self.logger.critical("TRADING HALTED - Drawdown >40%", component="Main")
                should_halt = True

            if pvs_info['should_halt']:
                self.logger.critical("TRADING HALTED - PVS >9", component="Main")
                should_halt = True

        # Check max trades
        if self.trades_today >= self.config.MAX_TRADES_PER_DAY:
            self.logger.info(f"Max trades reached ({self.trades_today})", component="Main")
            should_halt = True

        if should_halt:
            return

        # Scan for extremes
        detections = self._ScanForExtremes()

        if detections:
            self.logger.info(f"Detected {len(detections)} extremes", component="Main")

            for detection in detections:
                self._ProcessDetection(detection)

        # Health check
        self.health_monitor.run_health_check()

        # Log execution time
        execution_time = time.time() - start_time
        self.health_monitor.update_metrics('execution_time', execution_time)

        self.logger.info(f"Scan complete ({execution_time:.2f}s)", component="Main")

    # ==================== EXTREME DETECTION ====================

    def _ShouldCheckForExtremes(self):
        """
        Rate limit extreme detection to avoid spam

        Returns:
            bool: True if should scan for extremes now
        """
        # Check time elapsed since last scan
        elapsed_minutes = (self.Time - self.last_detection_scan).total_seconds() / 60

        if elapsed_minutes < self.DETECTION_INTERVAL_MINUTES:
            return False

        # Check hourly detection rate limit
        if self.detections_this_hour >= self.MAX_DETECTIONS_PER_HOUR:
            return False

        return True

    def _ScanForExtremes(self):
        """Scan all symbols for extremes (event-driven with rate limits)"""

        # Update last scan time
        self.last_detection_scan = self.Time

        detections = []

        for symbol in self.active_symbols:
            if symbol not in self.minute_bars:
                continue

            bars = self.minute_bars[symbol]

            if len(bars) < self.config.LOOKBACK_MINUTES:
                continue

            # Check for continuation extreme
            extreme = self.extreme_detector.Detect(symbol, bars)

            if extreme and extreme['is_extreme']:
                extreme['symbol'] = symbol
                extreme['type'] = 'continuation'
                extreme['detection_time'] = self.Time
                detections.append(extreme)

                self.health_monitor.update_metrics('detection', None)

            # v2+: Check for exhaustion
            if self.config.version >= 2 and self.config.ENABLE_EXHAUSTION:
                exhaustion = self.exhaustion_detector.Detect(symbol, bars)

                if exhaustion and exhaustion['is_exhaustion']:
                    exhaustion['symbol'] = symbol
                    exhaustion['type'] = 'exhaustion'
                    exhaustion['detection_time'] = self.Time
                    detections.append(exhaustion)

                    self.health_monitor.update_metrics('detection', None)

        return detections

    def _ProcessDetection(self, detection):
        """Process a detected extreme"""

        symbol = detection['symbol']

        # Increment detection counter for rate limiting
        self.detections_this_hour += 1

        self.logger.info(
            f"Extreme: {symbol} | Type: {detection['type']} | Z: {detection.get('z_score', 0):.2f} "
            f"({self.detections_this_hour}/{self.MAX_DETECTIONS_PER_HOUR} this hour)",
            component="ExtremeDetector"
        )

        # Get regime
        regime = self.hmm_regime.GetCurrentRegime()
        gpm = regime.get('gpm', 0.5)

        # v2+: Check cascade risk
        if self.config.version >= 2 and self.config.ENABLE_CASCADE_PREVENTION:
            can_trade, violations = self._CheckCascadeRisk(detection)

            if not can_trade:
                self.logger.warning(
                    f"Trade blocked - Cascade risk: {violations}",
                    component="CascadePrevention"
                )
                return

        # Calculate position size
        size = self._CalculatePositionSize(detection, gpm)

        if size < self.config.RISK_PER_TRADE * 0.5:
            self.logger.info("Position size too small - skipping", component="Main")
            return

        # v2+: Check portfolio constraints
        if self.config.version >= 2 and symbol in self.Securities:
            price = self.Securities[symbol].Price
            can_trade, reason = self.portfolio_constraints.CheckConstraints(symbol, size, price)

            if not can_trade:
                self.logger.warning(f"Trade blocked - {reason}", component="PortfolioConstraints")
                return

        # v2+: Add to pending entries (for timing)
        if self.config.version >= 2 and self.config.ENABLE_ENTRY_TIMING:
            self.pending_entries[symbol] = {
                'detection': detection,
                'size': size,
                'gpm': gpm,
                'timestamp': self.Time
            }

            self.logger.info(f"Added to pending entries - waiting for timing", component="Main")
        else:
            # Phase 1 or immediate entry
            self._EnterPosition(symbol, detection, size, gpm)

    def _CheckCascadeRisk(self, detection):
        """Check cascade prevention (v2+ only)"""

        pvs_score = self.pvs_monitor.GetPVS()
        consecutive_losses = self.pvs_monitor.consecutive_losses
        regime = self.hmm_regime.GetCurrentRegime()
        regime_confidence = regime.get('confidence', 0.5)
        trades_last_hour = self.trades_this_hour
        rule_violations = self.pvs_monitor.rule_violations_today

        return self.cascade_prevention.CheckCascadeRisk(
            detection,
            pvs_score,
            consecutive_losses,
            regime_confidence,
            trades_last_hour,
            rule_violations
        )

    def _CalculatePositionSize(self, detection, gpm):
        """Calculate position size with all multipliers (ATR-based for v2+)"""

        # Get symbol and z-score
        symbol = detection.get('symbol')
        z_score = abs(detection.get('z_score', 2.0))

        # v2+: Use advanced ATR-based sizing
        if self.config.version >= 2 and self.config.ENABLE_DYNAMIC_SIZING:
            dd_mult = self.drawdown_enforcer.GetSizeMultiplier()
            pvs_mult = self.pvs_monitor.GetSizeMultiplier()
            # NEW: Pass symbol for ATR-based sizing
            size = self.dynamic_sizer.CalculateSize(symbol, z_score, gpm, dd_mult, pvs_mult, use_atr=True)

            self.logger.info(
                f"Position size (ATR-based): ${size:.2f} (Z={z_score:.2f}, GPM={gpm:.2f})",
                component="DynamicSizer"
            )
        else:
            # v1: Fixed dollar size
            size = self.config.RISK_PER_TRADE

            self.logger.info(
                f"Position size (fixed): ${size:.2f} (Z={z_score:.2f})",
                component="Main"
            )

        return size

    # ==================== ENTRY/EXIT ====================

    def _CheckPendingEntries(self, data):
        """Check pending entries for timing (v2+ only)"""

        if self.config.version < 2 or not self.config.ENABLE_ENTRY_TIMING:
            return

        to_remove = []

        for symbol, entry_info in self.pending_entries.items():
            if symbol not in data or not data[symbol]:
                continue

            current_price = data[symbol].Close
            detection = entry_info['detection']

            # Get A-VWAP if available
            avwap_price = self.avwap_tracker.GetAVWAP(symbol)

            # Check timing
            can_enter, reason = self.entry_timing.CheckEntryTiming(
                detection,
                current_price,
                avwap_price
            )

            if can_enter:
                self.logger.info(f"Entry timing OK - {reason}", component="EntryTiming")

                # Enter position
                self._EnterPosition(
                    symbol,
                    detection,
                    entry_info['size'],
                    entry_info['gpm']
                )

                to_remove.append(symbol)

            # Timeout after 1 hour
            minutes_pending = (self.Time - entry_info['timestamp']).total_seconds() / 60
            if minutes_pending > 60:
                self.logger.info(f"Entry timeout - waited {minutes_pending:.0f} min", component="Main")
                to_remove.append(symbol)

        # Remove processed entries
        for symbol in to_remove:
            del self.pending_entries[symbol]

    # ==================== EXECUTION GUARDS (SAFETY) ====================

    def _GetCurrentSpread(self, symbol):
        """
        Get current bid-ask spread in basis points

        Returns:
            float: Spread in basis points, or inf if unable to calculate
        """
        try:
            if symbol not in self.Securities:
                return float('inf')

            bid = self.Securities[symbol].BidPrice
            ask = self.Securities[symbol].AskPrice

            if bid <= 0 or ask <= 0:
                return float('inf')

            mid = (bid + ask) / 2
            if mid <= 0:
                return float('inf')

            spread_bps = ((ask - bid) / mid) * 10000
            return spread_bps

        except Exception as e:
            self.logger.error(f"Error calculating spread for {symbol}: {str(e)}",
                            component="ExecutionGuard")
            return float('inf')  # Conservative: assume infinite spread on error

    def _IsInCooldown(self, symbol):
        """
        Check if symbol is in cooldown period after recent exit

        Returns:
            bool: True if symbol should not be traded yet
        """
        if symbol not in self.symbol_cooldowns:
            return False

        exit_time = self.symbol_cooldowns[symbol]
        elapsed_minutes = (self.Time - exit_time).total_seconds() / 60

        return elapsed_minutes < self.COOLDOWN_MINUTES

    def _GetDrawdownMultiplier(self):
        """
        Get current drawdown multiplier (v2+ only)

        Returns:
            float: Multiplier (0.0 = halt, 1.0 = full size)
        """
        if self.config.version < 2 or not self.config.ENFORCE_DRAWDOWN_LADDER:
            return 1.0

        try:
            return self.drawdown_enforcer.GetCurrentMultiplier()
        except:
            return 1.0  # Conservative: allow trading if check fails

    def _CheckExecutionGuards(self, symbol, direction, size):
        """
        Final safety check before order execution

        This is the last line of defense - checks all limits and guards
        before any real trade is executed.

        Args:
            symbol: Trading symbol
            direction: 'up' or 'down'
            size: Position size in dollars

        Returns:
            tuple: (allowed: bool, reason: str)
        """

        # Guard 1: Daily trade limit
        if self.trades_today >= self.config.MAX_TRADES_PER_DAY:
            return False, f"Daily trade limit reached ({self.trades_today}/{self.config.MAX_TRADES_PER_DAY})"

        # Guard 2: Drawdown ladder (v2+)
        dd_mult = self._GetDrawdownMultiplier()
        if dd_mult == 0:
            return False, "Drawdown ladder halted trading (4th rung)"

        # Guard 3: PVS halt level (v2+)
        if self.config.version >= 2 and self.config.ENABLE_PVS:
            try:
                pvs = self.pvs_monitor.GetCurrentPVS()
                if pvs >= self.config.PVS_HALT_LEVEL:
                    return False, f"PVS at halt level: {pvs} >= {self.config.PVS_HALT_LEVEL}"
            except Exception as e:
                self.logger.error(f"PVS check failed: {str(e)}", component="ExecutionGuard")
                # Don't halt on check failure, but log it

        # Guard 4: Spread quality check
        spread_bps = self._GetCurrentSpread(symbol)
        if spread_bps > self.config.MAX_SPREAD_BPS:
            return False, f"Spread too wide: {spread_bps:.1f} bps > {self.config.MAX_SPREAD_BPS} bps"

        # Guard 5: Position limit
        if len(self.Portfolio) >= self.config.MAX_POSITIONS:
            return False, f"Max positions reached ({len(self.Portfolio)}/{self.config.MAX_POSITIONS})"

        # Guard 6: Symbol cooldown (prevent rapid re-entry)
        if self._IsInCooldown(symbol):
            elapsed = (self.Time - self.symbol_cooldowns[symbol]).total_seconds() / 60
            remaining = self.COOLDOWN_MINUTES - elapsed
            return False, f"Symbol in cooldown: {remaining:.0f} min remaining"

        # Guard 7: Position size validation
        if size < self.config.RISK_PER_TRADE * 0.5:
            return False, f"Position too small: ${size:.2f} < ${self.config.RISK_PER_TRADE * 0.5:.2f}"

        # All guards passed
        return True, "OK"

    # ==================== POSITION MANAGEMENT ====================

    def _EnterPosition(self, symbol, detection, size, gpm):
        """Enter a position"""

        if symbol not in self.Securities:
            self.logger.error(f"Symbol not in securities: {symbol}", component="Main")
            return

        price = self.Securities[symbol].Price

        if price == 0:
            self.logger.error(f"Invalid price for {symbol}", component="Main")
            return

        # Calculate shares
        shares = int(size / price)

        if shares == 0:
            self.logger.info(f"Position too small: ${size} / ${price:.2f}", component="Main")
            return

        # Determine direction
        direction = detection.get('direction', 'up')

        if direction == 'down':
            shares = -shares

        # Check if observation mode
        if self.config.OBSERVATION_MODE:
            self.logger.info(
                f"[OBS] OBSERVATION MODE - Would enter: {shares:+d} {symbol} @ ${price:.2f}",
                component="Main"
            )
            return

        # CRITICAL: Final execution guards (last line of defense)
        allowed, reason = self._CheckExecutionGuards(symbol, direction, size)
        if not allowed:
            self.logger.warning(
                f"[BLOCKED] TRADE BLOCKED: {symbol} - {reason}",
                component="ExecutionGuard"
            )
            return

        # Execute order (v2+ only)
        try:
            ticket = self.MarketOrder(symbol, shares)

            if ticket.Status == OrderStatus.Filled or ticket.Status == OrderStatus.PartiallyFilled:
                fill_price = ticket.AverageFillPrice

                self.logger.info(
                    f"[ENTRY] {shares:+d} {symbol} @ ${fill_price:.2f} (${size:.2f})",
                    component="Trade"
                )

                # Record for backtest analysis
                self.backtest_analyzer.record_trade(
                    'open', symbol, shares, fill_price,
                    regime=self.hmm_regime.GetCurrentRegime().get('regime'),
                    direction=direction,
                    timestamp=self.Time,
                    metadata={'detection': detection, 'gpm': gpm}
                )

                # Track position
                self.active_positions[symbol] = {
                    'entry_price': fill_price,
                    'shares': shares,
                    'entry_time': self.Time,
                    'detection': detection,
                    'target': detection.get('target_price'),
                    'stop': detection.get('stop_price')
                }

                # Update counters
                self.trades_today += 1
                self.trades_this_hour += 1

                # Send alert
                self.alert_manager.alert_trade_executed(
                    'entry', symbol, shares, fill_price, detection['type']
                )

            else:
                self.logger.error(f"Order not filled: {ticket.Status}", component="Trade")

        except Exception as e:
            self.logger.error(f"Entry error: {str(e)}", component="Trade", exception=e)

    def _ManagePositions(self, data):
        """Manage active positions (v2+ only)"""

        if self.config.version < 2:
            return

        to_exit = []

        for symbol, position in self.active_positions.items():
            if symbol not in data or not data[symbol]:
                continue

            current_price = data[symbol].Close
            entry_price = position['entry_price']
            shares = position['shares']

            # Calculate P&L
            if shares > 0:
                pnl_pct = (current_price - entry_price) / entry_price
            else:
                pnl_pct = (entry_price - current_price) / entry_price

            # Check exit conditions
            should_exit = False
            exit_reason = ""

            # 1. Target hit
            target = position.get('target')
            if target:
                if (shares > 0 and current_price >= target) or \
                   (shares < 0 and current_price <= target):
                    should_exit = True
                    exit_reason = "Target hit"

            # 2. Stop hit
            stop = position.get('stop')
            if stop:
                if (shares > 0 and current_price <= stop) or \
                   (shares < 0 and current_price >= stop):
                    should_exit = True
                    exit_reason = "Stop hit"

            # 3. Time stop (5 hours)
            hours_held = (self.Time - position['entry_time']).total_seconds() / 3600
            if hours_held >= 5:
                should_exit = True
                exit_reason = "Time stop (5 hours)"

            # 4. End of day
            if self.Time.hour >= 15 and self.Time.minute >= 45:
                should_exit = True
                exit_reason = "End of day"

            if should_exit:
                to_exit.append((symbol, exit_reason))

        # Execute exits
        for symbol, reason in to_exit:
            self._ExitPosition(symbol, reason)

    def _ExitPosition(self, symbol, reason):
        """Exit a position"""

        if symbol not in self.active_positions:
            return

        position = self.active_positions[symbol]
        shares = position['shares']
        entry_price = position['entry_price']

        if symbol not in self.Securities:
            return

        current_price = self.Securities[symbol].Price

        # Calculate P&L
        if shares > 0:
            pnl = (current_price - entry_price) * shares
        else:
            pnl = (entry_price - current_price) * abs(shares)

        pnl_pct = pnl / (entry_price * abs(shares))

        # Check if observation mode
        if self.config.OBSERVATION_MODE:
            self.logger.info(
                f"[OBS] OBSERVATION MODE - Would exit: {-shares:+d} {symbol} @ ${current_price:.2f} | "
                f"P&L: ${pnl:+.2f} ({pnl_pct:+.2%}) | Reason: {reason}",
                component="Main"
            )
            del self.active_positions[symbol]
            return

        # Execute order (v2+ only)
        try:
            ticket = self.MarketOrder(symbol, -shares)

            if ticket.Status == OrderStatus.Filled or ticket.Status == OrderStatus.PartiallyFilled:
                exit_price = ticket.AverageFillPrice

                # Recalculate actual P&L
                if shares > 0:
                    actual_pnl = (exit_price - entry_price) * shares
                else:
                    actual_pnl = (entry_price - exit_price) * abs(shares)

                actual_pnl_pct = actual_pnl / (entry_price * abs(shares))

                self.logger.info(
                    f"[EXIT] {-shares:+d} {symbol} @ ${exit_price:.2f} | "
                    f"P&L: ${actual_pnl:+.2f} ({actual_pnl_pct:+.2%}) | {reason}",
                    component="Trade"
                )

                # Record for backtest analysis
                self.backtest_analyzer.record_trade(
                    'close', symbol, abs(shares), entry_price, exit_price,
                    timestamp=self.Time,
                    metadata={'reason': reason}
                )

                # v2+: Update PVS
                if self.config.version >= 2:
                    was_winner = actual_pnl > 0
                    self.pvs_monitor.RecordTrade(symbol, actual_pnl, was_winner, self.Time)

                # Send alert
                self.alert_manager.alert_trade_executed(
                    'exit', symbol, shares, exit_price, reason
                )

                # Remove from active
                del self.active_positions[symbol]

                # Track exit time for cooldown period
                self.symbol_cooldowns[symbol] = self.Time
                self.logger.info(
                    f"Cooldown started for {symbol}: {self.COOLDOWN_MINUTES} min",
                    component="ExecutionGuard"
                )

            else:
                self.logger.error(f"Exit order not filled: {ticket.Status}", component="Trade")

        except Exception as e:
            self.logger.error(f"Exit error: {str(e)}", component="Trade", exception=e)

    # ==================== REPORTING ====================

    def _GenerateEndOfDayReport(self):
        """Generate end of day report"""

        portfolio_value = self.Portfolio.TotalPortfolioValue

        self.logger.info("="*70, component="Report")
        self.logger.info("END OF DAY REPORT", component="Report")
        self.logger.info("="*70, component="Report")

        self.logger.info(f"Portfolio Value: ${portfolio_value:,.2f}", component="Report")
        self.logger.info(f"Trades Today: {self.trades_today}", component="Report")
        self.logger.info(f"Active Positions: {len(self.active_positions)}", component="Report")

        # v2+: Advanced reporting
        if self.config.version >= 2:
            dd_info = self.drawdown_enforcer.GetDrawdownInfo()
            pvs_info = self.pvs_monitor.GetPVSInfo()
            health = self.health_monitor.get_health_summary()

            self.logger.info("", component="Report")
            self.logger.info("DRAWDOWN STATUS:", component="Report")
            self.logger.info(f"  Current DD: {dd_info['current_dd_pct']:.2f}%", component="Report")
            self.logger.info(f"  Rung: {dd_info['current_rung']}/4", component="Report")
            self.logger.info(f"  Size Mult: {dd_info['current_multiplier']:.2f}x", component="Report")

            self.logger.info("", component="Report")
            self.logger.info("PVS STATUS:", component="Report")
            self.logger.info(f"  Score: {pvs_info['pvs']:.1f}/10 ({pvs_info['pvs_level']})", component="Report")
            self.logger.info(f"  Fear: {pvs_info['components']['fear']:.1f}", component="Report")
            self.logger.info(f"  Fatigue: {pvs_info['components']['fatigue']:.1f}", component="Report")
            self.logger.info(f"  Confidence: {pvs_info['components']['confidence']:.1f}", component="Report")

            self.logger.info("", component="Report")
            self.logger.info("SYSTEM HEALTH:", component="Report")
            self.logger.info(f"  Status: {'[HEALTHY]' if health['overall_healthy'] else '[ISSUES]'}", component="Report")
            self.logger.info(f"  Checks Passed: {health['checks_passed']}/{health['checks_total']}", component="Report")

        if self.trades_today > 0:
            # Generate backtest report
            metrics = self.backtest_analyzer.calculate_metrics()

            if metrics:
                self.logger.info("", component="Report")
                self.logger.info("PERFORMANCE:", component="Report")
                self.logger.info(f"  Win Rate: {metrics['win_rate']:.2%}", component="Report")
                self.logger.info(f"  Avg Return: ${metrics['avg_return_per_trade']:,.2f}", component="Report")
                self.logger.info(f"  Total Costs: ${metrics['total_costs']:,.2f}", component="Report")

        self.logger.info("="*70, component="Report")

    def OnEndOfAlgorithm(self):
        """End of algorithm - final reports"""

        self.logger.info("="*70, component="Main")
        self.logger.info("ALGORITHM COMPLETE", component="Main")
        self.logger.info("="*70, component="Main")

        # Generate final backtest report
        report = self.backtest_analyzer.generate_report()
        self.Log(report)

        # Log final stats
        final_value = self.Portfolio.TotalPortfolioValue
        total_return = (final_value / self.config.INITIAL_CAPITAL - 1) * 100

        self.logger.info(f"Final Portfolio Value: ${final_value:,.2f}", component="Main")
        self.logger.info(f"Total Return: {total_return:+.2f}%", component="Main")

        # Export trades
        trades_df = self.backtest_analyzer.export_trades_csv()
        if trades_df is not None:
            self.logger.info(f"Total Trades: {len(trades_df)}", component="Main")

        self.logger.info("="*70, component="Main")
