# region imports
from AlgorithmImports import *
from universe_filter import UniverseFilter
from extreme_detector import ExtremeDetector
from hmm_regime import HMMRegime
from avwap_tracker import AVWAPTracker
from risk_monitor import RiskMonitor
from logger import StrategyLogger
from config import Config
# endregion

class ExtremeAwareStrategy(QCAlgorithm):
    """
    Phase 1 Implementation - Observation Mode
    - Detect extremes (|Z₆₀| ≥ 2 + volume anomaly)
    - Track HMM regime posteriors
    - Calculate A-VWAP from impulse bars
    - Monitor only - NO REAL TRADES
    - Log all signals for confidence building
    """
    
    def Initialize(self):
        # Capital and timeframe
        self.SetStartDate(2024, 1, 1)
        self.SetEndDate(2024, 11, 6)
        self.SetCash(1000)
        
        # Set broker to Interactive Brokers
        self.SetBrokerageModel(BrokerageName.InteractiveBrokersBrokerage, AccountType.Margin)
        
        # Load configuration
        self.config = Config()
        
        # Initialize logger FIRST (so other components can use it)
        self.logger = StrategyLogger(self)
        self.logger.info("="*60)
        self.logger.info("EXTREME-AWARE TRADING STRATEGY - PHASE 1")
        self.logger.info("="*60)
        
        # Initialize components (pass logger to them)
        self.universe_filter = UniverseFilter(self)
        self.extreme_detector = ExtremeDetector(self)
        self.hmm_regime = HMMRegime(self)
        self.avwap_tracker = AVWAPTracker(self)
        self.risk_monitor = RiskMonitor(self)
        
        # Data structures
        self.active_symbols = set()
        self.minute_bars = {}  # symbol -> list of bars
        self.hourly_stats = {}  # symbol -> stats dict
        self.inplay_candidates = {}  # symbol -> detection info
        
        # Phase 1 flags
        self.OBSERVATION_MODE = True  # Set False when ready to trade
        self.MAX_CONCURRENT_POSITIONS = 1  # Phase 1: only 1 position
        self.RISK_PER_TRADE = 5  # $5 risk per trade in Phase 1
        
        # Universe selection - coarse + fine
        self.UniverseSettings.Resolution = Resolution.Minute
        self.AddUniverse(self.CoarseSelectionFilter, self.FineSelectionFilter)
        
        # Schedule functions
        self.Schedule.On(
            self.DateRules.EveryDay(),
            self.TimeRules.AfterMarketOpen("SPY", 5),
            self.OnMarketOpen
        )
        
        self.Schedule.On(
            self.DateRules.EveryDay(),
            self.TimeRules.Every(timedelta(minutes=60)),
            self.OnHourly
        )
        
        self.Schedule.On(
            self.DateRules.EveryDay(),
            self.TimeRules.BeforeMarketClose("SPY", 5),
            self.OnMarketClose
        )
        
        # Warm up period
        self.SetWarmUp(timedelta(days=60))
        
        # Log initialization complete
        self.logger.info(f"Phase 1 Observation Mode - Initialized", component="Main")
        self.logger.info(f"Capital: ${self.Portfolio.Cash:,.2f}", component="Main")
        self.logger.info(f"Observation Mode: {self.OBSERVATION_MODE}", component="Main")
        self.logger.info(f"Max Positions: {self.MAX_CONCURRENT_POSITIONS}", component="Main")
        self.logger.info(f"Risk/Trade: ${self.RISK_PER_TRADE}", component="Main")
        
        # Log initial performance snapshot
        self.logger.log_performance_snapshot()
    
    def CoarseSelectionFilter(self, coarse):
        """First pass: basic liquidity and price filters"""
        return self.universe_filter.CoarseFilter(coarse)
    
    def FineSelectionFilter(self, fine):
        """Second pass: detailed quality filters"""
        return self.universe_filter.FineFilter(fine)
    
    def OnData(self, data):
        """Process minute bars"""
        if self.IsWarmingUp:
            return
        
        # Update minute bars for active symbols
        for symbol in self.active_symbols:
            if symbol in data and data[symbol] is not None:
                if symbol not in self.minute_bars:
                    self.minute_bars[symbol] = []
                
                bar = data[symbol]
                self.minute_bars[symbol].append({
                    'time': bar.Time,
                    'open': bar.Open,
                    'high': bar.High,
                    'low': bar.Low,
                    'close': bar.Close,
                    'volume': bar.Volume
                })
                
                # Keep only last 24 hours (1440 minutes)
                if len(self.minute_bars[symbol]) > 1440:
                    self.minute_bars[symbol] = self.minute_bars[symbol][-1440:]
    
    def OnHourly(self):
        """Main hourly processing - detect extremes and update regime"""
        if self.IsWarmingUp:
            return
        
        self.logger.info(f"{'='*60}")
        self.logger.info(f"Hourly Check: {self.Time}", component="Main")
        self.logger.info(f"{'='*60}")
        
        # Update HMM regime (observation only)
        regime_state = self.hmm_regime.Update(self.Time)
        self.logger.info(f"HMM Regime: {regime_state}", component="Main")
        
        # Log performance snapshot
        perf = self.logger.log_performance_snapshot()
        
        # Scan for extremes
        candidates = []
        for symbol in self.active_symbols:
            if symbol in self.minute_bars and len(self.minute_bars[symbol]) >= 60:
                # Detect extreme
                extreme_info = self.extreme_detector.Detect(
                    symbol, 
                    self.minute_bars[symbol]
                )
                
                if extreme_info['is_extreme']:
                    candidates.append((symbol, extreme_info))
                    
                    # Use specialized extreme logging
                    self.logger.log_extreme_detection(symbol, extreme_info)
                    
                    # Update A-VWAP tracker
                    self.avwap_tracker.AddImpulse(symbol, extreme_info)
        
        # Update A-VWAP for tracked symbols
        avwap_updates = self.avwap_tracker.UpdateAll(self.minute_bars)
        
        # Log A-VWAP distances
        for symbol, avwap_data in avwap_updates.items():
            if avwap_data['is_active']:
                self.logger.log_avwap_track(symbol, avwap_data)
        
        # Phase 1: Log what we would trade
        if candidates and self.OBSERVATION_MODE:
            self.logger.info(f"OBSERVATION MODE - Would consider {len(candidates)} candidates", 
                           component="Main")
            for symbol, info in candidates[:3]:  # Top 3
                self.logger.debug(f"  {symbol}: Z={info['z_score']:.2f}, VolAnom={info['vol_anomaly']:.2f}x",
                                component="Main")
        
        # Risk monitoring
        self.risk_monitor.Update(self.Time, regime_state, candidates)
    
    def OnMarketOpen(self):
        """Start of day initialization"""
        self.Log(f"\n🔔 Market Open: {self.Time.date()}")
        self.Log(f"Active Universe Size: {len(self.active_symbols)}")
        
        # Reset intraday tracking
        self.inplay_candidates.clear()
    
    def OnMarketClose(self):
        """End of day summary"""
        self.logger.info(f"{'='*60}", component="Main")
        self.logger.info(f"Market Close: {self.Time.date()}", component="Main")
        self.logger.info(f"{'='*60}", component="Main")
        
        # Daily summary
        summary = self.risk_monitor.GetDailySummary()
        
        self.logger.info(f"Daily Summary:", component="Main")
        self.logger.info(f"  Extremes Detected: {summary['extremes_detected']}", component="Main")
        self.logger.info(f"  HMM Regime: {summary['dominant_regime']}", component="Main")
        self.logger.info(f"  Active A-VWAP Tracks: {summary['active_avwap_tracks']}", component="Main")
        
        if self.OBSERVATION_MODE:
            self.logger.info(f"  💡 OBSERVATION MODE - No trades executed", component="Main")
        
        # Log performance snapshot
        self.logger.log_performance_snapshot()
        
        # Get log summary
        log_summary = self.logger.get_daily_summary()
        self.logger.info(f"Log Summary: {log_summary['total_logs']} logs, "
                        f"{log_summary['total_errors']} errors, "
                        f"{log_summary['total_detections']} detections",
                        component="Logger")
        
        # Print specialized summaries
        if log_summary['total_detections'] > 0:
            detection_summary = self.logger.get_detection_summary()
            self.Log(detection_summary)
        
        if log_summary['total_errors'] > 0:
            error_report = self.logger.get_error_report()
            self.logger.warning("Errors occurred today - see report", component="Main")
            self.Log(error_report)
        
        # Export logs to ObjectStore (for later analysis)
        try:
            self.logger.export_logs_json('all')
            self.logger.info("Daily logs exported to ObjectStore", component="Main")
        except Exception as e:
            self.logger.error(f"Failed to export logs: {str(e)}", 
                            component="Main", exception=e)
        
        self.logger.info(f"{'='*60}", component="Main")
    
    def OnSecuritiesChanged(self, changes):
        """Handle universe changes"""
        # Add new securities
        for security in changes.AddedSecurities:
            self.active_symbols.add(security.Symbol)
            
            # Set up minute resolution if not already
            if not security.HasData:
                self.Log(f"Added to universe: {security.Symbol}")
        
        # Remove securities
        for security in changes.RemovedSecurities:
            symbol = security.Symbol
            if symbol in self.active_symbols:
                self.active_symbols.remove(symbol)
            
            # Clean up tracking data
            if symbol in self.minute_bars:
                del self.minute_bars[symbol]
            if symbol in self.hourly_stats:
                del self.hourly_stats[symbol]
            
            self.Log(f"Removed from universe: {symbol}")
    
    def OnOrderEvent(self, orderEvent):
        """Handle order fills (for when we go live)"""
        if orderEvent.Status == OrderStatus.Filled:
            order = self.Transactions.GetOrderById(orderEvent.OrderId)
            self.logger.info(f"Order Filled: {order.Symbol} {order.Quantity} @ {orderEvent.FillPrice}",
                           component="OrderExecution")
    
    def OnEndOfAlgorithm(self):
        """
        Called at end of backtest or when live trading stops
        Log comprehensive results
        """
        
        self.logger.info("="*60, component="EndOfAlgorithm")
        self.logger.info("ALGORITHM COMPLETE", component="EndOfAlgorithm")
        self.logger.info("="*60, component="EndOfAlgorithm")
        
        # Portfolio Statistics
        portfolio_stats = {
            'start_date': str(self.StartDate),
            'end_date': str(self.EndDate),
            'initial_capital': self.config.INITIAL_CAPITAL,
            'final_portfolio_value': self.Portfolio.TotalPortfolioValue,
            'cash': self.Portfolio.Cash,
            'total_profit': self.Portfolio.TotalPortfolioValue - self.config.INITIAL_CAPITAL,
            'total_return_pct': ((self.Portfolio.TotalPortfolioValue / self.config.INITIAL_CAPITAL) - 1) * 100,
            'total_fees': self.Portfolio.TotalFees,
            'total_unrealized_profit': self.Portfolio.TotalUnrealizedProfit
        }
        
        self.logger.info("Portfolio Summary:", component="EndOfAlgorithm")
        self.logger.info(f"  Period: {portfolio_stats['start_date']} to {portfolio_stats['end_date']}", 
                        component="EndOfAlgorithm")
        self.logger.info(f"  Initial Capital: ${portfolio_stats['initial_capital']:,.2f}", 
                        component="EndOfAlgorithm")
        self.logger.info(f"  Final Value: ${portfolio_stats['final_portfolio_value']:,.2f}", 
                        component="EndOfAlgorithm")
        self.logger.info(f"  Total P&L: ${portfolio_stats['total_profit']:,.2f}", 
                        component="EndOfAlgorithm")
        self.logger.info(f"  Total Return: {portfolio_stats['total_return_pct']:+.2f}%", 
                        component="EndOfAlgorithm")
        self.logger.info(f"  Total Fees: ${portfolio_stats['total_fees']:,.2f}", 
                        component="EndOfAlgorithm")
        
        # Detection Statistics
        detection_summary = self.logger.get_detection_summary()
        self.Log(detection_summary)
        
        # Trade Statistics (when trading enabled)
        if not self.OBSERVATION_MODE:
            trade_summary = self.logger.get_trade_summary()
            self.Log(trade_summary)
        
        # Error Summary (if any)
        log_summary = self.logger.get_daily_summary()
        if log_summary['total_errors'] > 0:
            error_report = self.logger.get_error_report()
            self.Log(error_report)
        
        # Risk Metrics
        max_dd = self.risk_monitor.CalculateDrawdown()
        self.logger.info(f"Risk Metrics:", component="EndOfAlgorithm")
        self.logger.info(f"  Max Drawdown: {max_dd:.2%}", component="EndOfAlgorithm")
        
        # Compile final results
        final_results = {
            'type': 'algorithm_complete',
            'mode': 'backtest' if not self.LiveMode else 'live',
            'observation_mode': self.OBSERVATION_MODE,
            'portfolio': portfolio_stats,
            'detections': {
                'total': len(self.logger.detection_logs),
                'up': sum(1 for d in self.logger.detection_logs if d['direction'] == 'up'),
                'down': sum(1 for d in self.logger.detection_logs if d['direction'] == 'down')
            },
            'trades': {
                'total': len(self.logger.trade_logs),
                'entries': sum(1 for t in self.logger.trade_logs if t['trade_type'] == 'entry'),
                'exits': sum(1 for t in self.logger.trade_logs if t['trade_type'] == 'exit')
            } if self.logger.trade_logs else {'total': 0},
            'errors': {
                'total': len(self.logger.error_logs),
                'by_component': dict(self.logger.error_counts)
            },
            'max_drawdown': max_dd,
            'session_id': self.logger.session_id
        }
        
        try:
            # Save comprehensive results
            key = f"final_results_{self.logger.session_id}"
            self.ObjectStore.Save(key, json.dumps(final_results, indent=2, default=str))
            self.logger.info(f"Final results saved to ObjectStore: {key}", component="EndOfAlgorithm")
        except Exception as e:
            self.logger.error(f"Failed to save final results: {str(e)}", 
                             component="EndOfAlgorithm", exception=e)
        
        # Export all logs
        try:
            self.logger.export_logs_json('all')
            self.logger.info("All logs exported successfully", component="EndOfAlgorithm")
        except Exception as e:
            self.logger.error(f"Failed to export logs: {str(e)}", 
                             component="EndOfAlgorithm", exception=e)
        
        self.logger.info("="*60, component="EndOfAlgorithm")
        self.logger.info(f"Session {self.logger.session_id} complete", component="EndOfAlgorithm")
