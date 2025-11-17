# src/components/analysis/backtest_logger.py

"""
Backtest Logger

Encapsulates the end-of-algorithm logging that used to live
directly in main.py's OnEndOfAlgorithm.
"""

import json


class BacktestLogger:
    def __init__(self, algorithm):
        """
        Parameters
        ----------
        algorithm : QCAlgorithm
            The live QCAlgorithm instance.
        """
        self.algo = algorithm

    def log_backtest(self) -> None:
        """
        Called at end of backtest - log comprehensive results.
        This is basically your old OnEndOfAlgorithm body,
        but written against self.algo instead of self.
        """
        a = self.algo
        logger = a.logger
        config = a.config

        logger.info("=" * 60, component="Backtest")
        logger.info("BACKTEST COMPLETE", component="Backtest")
        logger.info("=" * 60, component="Backtest")

        # ----------------- Portfolio Statistics -----------------
        initial_capital = getattr(
            config, "INITIAL_CAPITAL", a.Portfolio.TotalPortfolioValue
        )

        portfolio_stats = {
            "start_date": str(a.StartDate),
            "end_date": str(a.EndDate),
            "initial_capital": initial_capital,
            "final_portfolio_value": a.Portfolio.TotalPortfolioValue,
            "cash": a.Portfolio.Cash,
            "total_profit": a.Portfolio.TotalPortfolioValue - initial_capital,
            "total_return_pct": (
                (a.Portfolio.TotalPortfolioValue / initial_capital) - 1
            )
            * 100,
            "total_fees": a.Portfolio.TotalFees,
            "total_unrealized_profit": a.Portfolio.TotalUnrealizedProfit,
        }

        logger.info("Portfolio Summary:", component="Backtest")
        logger.info(
            f"  Period: {portfolio_stats['start_date']} to {portfolio_stats['end_date']}",
            component="Backtest",
        )
        logger.info(
            f"  Initial Capital: ${portfolio_stats['initial_capital']:,.2f}",
            component="Backtest",
        )
        logger.info(
            f"  Final Value: ${portfolio_stats['final_portfolio_value']:,.2f}",
            component="Backtest",
        )
        logger.info(
            f"  Total P&L: ${portfolio_stats['total_profit']:,.2f}",
            component="Backtest",
        )
        logger.info(
            f"  Total Return: {portfolio_stats['total_return_pct']:+.2f}%",
            component="Backtest",
        )
        logger.info(
            f"  Total Fees: ${portfolio_stats['total_fees']:,.2f}",
            component="Backtest",
        )

        # ----------------- Detection Statistics -----------------
        if hasattr(logger, "get_detection_summary"):
            detection_summary = logger.get_detection_summary()
            a.Log(detection_summary)

        # ----------------- Trade Statistics -----------------
        # OBSERVATION_MODE lives on config now; old code used self.OBSERVATION_MODE
        obs_mode = getattr(config, "OBSERVATION_MODE", True)
        if not obs_mode and hasattr(logger, "get_trade_summary"):
            trade_summary = logger.get_trade_summary()
            a.Log(trade_summary)

        # ----------------- Error Summary -----------------
        if hasattr(logger, "get_daily_summary"):
            log_summary = logger.get_daily_summary()
            if log_summary.get("total_errors", 0) > 0 and hasattr(
                logger, "get_error_report"
            ):
                error_report = logger.get_error_report()
                a.Log(error_report)

        # ----------------- Risk Metrics -----------------
        max_dd = 0.0
        if hasattr(a, "risk_monitor") and hasattr(a.risk_monitor, "CalculateDrawdown"):
            max_dd = a.risk_monitor.CalculateDrawdown()

        logger.info("Risk Metrics:", component="Backtest")
        logger.info(f"  Max Drawdown: {max_dd:.2%}", component="Backtest")

        # ----------------- ObjectStore dump -----------------
        detection_logs = getattr(logger, "detection_logs", [])
        trade_logs = getattr(logger, "trade_logs", [])
        error_logs = getattr(logger, "error_logs", [])
        error_counts = getattr(logger, "error_counts", {})
        session_id = getattr(logger, "session_id", "unknown_session")

        backtest_results = {
            "type": "backtest_complete",
            "portfolio": portfolio_stats,
            "detections": {
                "total": len(detection_logs),
                "up": sum(1 for d in detection_logs if d.get("direction") == "up"),
                "down": sum(1 for d in detection_logs if d.get("direction") == "down"),
            },
            "trades": {
                "total": len(trade_logs),
                "entries": sum(1 for t in trade_logs if t.get("trade_type") == "entry"),
                "exits": sum(1 for t in trade_logs if t.get("trade_type") == "exit"),
            },
            "errors": {
                "total": len(error_logs),
                "by_component": dict(error_counts),
            },
            "max_drawdown": max_dd,
        }

        try:
            key = f"backtest_results_{session_id}"
            a.ObjectStore.Save(
                key,
                json.dumps(backtest_results, indent=2, default=str),
            )
            logger.info(
                f"Backtest results saved to ObjectStore: {key}",
                component="Backtest",
            )
        except Exception as e:
            logger.error(
                f"Failed to save backtest results: {str(e)}",
                component="Backtest",
                exception=e,
            )

        # ----------------- Export logs -----------------
        if hasattr(logger, "export_logs_json"):
            try:
                logger.export_logs_json("all")
                logger.info(
                    "All logs exported successfully",
                    component="Backtest",
                )
            except Exception as e:
                logger.error(
                    f"Failed to export logs: {str(e)}",
                    component="Backtest",
                    exception=e,
                )

        logger.info("=" * 60, component="Backtest")
