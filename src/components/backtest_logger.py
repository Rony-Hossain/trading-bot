"""
Backtest Results Logger Extension

Add this to main.py to capture comprehensive backtest results
"""

def OnEndOfAlgorithm(self):
    """
    Called at end of backtest - log comprehensive results
    """

    self.logger.info("="*60, component="Backtest")
    self.logger.info("BACKTEST COMPLETE", component="Backtest")
    self.logger.info("="*60, component="Backtest")

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

    self.logger.info("Portfolio Summary:", component="Backtest")
    self.logger.info(f"  Period: {portfolio_stats['start_date']} to {portfolio_stats['end_date']}",
                    component="Backtest")
    self.logger.info(f"  Initial Capital: ${portfolio_stats['initial_capital']:,.2f}",
                    component="Backtest")
    self.logger.info(f"  Final Value: ${portfolio_stats['final_portfolio_value']:,.2f}",
                    component="Backtest")
    self.logger.info(f"  Total P&L: ${portfolio_stats['total_profit']:,.2f}",
                    component="Backtest")
    self.logger.info(f"  Total Return: {portfolio_stats['total_return_pct']:+.2f}%",
                    component="Backtest")
    self.logger.info(f"  Total Fees: ${portfolio_stats['total_fees']:,.2f}",
                    component="Backtest")

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
    self.logger.info(f"Risk Metrics:", component="Backtest")
    self.logger.info(f"  Max Drawdown: {max_dd:.2%}", component="Backtest")

    # Log final summary to ObjectStore
    backtest_results = {
        'type': 'backtest_complete',
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
        },
        'errors': {
            'total': len(self.logger.error_logs),
            'by_component': dict(self.logger.error_counts)
        },
        'max_drawdown': max_dd
    }

    try:
        # Save comprehensive backtest results
        key = f"backtest_results_{self.logger.session_id}"
        self.ObjectStore.Save(key, json.dumps(backtest_results, indent=2, default=str))
        self.logger.info(f"Backtest results saved to ObjectStore: {key}", component="Backtest")
    except Exception as e:
        self.logger.error(f"Failed to save backtest results: {str(e)}",
                         component="Backtest", exception=e)

    # Export all logs
    try:
        self.logger.export_logs_json('all')
        self.logger.info("All logs exported successfully", component="Backtest")
    except Exception as e:
        self.logger.error(f"Failed to export logs: {str(e)}",
                         component="Backtest", exception=e)

    self.logger.info("="*60, component="Backtest")
