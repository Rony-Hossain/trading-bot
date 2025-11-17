# src/core_strategy.py

from AlgorithmImports import *
from datetime import timedelta
import time

from src.platform.base import IAlgoHost
from engines.quantconnect.host import QCAlgoHost
from config import Config

# Import through your components façade
from src.components import (
    ExtremeDetector,
    ExhaustionDetector,
    UniverseFilter,
    HMMRegime,
    AVWAPTracker,
    SignalPipeline,
    RiskMonitor,
    DrawdownEnforcer,
    PVSMonitor,
    CascadePrevention,
    PortfolioConstraints,
    DynamicSizer,
    EntryTiming,
    TradeEngine,
    AlertManager,
    HealthMonitor,
    StrategyLogger,
    LogRetriever,
    BacktestAnalyzer,
    BacktestLogger,
)


class ExtremeAwareCore:
    """
    Core brain of the strategy.

    QCAlgorithm is just a thin shell (ExtremeAwareAlgorithm in main.py) that:
      - creates Config
      - creates ExtremeAwareCore(self, config)
      - delegates all events (Initialize, OnData, HourlyScan, etc.)

    All real logic lives here or in components/*.
    """

    def __init__(self, algo, config: Config, host: IAlgoHost | None = None) -> None:
        """
        algo: engine-native object (QCAlgorithm, bt.Strategy, etc.)
        host: platform adapter; if None, we build a QC host by default.
        """
        self.algo = algo    
        self.config = config
        self.host = host or QCAlgoHost(algo)

        # We keep most state on the algorithm object so existing components
        # that do self.algorithm.xxx still work unchanged.
        self.logger: StrategyLogger | None = None
        self.alert_manager: AlertManager | None = None
        self.health_monitor: HealthMonitor | None = None
        self.backtest_analyzer: BacktestAnalyzer | None = None

        # Warmup marker (we’ll mirror this onto algo)
        self.warmup_complete_logged = False

    # -------------------------------------------------------------------------
    # INITIALIZATION
    # -------------------------------------------------------------------------

    def initialize(self) -> None:
        """Set up env, components, data structures, and schedules."""

        a = self.algo
        c = self.config

        # ---- Basic setup (QC-specific for now) ----
        a.SetStartDate(2024, 1, 1)
        a.SetCash(c.INITIAL_CAPITAL)
        a.SetBrokerageModel(
            BrokerageName.InteractiveBrokersBrokerage,
            AccountType.Margin,
        )

        # Expose config on algo so components can read algorithm.config
        a.config = c

        # ---- Logging / infra ----
        self.logger = StrategyLogger(a)
        a.logger = self.logger

        self.log_retrieval = LogRetriever(self.logger)
        a.log_retrieval = self.log_retrieval

        self.alert_manager = AlertManager(a, c)
        a.alert_manager = self.alert_manager

        self.health_monitor = (
            HealthMonitor(a, c)
            if self._takes_config(HealthMonitor)
            else HealthMonitor(a)
        )
        a.health_monitor = self.health_monitor

        self.backtest_analyzer = BacktestAnalyzer(a)
        a.backtest_analyzer = self.backtest_analyzer

        mode_desc = "OBSERVATION" if c.OBSERVATION_MODE else "LIVE TRADING"
        self.logger.info("=" * 70, component="Main")
        self.logger.info(
            f"EXTREME-AWARE STRATEGY - v{c.version} | {mode_desc}",
            component="Main",
        )
        self.logger.info("=" * 70, component="Main")

        # ---- Universe & signals ----
        self.universe_filter = UniverseFilter(a, c)
        a.universe_filter = self.universe_filter

        a.SetUniverseSelection(
            FineFundamentalUniverseSelectionModel(
                self.select_coarse,
                self.select_fine,
            )
        )

        self.extreme_detector = ExtremeDetector(a, c)
        a.extreme_detector = self.extreme_detector

        self.exhaustion_detector = (
            ExhaustionDetector(a, c) if c.version >= 2 and c.ENABLE_EXHAUSTION else None
        )
        if self.exhaustion_detector is not None:
            a.exhaustion_detector = self.exhaustion_detector

        self.hmm_regime = HMMRegime(a, c)
        a.hmm_regime = self.hmm_regime

        self.avwap_tracker = AVWAPTracker(a, c)
        a.avwap_tracker = self.avwap_tracker

        # ---- Risk systems ----
        self.risk_monitor = RiskMonitor(a)
        a.risk_monitor = self.risk_monitor

        self.drawdown_enforcer = DrawdownEnforcer(a) if c.version >= 2 else None
        if self.drawdown_enforcer is not None:
            a.drawdown_enforcer = self.drawdown_enforcer

        self.pvs_monitor = PVSMonitor(a) if c.version >= 2 else None
        if self.pvs_monitor is not None:
            a.pvs_monitor = self.pvs_monitor

        self.cascade_prevention = (
            CascadePrevention(c)
            if c.version >= 2 and c.ENABLE_CASCADE_PREVENTION
            else None
        )
        if self.cascade_prevention is not None:
            a.cascade_prevention = self.cascade_prevention

        self.portfolio_constraints = (
            PortfolioConstraints(a)
            if c.version >= 2 and c.ENFORCE_SECTOR_NEUTRALITY
            else None
        )
        if self.portfolio_constraints is not None:
            a.portfolio_constraints = self.portfolio_constraints

        # ---- Execution systems ----
        self.dynamic_sizer = (
            DynamicSizer(a) if c.version >= 2 and c.ENABLE_DYNAMIC_SIZING else None
        )
        if self.dynamic_sizer is not None:
            a.dynamic_sizer = self.dynamic_sizer

        self.entry_timing = (
            EntryTiming(a, c) if c.version >= 2 and c.ENABLE_ENTRY_TIMING else None
        )
        if self.entry_timing is not None:
            a.entry_timing = self.entry_timing

        # ---- Orchestrators ----
        self.signal_pipeline = SignalPipeline(a)
        a.signal_pipeline = self.signal_pipeline

        from components.execution import TradeEngine
        self.trade_engine = TradeEngine(a)
        a.trade_engine = self.trade_engine

        self.logger.info("Core + orchestrators initialized", component="Main")

        # ---- Data structures ----
        a.active_symbols = []
        a.minute_bars = {}      # symbol -> list of minute bars
        a.pending_entries = {}  # symbol -> entry info
        a.active_positions = {} # symbol -> position info
        a.trades_today = 0
        a.trades_this_hour = 0
        a.last_hour = None
        a.warmup_complete_logged = False

        # ---- Scheduling (via host, platform-agnostic) ----
        self.host.schedule_hourly(self.hourly_scan)
        self.host.schedule_open(self.on_market_open)
        self.host.schedule_close(self.on_market_close)
        self.host.schedule_eod(self.on_end_of_day)

        # ---- Warmup (still QC-specific) ----
        a.SetWarmUp(timedelta(days=30))
        self.logger.info("Initialization complete - entering warmup", component="Main")
        self.alert_manager.send_alert(
            "info",
            f"Strategy initialized - v{c.version} | {mode_desc}",
            component="Main",
        )


    # -------------------------------------------------------------------------
    # UNIVERSE SELECTION
    # -------------------------------------------------------------------------

    def select_coarse(self, coarse):
        """Coarse universe filter."""
        if self.algo.IsWarmingUp:
            return []
        return self.universe_filter.CoarseFilter(coarse)

    def select_fine(self, fine):
        """Fine universe filter."""
        if self.algo.IsWarmingUp:
            return []

        symbols = self.universe_filter.FineFilter(fine)
        self.algo.active_symbols = symbols

        self.logger.info(
            f"Universe selected: {len(symbols)} symbols",
            component="Universe",
        )
        return symbols

    # -------------------------------------------------------------------------
    # ONDATA + INTRADAY
    # -------------------------------------------------------------------------

    def on_data(self, data) -> None:
        a = self.algo

        if a.IsWarmingUp:
            return

        # Log warmup completion once
        if not getattr(a, "warmup_complete_logged", False):
            self.logger.info(
                "WARMUP COMPLETE - Strategy now active",
                component="Main",
            )
            self.alert_manager.send_alert(
                "info",
                "Warmup complete - strategy active",
                component="Main",
            )
            a.warmup_complete_logged = True

        # 1) Run signal pipeline → detections
        detections = self.signal_pipeline.Run(data)

        # 2) Hand detections to TradeEngine
        for detection in detections:
            self.trade_engine.ProcessDetection(detection)

        # 3) Let TradeEngine manage timing + positions
        self.trade_engine.CheckPendingEntries(data)
        self.trade_engine.ManagePositions(data)

        # 4) Maintain bar buffers / health
        self.signal_pipeline.UpdateMinuteBars(data)


    # -------------------------------------------------------------------------
    # HOURLY SCAN
    # -------------------------------------------------------------------------

    def hourly_scan(self) -> None:
        a = self.algo
        c = self.config

        if a.IsWarmingUp:
            # Optional: log warmup progress once per day
            if a.Time.hour == 10 and a.Time.minute == 0:
                self.logger.info(
                    f"WARMUP in progress - {a.Time.date()}",
                    component="Main",
                )
            return

        self.logger.info(
            f"=== HOURLY SCAN: {a.Time.strftime('%H:%M')} ===",
            component="Main",
        )

        start_time = time.time()

        # Reset hourly trade counter on hour change
        current_hour = a.Time.hour
        if a.last_hour is None:
            a.last_hour = current_hour
        elif current_hour != a.last_hour:
            a.trades_this_hour = 0
            a.last_hour = current_hour

        # Update RiskMonitor equity curve (for drawdown tracking)
        self.risk_monitor.UpdateEquityCurve()

        # Hard global halt (drawdown / breakers)
        if self.risk_monitor.ShouldHaltTrading():
            self.logger.warning(
                "RISK HALT ACTIVE: not opening new positions this scan",
                component="RiskMonitor",
            )

        # Max daily trades cap
        if a.trades_today >= c.MAX_TRADES_PER_DAY:
            self.logger.info(
                f"Max trades reached ({a.trades_today}) - skipping scan entries",
                component="Main",
            )
            return

        # Scan for extremes via pipeline (this should also call RiskMonitor.Update internally)
        detections = self.signal_pipeline.ScanForDetections()

        if detections:
            self.logger.info(
                f"Detected {len(detections)} extremes",
                component="Main",
            )
            for detection in detections:
                self.trade_engine.ProcessDetection(detection)

        # Health check
        self.health_monitor.run_health_check()

        # Execution time metric
        execution_time = time.time() - start_time
        self.health_monitor.update_metrics("execution_time", execution_time)
        self.logger.info(
            f"Scan complete ({execution_time:.2f}s)",
            component="Main",
        )

    # -------------------------------------------------------------------------
    # DAILY / LIFECYCLE EVENTS
    # -------------------------------------------------------------------------

    def on_market_open(self) -> None:
        self.logger.info(
            f"Market open - {self.algo.Time}",
            component="Main",
        )

    def on_market_close(self) -> None:
        self.logger.info(
            f"Market close - {self.algo.Time}",
            component="Main",
        )

    def on_end_of_day(self) -> None:
        """End-of-day summary + alerts."""
        summary = self.risk_monitor.GetDailySummary()
        self.logger.info(
            f"End of day summary: {summary}",
            component="DailySummary",
        )
        self.alert_manager.send_daily_summary()

    def on_end_of_algorithm(self) -> None:
        """Final backtest/live report."""
        a = self.algo
        c = self.config

        self.logger.info("=" * 70, component="Main")
        self.logger.info(
            "Algorithm finished - generating final report", component="Main"
        )
        self.logger.info("=" * 70, component="Main")

        # Final report from analyzer
        report = self.backtest_analyzer.generate_report()
        a.Log(report)

        final_value = a.Portfolio.TotalPortfolioValue
        total_return = ((final_value / c.INITIAL_CAPITAL) - 1.0) * 100.0

        self.logger.info(
            f"Final Portfolio Value: ${final_value:,.2f}",
            component="Main",
        )
        self.logger.info(
            f"Total Return: {total_return:+.2f}%",
            component="Main",
        )

        trades_df = self.backtest_analyzer.export_trades_csv()
        if trades_df is not None:
            self.logger.info(
                f"Total Trades: {len(trades_df)}",
                component="Main",
            )

        self.logger.info("=" * 70, component="Main")

    # -------------------------------------------------------------------------
    # SMALL HELPER
    # -------------------------------------------------------------------------

    @staticmethod
    def _takes_config(cls) -> bool:
        """
        Dumb helper to avoid guessing constructor signatures too hard.
        If your HealthMonitor signature is known, you can scrap this and
        just call HealthMonitor(algo, config) or HealthMonitor(algo).
        """
        # This is just a placeholder – adjust manually if needed.
        return False
