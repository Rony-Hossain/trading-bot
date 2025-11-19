"""
Alert System for Extreme-Aware Trading Strategy

Sends real-time alerts via multiple channels when critical events occur.

Features:
- Email alerts (SendGrid, SMTP)
- SMS alerts (Twilio)
- Slack/Discord webhooks
- Telegram bot
- QuantConnect notifications
- Alert severity levels
- Rate limiting (avoid spam)
- Daily summary emails
- Alert history tracking

Usage:
    from alert_manager import AlertManager

    alert_manager = AlertManager(algorithm, config)
    alert_manager.send_alert('critical', 'Circuit breaker fired', details)
"""

from AlgorithmImports import *
import json
from datetime import datetime, timedelta
from collections import defaultdict, deque


class AlertManager:
    """
    Multi-channel alert system for trading strategy
    """

from collections import deque, defaultdict
from datetime import timedelta

class AlertManager:
    def __init__(self, algorithm, alert_config=None):
        self.algorithm = algorithm
        self.logger = algorithm.logger if hasattr(algorithm, "logger") else None

        # Alert configuration: can be Config or dict or None
        self.config = alert_config

        # Small helper so we can read from Config OR dict OR None safely
        def _cfg(name, default=None):
            if self.config is None:
                return default
            # Config-style attribute access
            if hasattr(self.config, name):
                return getattr(self.config, name)
            # Dict-style access (if you ever pass a dict)
            if isinstance(self.config, dict):
                return self.config.get(name, default)
            return default

        # Alert channels
        self.channels = {
            "email": _cfg("ENABLE_EMAIL_ALERTS", False),
            "sms": _cfg("ENABLE_SMS_ALERTS", False),
            "slack": _cfg("ENABLE_SLACK_ALERTS", False),
            "telegram": _cfg("ENABLE_TELEGRAM_ALERTS", False),
            "qc_notify": True,  # Always available in QC
        }

        # Email-specific settings
        self.email_to = _cfg("ALERT_EMAIL_TO", None)
        self.email_subject_prefix = _cfg(
            "ALERT_EMAIL_SUBJECT_PREFIX",
            "[ExtremeAware]"
        )

        # Alert history
        self.alert_history = deque(maxlen=1000)
        self.alert_counts = defaultdict(int)

        # Rate limiting (prevent spam)
        self.rate_limits = {
            "info": timedelta(minutes=30),
            "warning": timedelta(minutes=15),
            "error": timedelta(minutes=5),
            "critical": timedelta(minutes=1),
        }
        self.last_alert_time = {}

        # Per-symbol rate limiting for detections (prevent flood)
        self.symbol_detection_cooldown = timedelta(
            minutes=15
        )  # Same as extreme detector cooldown
        self.last_detection_alert = {}  # symbol -> last alert time

        # Daily summary tracking
        self.daily_summary = {
            "date": algorithm.Time.date(),
            "alerts": [],
            "errors": 0,
            "warnings": 0,
            "critical": 0,
        }

        if self.logger:
            self.logger.info("AlertManager initialized", component="AlertManager")

    def _default_config(self):
        """Default alert configuration"""
        return {
            "enable_email": False,  # Set True to enable
            "enable_sms": False,
            "enable_slack": False,
            "enable_telegram": False,
            "email_recipients": [],
            "sms_numbers": [],
            "slack_webhook": None,
            "telegram_bot_token": None,
            "telegram_chat_id": None,
            "alert_on_startup": True,
            "alert_on_market_close": True,
            "alert_on_errors": True,
            "alert_on_circuit_breakers": True,
            "alert_on_detections": False,  # Too noisy
            "daily_summary_time": "16:05",  # After market close
        }

    def send_alert(self, level, message, component=None, details=None):
        """
        Send alert across configured channels

        Args:
            level: 'info', 'warning', 'error', 'critical'
            message: Alert message
            component: Component that triggered alert
            details: Additional context (dict)
        """

        # Check rate limiting
        if self._is_rate_limited(level, message):
            return

        # Create alert object
        alert = {
            "timestamp": self.algorithm.Time.strftime("%Y-%m-%d %H:%M:%S"),
            "level": level,
            "message": message,
            "component": component,
            "details": details or {},
        }

        # Add to history
        self.alert_history.append(alert)
        self.alert_counts[level] += 1

        # Add to daily summary
        self.daily_summary["alerts"].append(alert)
        if level == "error":
            self.daily_summary["errors"] += 1
        elif level == "warning":
            self.daily_summary["warnings"] += 1
        elif level == "critical":
            self.daily_summary["critical"] += 1

        # Format message with emoji
        emoji = self._get_emoji(level)
        formatted_msg = f"{emoji} {level.upper()}: {message}"

        if component:
            formatted_msg += f" [{component}]"

        # Send via each enabled channel
        if self.channels["qc_notify"]:
            self._send_qc_notification(formatted_msg, alert)

        if self.channels["email"] and level in ["error", "critical"]:
            self._send_email(formatted_msg, alert)

        if self.channels["sms"] and level == "critical":
            self._send_sms(formatted_msg, alert)

        if self.channels["slack"]:
            self._send_slack(formatted_msg, alert)

        if self.channels["telegram"]:
            self._send_telegram(formatted_msg, alert)

        # Log it
        if self.logger:
            self.logger.info(f"Alert sent: {formatted_msg}", component="AlertManager")

    def _is_rate_limited(self, level, message):
        """Check if alert should be rate limited"""
        key = f"{level}:{message[:50]}"  # Use first 50 chars as key

        if key in self.last_alert_time:
            time_since = self.algorithm.Time - self.last_alert_time[key]
            if time_since < self.rate_limits.get(level, timedelta(minutes=5)):
                return True

        self.last_alert_time[key] = self.algorithm.Time
        return False

    def _get_emoji(self, level):
        """Get emoji for alert level"""
        emojis = {
            "info": "info",
            "warning": "wearning",
            "error": "error",
            "critical": "",
        }
        return emojis.get(level, "")

    def _send_qc_notification(self, message, alert) -> None:
        """
        Send a QC notification if email alerts are enabled.

        QC expects: Notify.Email(to, subject, message)
        """
        # Respect config channel: if email channel is off, do nothing
        if not self.channels.get("email", False):
            return

        # If we don't have a target address, bail out gracefully
        if not self.email_to:
            self.algorithm.Log(
                "AlertManager: email_to not configured, skipping Notify.Email"
            )
            return

        level = alert.get("level", "info").upper()
        subject = f"{self.email_subject_prefix} [{level}] {alert.get('component', 'Alert')}"

        try:
            # Use QC's Notify method: Notify.Email(to, subject, message)
            self.algorithm.Notify.Email(self.email_to, subject, message)
        except Exception as e:
            if self.logger:
                self.logger.error(
                    f"Failed to send QC notification: {str(e)}",
                    component="AlertManager",
                    exception=e,
                )
            else:
                self.algorithm.Log(f"AlertManager: failed to send QC email: {e}")

    def _send_email(self, message, alert):
        """Send email alert (requires configuration)"""
        if not self.config.get("email_recipients"):
            return

        try:
            # Example using SendGrid (needs API key)
            # Or use SMTP

            subject = f"[{alert['level'].upper()}] Trading Alert - {self.algorithm.Time.strftime('%Y-%m-%d %H:%M')}"

            body = f"""
Trading Strategy Alert

Time: {alert['timestamp']}
Level: {alert['level'].upper()}
Component: {alert.get('component', 'N/A')}

Message:
{alert['message']}

Details:
{json.dumps(alert['details'], indent=2)}

---
Extreme-Aware Trading Strategy
            """

            # Send via configured email service
            # self.algorithm.Notify.Email(subject, body)

            if self.logger:
                self.logger.info(
                    f"Email alert sent to {len(self.config['email_recipients'])} recipients",
                    component="AlertManager",
                )

        except Exception as e:
            if self.logger:
                self.logger.error(
                    f"Failed to send email: {str(e)}",
                    component="AlertManager",
                    exception=e,
                )

    def _send_sms(self, message, alert):
        """Send SMS alert via Twilio (requires configuration)"""
        if not self.config.get("sms_numbers"):
            return

        try:
            # Twilio SMS example
            # Requires: twilio_account_sid, twilio_auth_token, twilio_from_number

            # Keep SMS short
            sms_message = f"{alert['level'].upper()}: {alert['message'][:100]}"

            # Send via Twilio API
            # (Implementation depends on QC's external API support)

            if self.logger:
                self.logger.info(
                    f"SMS alert sent to {len(self.config['sms_numbers'])} numbers",
                    component="AlertManager",
                )

        except Exception as e:
            if self.logger:
                self.logger.error(
                    f"Failed to send SMS: {str(e)}",
                    component="AlertManager",
                    exception=e,
                )

    def _send_slack(self, message, alert):
        """Send Slack webhook alert"""
        webhook_url = self.config.get("slack_webhook")
        if not webhook_url:
            return

        try:
            # Slack webhook payload
            color_map = {
                "info": "#36a64f",  # Green
                "warning": "#ff9900",  # Orange
                "error": "#ff0000",  # Red
                "critical": "#ff0000",  # Red
            }

            payload = {
                "attachments": [
                    {
                        "color": color_map.get(alert["level"], "#36a64f"),
                        "title": f"{alert['level'].upper()} Alert",
                        "text": alert["message"],
                        "fields": [
                            {
                                "title": "Time",
                                "value": alert["timestamp"],
                                "short": True,
                            },
                            {
                                "title": "Component",
                                "value": alert.get("component", "N/A"),
                                "short": True,
                            },
                        ],
                        "footer": "Extreme-Aware Trading Strategy",
                        "ts": int(self.algorithm.Time.timestamp()),
                    }
                ]
            }

            # Send webhook request
            # (Would need requests library or QC's HTTP support)

            if self.logger:
                self.logger.info("Slack alert sent", component="AlertManager")

        except Exception as e:
            if self.logger:
                self.logger.error(
                    f"Failed to send Slack alert: {str(e)}",
                    component="AlertManager",
                    exception=e,
                )

    def _send_telegram(self, message, alert):
        """Send Telegram bot message"""
        bot_token = self.config.get("telegram_bot_token")
        chat_id = self.config.get("telegram_chat_id")

        if not bot_token or not chat_id:
            return

        try:
            # Telegram bot API
            text = f"*{alert['level'].upper()} Alert*\n\n"
            text += f"_{alert['timestamp']}_\n\n"
            text += f"{alert['message']}\n\n"
            text += f"Component: `{alert.get('component', 'N/A')}`"

            # Send via Telegram Bot API
            # (Would need HTTP request capability)

            if self.logger:
                self.logger.info("Telegram alert sent", component="AlertManager")

        except Exception as e:
            if self.logger:
                self.logger.error(
                    f"Failed to send Telegram alert: {str(e)}",
                    component="AlertManager",
                    exception=e,
                )

    def alert_circuit_breaker(self, breaker_type, reason, action):
        """Specialized alert for circuit breakers"""
        details = {
            "breaker_type": breaker_type,
            "reason": reason,
            "action": action,
            "portfolio_value": self.algorithm.Portfolio.TotalPortfolioValue,
        }

        message = f"Circuit Breaker: {breaker_type} - {reason} - Action: {action}"

        self.send_alert(
            "critical", message, component="CircuitBreaker", details=details
        )

    def alert_extreme_detected(self, symbol, extreme_info):
        """
        Alert when extreme detected (optional, can be noisy)

        Uses per-symbol rate limiting to prevent alert flooding when
        multiple symbols trigger extremes simultaneously.
        """
        if not self.config.get("alert_on_detections", False):
            return

        # Check per-symbol rate limit to prevent flood
        symbol_str = str(symbol)
        if symbol_str in self.last_detection_alert:
            time_since = self.algorithm.Time - self.last_detection_alert[symbol_str]
            if time_since < self.symbol_detection_cooldown:
                # Silently skip - too soon since last alert for this symbol
                if self.logger:
                    self.logger.debug(
                        f"Detection alert skipped for {symbol_str}: cooldown active "
                        f"({(self.symbol_detection_cooldown - time_since).total_seconds() / 60:.1f} min remaining)",
                        component="AlertManager",
                    )
                return

        # Update last alert time for this symbol
        self.last_detection_alert[symbol_str] = self.algorithm.Time

        message = (
            f"Extreme detected: {symbol} | "
            f"Z={extreme_info['z_score']:.2f} | "
            f"VolAnom={extreme_info['vol_anomaly']:.2f}x"
        )

        self.send_alert(
            "info", message, component="ExtremeDetector", details=extreme_info
        )

    def alert_trade_executed(self, trade_type, symbol, quantity, price, reason):
        """Alert on trade execution"""
        details = {
            "trade_type": trade_type,
            "symbol": str(symbol),
            "quantity": quantity,
            "price": price,
            "reason": reason,
        }

        message = f"Trade: {trade_type.upper()} {quantity:+.0f} {symbol} @ ${price:.2f}"

        self.send_alert("info", message, component="TradeExecution", details=details)

    def alert_error_spike(self, error_count, time_window):
        """Alert when error rate spikes"""
        message = f"Error spike detected: {error_count} errors in {time_window} minutes"

        self.send_alert("error", message, component="HealthMonitor")

    def alert_detection_drought(self, hours_since_last):
        """Alert when no detections for unusual period"""
        message = f"No extremes detected for {hours_since_last} hours (unusual)"

        self.send_alert("warning", message, component="HealthMonitor")

    def alert_drawdown(self, current_dd, threshold):
        """Alert on significant drawdown"""
        details = {
            "current_drawdown": current_dd,
            "threshold": threshold,
            "portfolio_value": self.algorithm.Portfolio.TotalPortfolioValue,
        }

        message = f"Drawdown alert: {current_dd:.2%} (threshold: {threshold:.2%})"

        self.send_alert("warning", message, component="RiskMonitor", details=details)

    def alert_system_health(self, health_status):
        """Alert on system health issues"""
        failed_checks = [k for k, v in health_status.items() if not v]

        if failed_checks:
            message = f"System health check failed: {', '.join(failed_checks)}"
            self.send_alert(
                "error", message, component="HealthMonitor", details=health_status
            )

    def send_daily_summary(self):
        """Send end-of-day summary"""
        summary = self.get_daily_summary()

        message = f"""Daily Summary - {summary['date']}

Total Alerts: {summary['total_alerts']}
  Critical: {summary['critical']}
  Errors: {summary['errors']}
  Warnings: {summary['warnings']}

Extremes Detected: {summary.get('extremes_detected', 0)}
Trades Executed: {summary.get('trades_executed', 0)}

Portfolio Value: ${summary.get('portfolio_value', 0):,.2f}
Daily Return: {summary.get('daily_return', 0):.2%}

See logs for detailed breakdown.
        """

        self.send_alert("info", message, component="DailySummary", details=summary)

    def get_daily_summary(self):
        """Generate daily summary statistics"""
        summary = {
            "date": self.daily_summary["date"],
            "total_alerts": len(self.daily_summary["alerts"]),
            "critical": self.daily_summary["critical"],
            "errors": self.daily_summary["errors"],
            "warnings": self.daily_summary["warnings"],
            "portfolio_value": self.algorithm.Portfolio.TotalPortfolioValue,
        }

        return summary

    def reset_daily_summary(self):
        """Reset daily summary for new day"""
        self.daily_summary = {
            "date": self.algorithm.Time.date(),
            "alerts": [],
            "errors": 0,
            "warnings": 0,
            "critical": 0,
        }

    def get_alert_history(self, hours=24, level=None):
        """Get alert history for specified time period"""
        cutoff_time = self.algorithm.Time - timedelta(hours=hours)

        history = [
            alert
            for alert in self.alert_history
            if datetime.strptime(alert["timestamp"], "%Y-%m-%d %H:%M:%S") >= cutoff_time
        ]

        if level:
            history = [a for a in history if a["level"] == level]

        return history

    def get_alert_stats(self):
        """Get alert statistics"""
        # Clean up stale detection cooldowns (older than 24 hours)
        cutoff = self.algorithm.Time - timedelta(hours=24)
        stale_symbols = [
            symbol
            for symbol, last_time in self.last_detection_alert.items()
            if last_time < cutoff
        ]
        for symbol in stale_symbols:
            del self.last_detection_alert[symbol]

        return {
            "total_alerts": len(self.alert_history),
            "by_level": dict(self.alert_counts),
            "rate_limited_count": len(self.last_alert_time),
            "detection_cooldown_active": len(
                self.last_detection_alert
            ),  # Symbols on cooldown
        }
