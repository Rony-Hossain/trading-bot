# src/components/execution/trade_engine.py
from AlgorithmImports import *


class TradeEngine:
    """
    Executes trades given detections, respecting all risk controls.

    This wraps what used to live in main.py:
      - _ProcessDetection
      - _CheckCascadeRisk
      - _CalculatePositionSize
      - _CheckPendingEntries
      - _ManagePositions
      - _EnterPosition
      - _ExitPosition
    """

    def __init__(self, algorithm: QCAlgorithm):
        self.algo = algorithm
        self.config = algorithm.config
        self.logger = algorithm.logger

        # Component references (all set in core.initialize())
        self.risk_monitor = getattr(algorithm, "risk_monitor", None)
        self.pvs_monitor = getattr(algorithm, "pvs_monitor", None)
        self.drawdown_enforcer = getattr(algorithm, "drawdown_enforcer", None)
        self.dynamic_sizer = getattr(algorithm, "dynamic_sizer", None)
        self.entry_timing = getattr(algorithm, "entry_timing", None)
        self.cascade_prevention = getattr(algorithm, "cascade_prevention", None)
        self.portfolio_constraints = getattr(algorithm, "portfolio_constraints", None)
        self.avwap_tracker = getattr(algorithm, "avwap_tracker", None)
        self.alert_manager = getattr(algorithm, "alert_manager", None)
        self.hmm_regime = getattr(algorithm, "hmm_regime", None)
        self.backtest_analyzer = getattr(algorithm, "backtest_analyzer", None)

    # ------------------------------------------------------------------
    # PUBLIC ENTRYPOINTS
    # ------------------------------------------------------------------

    def ProcessDetection(self, detection: dict) -> None:
        """Process a detected extreme/exhaustion."""
        symbol = detection["symbol"]

        self.logger.info(
            f"Extreme: {symbol} | Type: {detection['type']} | "
            f"Z: {detection.get('z_score', 0):.2f}",
            component="ExtremeDetector",
        )

        # Send alert if enabled (with per-symbol flood protection)
        if self.alert_manager is not None:
            self.alert_manager.alert_extreme_detected(symbol, detection)

        # Get regime (for GPM / sizing)
        regime = self.hmm_regime.GetCurrentRegime() if self.hmm_regime else {}
        gpm = regime.get("gpm", 0.5)

        # 1) Global RiskMonitor gate (hard kill)
        if self.risk_monitor and self.risk_monitor.ShouldHaltTrading():
            self.logger.warning(
                f"RISK HALT (RiskMonitor): blocking new trade for {symbol}",
                component="RiskMonitor",
            )
            self.risk_monitor.LogBlockedTrade(symbol, "risk_monitor_halt")
            return

        # 2) Cascade prevention (soft overtrading control)
        if (
            self.config.version >= 2
            and self.config["ENABLE_CASCADE_PREVENTION"]
            and self.cascade_prevention is not None
            and self.pvs_monitor is not None
        ):
            can_trade, violations = self._CheckCascadeRisk(detection)
            if not can_trade:
                self.logger.warning(
                    f"Trade blocked - Cascade risk: {violations}",
                    component="CascadePrevention",
                )
                self.risk_monitor.LogBlockedTrade(symbol, "cascade")
                return

        # 3) Calculate position size
        size = self._CalculatePositionSize(detection, gpm)

        if size < self.config["RISK_PER_TRADE"] * 0.5:
            self.logger.info("Position size too small - skipping", component="Main")
            return

        # 4) Portfolio constraints (v2+)
        if (
            self.config.version >= 2
            and self.portfolio_constraints is not None
            and symbol in self.algo.Securities
        ):
            price = self.algo.Securities[symbol].Price
            can_trade, reason = self.portfolio_constraints.CheckConstraints(
                symbol, size, price
            )
            if not can_trade:
                self.logger.warning(
                    f"Trade blocked - {reason}", component="PortfolioConstraints"
                )
                self.risk_monitor.LogBlockedTrade(symbol, "portfolio")
                return

        # 5) Entry timing (v2+) – put into pending entries
        if self.config.version >= 2 and self.config["ENABLE_ENTRY_TIMING"]:
            self.algo.pending_entries[symbol] = {
                "detection": detection,
                "size": size,
                "gpm": gpm,
                "timestamp": self.algo.Time,
            }
            self.logger.info(
                "Added to pending entries - waiting for timing",
                component="Main",
            )
        else:
            # Phase 1 or immediate entry
            self._EnterPosition(symbol, detection, size, gpm)

    def CheckPendingEntries(self, data) -> None:
        """Check pending entries for timing (v2+ only)."""

        if self.config.version < 2 or not self.config["ENABLE_ENTRY_TIMING"]:
            return

        if self.entry_timing is None:
            return

        to_remove = []

        for symbol, entry_info in list(self.algo.pending_entries.items()):
            if symbol not in data or not data[symbol]:
                continue

            # Global RiskMonitor gate for pending entries
            if self.risk_monitor and self.risk_monitor.ShouldHaltTrading():
                self.logger.warning(
                    f"RISK HALT (RiskMonitor): blocking pending entry for {symbol}",
                    component="RiskMonitor",
                )
                self.risk_monitor.LogBlockedTrade(symbol, "risk_monitor_halt_pending")
                to_remove.append(symbol)
                continue

            current_price = data[symbol].Close
            detection = entry_info["detection"]

            # Get A-VWAP if available
            # avwap_price = None
            # if (
            #     self.avwap_tracker is not None
            #     and symbol in self.avwap_tracker.avwap_values
            # ):
            #     avwap_price = self.avwap_tracker.avwap_values[symbol]
            # Get A-VWAP if available (duck-typed; works with multiple tracker shapes)
            avwap_price = self._get_avwap(symbol)
            # Check timing
            can_enter, reason = self.entry_timing.CheckEntryTiming(
                detection, current_price, avwap_price
            )

            if can_enter:
                self.logger.info(
                    f"Entry timing OK - {reason}",
                    component="EntryTiming",
                )
                self._EnterPosition(
                    symbol,
                    detection,
                    entry_info["size"],
                    entry_info["gpm"],
                )
                to_remove.append(symbol)

            # Timeout after 1 hour
            minutes_pending = (
                self.algo.Time - entry_info["timestamp"]
            ).total_seconds() / 60.0
            if minutes_pending > 60:
                self.logger.info(
                    f"Entry timeout - waited {minutes_pending:.0f} min",
                    component="Main",
                )
                to_remove.append(symbol)

        # Remove processed entries
        for symbol in to_remove:
            self.algo.pending_entries.pop(symbol, None)

    def _get_avwap(self, symbol):
        """
        Best-effort AVWAP lookup for a symbol.

        Supports several possible AVWAPTracker APIs:
          - tracker.avwap_values[symbol]
          - tracker.GetAVWAP(symbol)
          - tracker.GetCurrentAVWAP(symbol)
        Returns None if nothing is available or it errors.
        """
        tracker = self.avwap_tracker
        if tracker is None:
            return None

        # 1) Dict-style attribute: avwap_values
        if hasattr(tracker, "avwap_values"):
            try:
                values = getattr(tracker, "avwap_values") or {}
                # support dict keyed by Symbol or str
                return values.get(symbol) or values.get(str(symbol))
            except Exception:
                pass

        # 2) Method: GetAVWAP(symbol)
        if hasattr(tracker, "GetAVWAP"):
            try:
                return tracker.GetAVWAP(symbol)
            except Exception:
                pass

        # 3) Method: GetCurrentAVWAP(symbol)
        if hasattr(tracker, "GetCurrentAVWAP"):
            try:
                return tracker.GetCurrentAVWAP(symbol)
            except Exception:
                pass

        # Nothing usable
        return None

    def ManagePositions(self, data) -> None:
        """Manage open positions (stops, timeouts, EOD exits)."""

        if self.config.version < 2:
            return

        to_exit = []

        for symbol, position in list(self.algo.active_positions.items()):
            if symbol not in data or not data[symbol]:
                continue

            current_price = data[symbol].Close
            entry_price = position["entry_price"]
            shares = position["shares"]

            # P&L %
            if shares > 0:
                pnl_pct = (current_price - entry_price) / entry_price
            else:
                pnl_pct = (entry_price - current_price) / entry_price

            should_exit = False
            exit_reason = ""

            # 1. Target hit
            target = position.get("target")
            if target:
                if (shares > 0 and current_price >= target) or (
                    shares < 0 and current_price <= target
                ):
                    should_exit = True
                    exit_reason = "Target hit"

            # 2. Stop hit
            stop = position.get("stop")
            if stop:
                if (shares > 0 and current_price <= stop) or (
                    shares < 0 and current_price >= stop
                ):
                    should_exit = True
                    exit_reason = "Stop hit"

            # 3. Time stop (5 hours)
            hours_held = (
                self.algo.Time - position["entry_time"]
            ).total_seconds() / 3600.0
            if hours_held >= 5:
                should_exit = True
                exit_reason = "Time stop (5 hours)"

            # 4. End of day (15:45+)
            if self.algo.Time.hour >= 15 and self.algo.Time.minute >= 45:
                should_exit = True
                exit_reason = "End of day"

            if should_exit:
                to_exit.append((symbol, exit_reason))

        # Execute exits
        for symbol, reason in to_exit:
            self._ExitPosition(symbol, reason)

    # ------------------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------------------

    def _CheckCascadeRisk(self, detection):
        """Check cascade prevention (v2+ only)."""

        pvs_score = self.pvs_monitor.GetPVS()
        consecutive_losses = self.pvs_monitor.consecutive_losses
        regime = self.hmm_regime.GetCurrentRegime() if self.hmm_regime else {}
        regime_confidence = regime.get("confidence", 0.5)
        trades_last_hour = self.algo.trades_this_hour
        rule_violations = self.pvs_monitor.rule_violations_today

        return self.cascade_prevention.CheckCascadeRisk(
            detection,
            pvs_score,
            consecutive_losses,
            regime_confidence,
            trades_last_hour,
            rule_violations,
        )

    def _CalculatePositionSize(self, detection, gpm):
        """Calculate position size with all multipliers."""

        z_score = abs(detection.get("z_score", 2.0))

        if self.config.version >= 2 and self.config["ENABLE_DYNAMIC_SIZING"]:
            dd_mult = (
                self.risk_monitor.GetRiskMultiplier()
                if self.risk_monitor is not None
                else 1.0
            )
            pvs_mult = (
                self.pvs_monitor.GetSizeMultiplier()
                if self.pvs_monitor is not None
                else 1.0
            )
            size = self.dynamic_sizer.CalculateSize(z_score, gpm, dd_mult, pvs_mult)
        else:
            # Phase 1: fixed dollar risk
            size = float(self.config["RISK_PER_TRADE"])

        self.logger.info(
            f"Position size: ${size:.2f} (Z={z_score:.2f}, GPM={gpm:.2f})",
            component="DynamicSizer" if self.config.version >= 2 else "Main",
        )
        return size

    def _EnterPosition(self, symbol, detection, size, gpm):
        """Enter a position."""

        if symbol not in self.algo.Securities:
            self.logger.error(f"Symbol not in securities: {symbol}", component="Main")
            return

        price = self.algo.Securities[symbol].Price
        if price == 0:
            self.logger.error(f"Invalid price for {symbol}", component="Main")
            return

        shares = int(size / price)
        if shares == 0:
            self.logger.info(
                f"Position too small: ${size:.2f} / ${price:.2f}",
                component="Main",
            )
            return

        direction = detection.get("direction", "up")
        if direction == "down":
            shares = -shares

        # Observation mode: log-only
        if self.config.OBSERVATION_MODE:
            self.logger.info(
                f" OBSERVATION MODE - Would enter: {shares:+d} {symbol} @ ${price:.2f}",
                component="Main",
            )
            return

        try:
            ticket = self.algo.MarketOrder(symbol, shares)

            if ticket.Status in (OrderStatus.Filled, OrderStatus.PartiallyFilled):
                fill_price = ticket.AverageFillPrice

                self.logger.info(
                    f"✓ ENTRY: {shares:+d} {symbol} @ ${fill_price:.2f} (${size:.2f})",
                    component="Trade",
                )

                # Backtest record
                if self.backtest_analyzer is not None:
                    self.backtest_analyzer.record_trade(
                        "open",
                        symbol,
                        shares,
                        fill_price,
                        regime=(
                            self.hmm_regime.GetCurrentRegime().get("regime")
                            if self.hmm_regime
                            else None
                        ),
                        direction=direction,
                        timestamp=self.algo.Time,
                        metadata={"detection": detection, "gpm": gpm},
                    )

                # Track position
                self.algo.active_positions[symbol] = {
                    "entry_price": fill_price,
                    "shares": shares,
                    "entry_time": self.algo.Time,
                    "detection": detection,
                    "target": detection.get("target_price"),
                    "stop": detection.get("stop_price"),
                }

                # Counters
                self.algo.trades_today += 1
                self.algo.trades_this_hour += 1

                # Alerts
                if self.alert_manager is not None:
                    self.alert_manager.alert_trade_executed(
                        "entry", symbol, shares, fill_price, detection["type"]
                    )
            else:
                self.logger.error(
                    f"Order not filled: {ticket.Status}",
                    component="Trade",
                )

        except Exception as e:
            self.logger.error(
                f"Entry error: {str(e)}",
                component="Trade",
                exception=e,
            )

    def _ExitPosition(self, symbol, reason: str):
        """Exit a position."""

        if symbol not in self.algo.active_positions:
            return

        position = self.algo.active_positions[symbol]
        shares = position["shares"]
        entry_price = position["entry_price"]

        if symbol not in self.algo.Securities:
            return

        current_price = self.algo.Securities[symbol].Price

        # P&L using current quote
        if shares > 0:
            pnl = (current_price - entry_price) * shares
        else:
            pnl = (entry_price - current_price) * abs(shares)

        pnl_pct = pnl / (entry_price * abs(shares))

        # Observation mode: log-only
        if self.config.OBSERVATION_MODE:
            self.logger.info(
                f" OBSERVATION MODE - Would exit: {-shares:+d} {symbol} @ ${current_price:.2f} | "
                f"P&L: ${pnl:+.2f} ({pnl_pct:+.2%}) | Reason: {reason}",
                component="Main",
            )
            del self.algo.active_positions[symbol]
            return

        try:
            ticket = self.algo.MarketOrder(symbol, -shares)

            if ticket.Status in (OrderStatus.Filled, OrderStatus.PartiallyFilled):
                exit_price = ticket.AverageFillPrice

                # Actual realized P&L
                if shares > 0:
                    actual_pnl = (exit_price - entry_price) * shares
                else:
                    actual_pnl = (entry_price - exit_price) * abs(shares)

                actual_pnl_pct = actual_pnl / (entry_price * abs(shares))

                self.logger.info(
                    f"✓ EXIT: {-shares:+d} {symbol} @ ${exit_price:.2f} | "
                    f"P&L: ${actual_pnl:+.2f} ({actual_pnl_pct:+.2%}) | {reason}",
                    component="Trade",
                )

                # Backtest record
                if self.backtest_analyzer is not None:
                    self.backtest_analyzer.record_trade(
                        "close",
                        symbol,
                        abs(shares),
                        entry_price,
                        exit_price,
                        timestamp=self.algo.Time,
                        metadata={"reason": reason},
                    )

                # v2+: PVS update
                if self.config.version >= 2 and self.pvs_monitor is not None:
                    was_winner = actual_pnl > 0
                    self.pvs_monitor.RecordTrade(
                        symbol, actual_pnl, was_winner, self.algo.Time
                    )

                # Alerts
                if self.alert_manager is not None:
                    self.alert_manager.alert_trade_executed(
                        "exit", symbol, shares, exit_price, reason
                    )

                # Remove from active
                del self.algo.active_positions[symbol]

            else:
                self.logger.error(
                    f"Exit order not filled: {ticket.Status}",
                    component="Trade",
                )

        except Exception as e:
            self.logger.error(
                f"Exit error: {str(e)}",
                component="Trade",
                exception=e,
            )
