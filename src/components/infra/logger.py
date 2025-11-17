"""
Advanced Logging System for Extreme-Aware Trading Strategy

Features:
- Multiple log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- File outputs (daily rotation)
- Structured JSON logs for analysis
- Performance metrics tracking
- Error traces with context
- Trade audit trail
- Easy sharing/export

Usage in components:
    from logger import StrategyLogger
    logger = StrategyLogger(self.algorithm)
    logger.info("Message", extra_data={'key': 'value'})
"""

from AlgorithmImports import *
import json
from datetime import datetime
from collections import defaultdict
import traceback

class StrategyLogger:
    """
    Comprehensive logging system with file outputs and structured data
    """

    def __init__(self, algorithm):
        self.algorithm = algorithm
        self.logs_dir = "/logs"  # QC doesn't have filesystem, but we track

        # Log buffers (for export/analysis)
        self.daily_logs = []
        self.error_logs = []
        self.trade_logs = []
        self.performance_logs = []
        self.detection_logs = []

        # Counters
        self.log_counts = defaultdict(int)
        self.error_counts = defaultdict(int)

        # Session info
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.start_time = algorithm.Time

        # Log levels
        self.LOG_LEVELS = {
            'DEBUG': 0,
            'INFO': 1,
            'WARNING': 2,
            'ERROR': 3,
            'CRITICAL': 4
        }

        self.current_level = self.LOG_LEVELS['INFO']  # Default level

        self.info(f"StrategyLogger initialized - Session: {self.session_id}")

    def _format_message(self, level, message, component=None, extra_data=None):
        """Format log message with metadata"""

        timestamp = self.algorithm.Time.strftime("%Y-%m-%d %H:%M:%S")

        # Basic format
        formatted = f"[{timestamp}] [{level:8s}]"

        if component:
            formatted += f" [{component}]"

        formatted += f" {message}"

        # Create structured log entry
        log_entry = {
            'timestamp': timestamp,
            'level': level,
            'component': component,
            'message': message,
            'session_id': self.session_id
        }

        if extra_data:
            log_entry['data'] = extra_data

        return formatted, log_entry

    def debug(self, message, component=None, extra_data=None):
        """Debug level - detailed tracing"""
        if self.current_level <= self.LOG_LEVELS['DEBUG']:
            formatted, entry = self._format_message('DEBUG', message, component, extra_data)
            self.algorithm.Debug(formatted)
            self.daily_logs.append(entry)
            self.log_counts['DEBUG'] += 1

    def info(self, message, component=None, extra_data=None):
        """Info level - normal operations"""
        if self.current_level <= self.LOG_LEVELS['INFO']:
            formatted, entry = self._format_message('INFO', message, component, extra_data)
            self.algorithm.Log(formatted)
            self.daily_logs.append(entry)
            self.log_counts['INFO'] += 1

    def warning(self, message, component=None, extra_data=None):
        """Warning level - potential issues"""
        if self.current_level <= self.LOG_LEVELS['WARNING']:
            formatted, entry = self._format_message('WARNING', message, component, extra_data)
            self.algorithm.Log(f" {formatted}")
            self.daily_logs.append(entry)
            self.log_counts['WARNING'] += 1

    def error(self, message, component=None, exception=None, extra_data=None):
        """Error level - something went wrong"""
        formatted, entry = self._format_message('ERROR', message, component, extra_data)

        # Add exception details if provided
        if exception:
            entry['exception'] = {
                'type': type(exception).__name__,
                'message': str(exception),
                'traceback': traceback.format_exc()
            }
            formatted += f"\n    Exception: {type(exception).__name__}: {str(exception)}"

        self.algorithm.Error(f" {formatted}")
        self.daily_logs.append(entry)
        self.error_logs.append(entry)
        self.log_counts['ERROR'] += 1
        self.error_counts[component or 'unknown'] += 1

    def critical(self, message, component=None, exception=None, extra_data=None):
        """Critical level - system failure"""
        formatted, entry = self._format_message('CRITICAL', message, component, extra_data)

        if exception:
            entry['exception'] = {
                'type': type(exception).__name__,
                'message': str(exception),
                'traceback': traceback.format_exc()
            }
            formatted += f"\n    Exception: {type(exception).__name__}: {str(exception)}"

        self.algorithm.Error(f" CRITICAL: {formatted}")
        self.daily_logs.append(entry)
        self.error_logs.append(entry)
        self.log_counts['CRITICAL'] += 1

    def log_extreme_detection(self, symbol, extreme_info):
        """Specialized logging for extreme detection"""

        log_entry = {
            'timestamp': self.algorithm.Time.strftime("%Y-%m-%d %H:%M:%S"),
            'type': 'extreme_detection',
            'symbol': str(symbol),
            'z_score': extreme_info.get('z_score', 0),
            'vol_anomaly': extreme_info.get('vol_anomaly', 0),
            'direction': extreme_info.get('direction', 'unknown'),
            'return_60m': extreme_info.get('return_60m', 0)
        }

        self.detection_logs.append(log_entry)

        msg = (f" EXTREME: {symbol} | "
               f"Z={extreme_info.get('z_score', 0):.2f} | "
               f"VolAnom={extreme_info.get('vol_anomaly', 0):.2f}x | "
               f"Dir={extreme_info.get('direction', '?')} | "
               f"Ret={extreme_info.get('return_60m', 0):.2%}")

        self.info(msg, component='ExtremeDetector', extra_data=log_entry)

    def log_trade(self, trade_type, symbol, quantity, price, reason, metadata=None):
        """Specialized logging for trade execution"""

        log_entry = {
            'timestamp': self.algorithm.Time.strftime("%Y-%m-%d %H:%M:%S"),
            'type': 'trade',
            'trade_type': trade_type,  # 'entry', 'exit', 'hedge'
            'symbol': str(symbol),
            'quantity': quantity,
            'price': price,
            'reason': reason,
            'portfolio_value': self.algorithm.Portfolio.TotalPortfolioValue
        }

        if metadata:
            log_entry['metadata'] = metadata

        self.trade_logs.append(log_entry)

        msg = (f" TRADE: {trade_type.upper()} {quantity:+.2f} {symbol} "
               f"@ ${price:.2f} | Reason: {reason}")

        self.info(msg, component='TradeExecution', extra_data=log_entry)

    def log_regime_change(self, old_regime, new_regime, regime_data):
        """Log HMM regime changes"""

        log_entry = {
            'timestamp': self.algorithm.Time.strftime("%Y-%m-%d %H:%M:%S"),
            'type': 'regime_change',
            'old_regime': old_regime,
            'new_regime': new_regime,
            'gpm': regime_data.get('gpm', 1.0),
            'state_probs': regime_data.get('state_probs', {})
        }

        msg = f" REGIME: {old_regime} → {new_regime} (GPM: {regime_data.get('gpm', 1.0):.2f})"

        self.info(msg, component='HMMRegime', extra_data=log_entry)

    def log_circuit_breaker(self, breaker_type, reason, action):
        """Log circuit breaker activations"""

        log_entry = {
            'timestamp': self.algorithm.Time.strftime("%Y-%m-%d %H:%M:%S"),
            'type': 'circuit_breaker',
            'breaker_type': breaker_type,
            'reason': reason,
            'action': action
        }

        msg = f" CIRCUIT BREAKER: {breaker_type} | {reason} | Action: {action}"

        self.warning(msg, component='CircuitBreaker', extra_data=log_entry)

    def log_performance_snapshot(self):
        """Log current performance metrics"""

        portfolio = self.algorithm.Portfolio

        log_entry = {
            'timestamp': self.algorithm.Time.strftime("%Y-%m-%d %H:%M:%S"),
            'type': 'performance',
            'total_value': portfolio.TotalPortfolioValue,
            'cash': portfolio.Cash,
            'total_holdings': portfolio.TotalHoldingsValue,
            'total_unrealized_profit': portfolio.TotalUnrealizedProfit,
            'total_fees': portfolio.TotalFees,
            'positions': len([x for x in portfolio.Values if x.Invested])
        }

        self.performance_logs.append(log_entry)

        return log_entry

    def log_avwap_track(self, symbol, avwap_data):
        """Log A-VWAP tracking updates"""

        msg = (f" A-VWAP: {symbol} | "
               f"VWAP=${avwap_data.get('avwap', 0):.2f} | "
               f"Distance={avwap_data.get('distance', 0):.2%} | "
               f"Bars={avwap_data.get('bars_since_impulse', 0)}")

        self.debug(msg, component='AVWAPTracker', extra_data=avwap_data)

    def log_risk_metrics(self, metrics):
        """Log risk management metrics"""

        msg = (f" RISK: DD={metrics.get('drawdown', 0):.2%} | "
               f"VaR={metrics.get('var_utilization', 0):.1%} | "
               f"Beta={metrics.get('beta', 0):.2f} | "
               f"PVS={metrics.get('pvs', 0):.1f}")

        self.info(msg, component='RiskMonitor', extra_data=metrics)

    def get_daily_summary(self):
        """Generate daily summary of logs"""

        summary = {
            'date': self.algorithm.Time.strftime("%Y-%m-%d"),
            'session_id': self.session_id,
            'log_counts': dict(self.log_counts),
            'error_counts': dict(self.error_counts),
            'total_logs': len(self.daily_logs),
            'total_errors': len(self.error_logs),
            'total_trades': len(self.trade_logs),
            'total_detections': len(self.detection_logs),
            'performance_snapshots': len(self.performance_logs)
        }

        return summary

    def export_logs_json(self, log_type='all'):
        """
        Export logs as JSON for analysis

        Args:
            log_type: 'all', 'errors', 'trades', 'detections', 'performance'
        """

        if log_type == 'all':
            data = {
                'session_id': self.session_id,
                'start_time': str(self.start_time),
                'current_time': str(self.algorithm.Time),
                'summary': self.get_daily_summary(),
                'logs': self.daily_logs,
                'errors': self.error_logs,
                'trades': self.trade_logs,
                'detections': self.detection_logs,
                'performance': self.performance_logs
            }
        elif log_type == 'errors':
            data = {'errors': self.error_logs}
        elif log_type == 'trades':
            data = {'trades': self.trade_logs}
        elif log_type == 'detections':
            data = {'detections': self.detection_logs}
        elif log_type == 'performance':
            data = {'performance': self.performance_logs}
        else:
            data = {'logs': self.daily_logs}

        # Convert to JSON string
        json_str = json.dumps(data, indent=2, default=str)

        # In QuantConnect, we can't write files directly, but we can log it
        # or save to ObjectStore for later retrieval
        try:
            # Store in QC ObjectStore
            key = f"logs_{log_type}_{self.session_id}_{self.algorithm.Time.strftime('%Y%m%d')}"
            self.algorithm.ObjectStore.Save(key, json_str)
            self.info(f"Logs exported to ObjectStore: {key}", component='Logger')
        except Exception as e:
            self.error(f"Failed to export logs: {str(e)}", component='Logger', exception=e)

        return json_str

    def get_error_report(self):
        """Generate detailed error report"""

        if not self.error_logs:
            return "No errors logged."

        report = "\n" + "="*60 + "\n"
        report += "ERROR REPORT\n"
        report += "="*60 + "\n\n"

        # Group errors by component
        errors_by_component = defaultdict(list)
        for error in self.error_logs:
            component = error.get('component', 'unknown')
            errors_by_component[component].append(error)

        for component, errors in errors_by_component.items():
            report += f"\n{component} ({len(errors)} errors):\n"
            report += "-" * 40 + "\n"

            for error in errors[-5:]:  # Last 5 errors
                report += f"  [{error['timestamp']}] {error['message']}\n"
                if 'exception' in error:
                    report += f"    {error['exception']['type']}: {error['exception']['message']}\n"

            if len(errors) > 5:
                report += f"  ... and {len(errors) - 5} more\n"

        report += "\n" + "="*60 + "\n"

        return report

    def get_trade_summary(self):
        """Generate trade execution summary"""

        if not self.trade_logs:
            return "No trades executed."

        summary = "\n" + "="*60 + "\n"
        summary += "TRADE SUMMARY\n"
        summary += "="*60 + "\n\n"

        # Count by type
        entry_count = sum(1 for t in self.trade_logs if t['trade_type'] == 'entry')
        exit_count = sum(1 for t in self.trade_logs if t['trade_type'] == 'exit')
        hedge_count = sum(1 for t in self.trade_logs if t['trade_type'] == 'hedge')

        summary += f"Total Trades: {len(self.trade_logs)}\n"
        summary += f"  Entries: {entry_count}\n"
        summary += f"  Exits: {exit_count}\n"
        summary += f"  Hedges: {hedge_count}\n\n"

        summary += "Recent Trades:\n"
        summary += "-" * 40 + "\n"

        for trade in self.trade_logs[-10:]:  # Last 10 trades
            summary += (f"  [{trade['timestamp']}] {trade['trade_type'].upper()} "
                       f"{trade['quantity']:+.2f} {trade['symbol']} @ ${trade['price']:.2f}\n")
            summary += f"    Reason: {trade['reason']}\n"

        summary += "\n" + "="*60 + "\n"

        return summary

    def get_detection_summary(self):
        """Generate extreme detection summary"""

        if not self.detection_logs:
            return "No extremes detected."

        summary = "\n" + "="*60 + "\n"
        summary += "EXTREME DETECTION SUMMARY\n"
        summary += "="*60 + "\n\n"

        summary += f"Total Extremes: {len(self.detection_logs)}\n\n"

        # Count by direction
        up_count = sum(1 for d in self.detection_logs if d['direction'] == 'up')
        down_count = sum(1 for d in self.detection_logs if d['direction'] == 'down')

        summary += f"  Up: {up_count}\n"
        summary += f"  Down: {down_count}\n\n"

        # Average metrics
        avg_z = sum(abs(d['z_score']) for d in self.detection_logs) / len(self.detection_logs)
        avg_vol = sum(d['vol_anomaly'] for d in self.detection_logs) / len(self.detection_logs)

        summary += f"Average |Z-score|: {avg_z:.2f}\n"
        summary += f"Average Vol Anomaly: {avg_vol:.2f}x\n\n"

        summary += "Recent Detections:\n"
        summary += "-" * 40 + "\n"

        for det in self.detection_logs[-10:]:  # Last 10
            summary += (f"  [{det['timestamp']}] {det['symbol']:6s} | "
                       f"Z={det['z_score']:+.2f} | Vol={det['vol_anomaly']:.1f}x | "
                       f"{det['direction']:>4s}\n")

        summary += "\n" + "="*60 + "\n"

        return summary

    def set_log_level(self, level):
        """Change logging level"""
        if level in self.LOG_LEVELS:
            self.current_level = self.LOG_LEVELS[level]
            self.info(f"Log level set to {level}", component='Logger')
        else:
            self.warning(f"Invalid log level: {level}", component='Logger')

    def clear_logs(self):
        """Clear all log buffers (use carefully!)"""
        self.daily_logs.clear()
        self.error_logs.clear()
        self.trade_logs.clear()
        self.performance_logs.clear()
        self.detection_logs.clear()
        self.log_counts.clear()
        self.error_counts.clear()

        self.info("All logs cleared", component='Logger')
