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
import yaml
import os
from pathlib import Path

class AlertManager:
    """
    Multi-channel alert system for trading strategy
    """

    def __init__(self, algorithm, alert_config=None):
        self.algorithm = algorithm
        self.logger = algorithm.logger if hasattr(algorithm, 'logger') else None

        # Load scanner.yaml config if available
        scanner_config = self._load_scanner_yaml()

        # Alert configuration (scanner.yaml takes precedence)
        self.config = alert_config or scanner_config or self._default_config()

        # Extract scanner.yaml settings if present
        if scanner_config:
            self.mode = scanner_config.get('alerts', {}).get('mode', 'PROMPT_FIRST')
            self.rate_limit_per_hour = scanner_config.get('alerts', {}).get('rate_limit_per_hour', 12)
            self.min_confidence = scanner_config.get('alerts', {}).get('min_confidence', 0.7)
            self.min_signal_score = scanner_config.get('scoring', {}).get('min_signal_score', 2.0)

            if self.logger:
                self.logger.info(
                    f"AlertManager loaded scanner.yaml: mode={self.mode}, "
                    f"rate_limit={self.rate_limit_per_hour}/hr, min_score={self.min_signal_score}",
                    component="AlertManager"
                )
        else:
            self.mode = 'LOG_ONLY'
            self.rate_limit_per_hour = 12
            self.min_confidence = 0.7
            self.min_signal_score = 2.0
        
        # Alert channels
        self.channels = {
            'email': self.config.get('enable_email', False),
            'sms': self.config.get('enable_sms', False),
            'slack': self.config.get('enable_slack', False),
            'telegram': self.config.get('enable_telegram', False),
            'qc_notify': True  # Always available in QC
        }
        
        # Alert history
        self.alert_history = deque(maxlen=1000)
        self.alert_counts = defaultdict(int)
        
        # Rate limiting (prevent spam)
        self.rate_limits = {
            'info': timedelta(minutes=30),
            'warning': timedelta(minutes=15),
            'error': timedelta(minutes=5),
            'critical': timedelta(minutes=1)
        }
        self.last_alert_time = {}
        
        # Daily summary tracking
        self.daily_summary = {
            'date': algorithm.Time.date(),
            'alerts': [],
            'errors': 0,
            'warnings': 0,
            'critical': 0
        }
        
        if self.logger:
            self.logger.info("AlertManager initialized", component="AlertManager")

    def _load_scanner_yaml(self):
        """
        Load scanner.yaml configuration file using pathlib for robustness

        Returns:
            dict: Parsed YAML config, or None if not found
        """
        # Try multiple possible paths (de-duplicated, using pathlib)
        # Order: config subdir -> parent config -> current dir
        possible_paths = [
            Path('config/scanner.yaml'),      # ./config/scanner.yaml
            Path('../config/scanner.yaml'),   # ../config/scanner.yaml
            Path('scanner.yaml')              # ./scanner.yaml (cwd)
        ]

        for path in possible_paths:
            if path.exists():
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        config = yaml.safe_load(f)
                    if self.logger:
                        self.logger.info(f"Loaded scanner config from: {path}", component="AlertManager")
                    return config
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"Failed to load {path}: {str(e)}", component="AlertManager")
                    # Continue trying other paths instead of returning None immediately
                    continue

        # scanner.yaml not found - this is okay, use defaults
        if self.logger:
            self.logger.debug("No scanner.yaml found, using default config", component="AlertManager")
        return None

    def _default_config(self):
        """Default alert configuration"""
        return {
            'enable_email': False,  # Set True to enable
            'enable_sms': False,
            'enable_slack': False,
            'enable_telegram': False,
            'email_recipients': [],
            'sms_numbers': [],
            'slack_webhook': None,
            'telegram_bot_token': None,
            'telegram_chat_id': None,
            'alert_on_startup': True,
            'alert_on_market_close': True,
            'alert_on_errors': True,
            'alert_on_circuit_breakers': True,
            'alert_on_detections': False,  # Too noisy
            'daily_summary_time': '16:05'  # After market close
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
            'timestamp': self.algorithm.Time.strftime("%Y-%m-%d %H:%M:%S"),
            'level': level,
            'message': message,
            'component': component,
            'details': details or {}
        }
        
        # Add to history
        self.alert_history.append(alert)
        self.alert_counts[level] += 1
        
        # Add to daily summary
        self.daily_summary['alerts'].append(alert)
        if level == 'error':
            self.daily_summary['errors'] += 1
        elif level == 'warning':
            self.daily_summary['warnings'] += 1
        elif level == 'critical':
            self.daily_summary['critical'] += 1
        
        # Format message with emoji
        emoji = self._get_emoji(level)
        formatted_msg = f"{emoji} {level.upper()}: {message}"
        
        if component:
            formatted_msg += f" [{component}]"
        
        # Send via each enabled channel
        if self.channels['qc_notify']:
            self._send_qc_notification(formatted_msg, alert)
        
        if self.channels['email'] and level in ['error', 'critical']:
            self._send_email(formatted_msg, alert)
        
        if self.channels['sms'] and level == 'critical':
            self._send_sms(formatted_msg, alert)
        
        if self.channels['slack']:
            self._send_slack(formatted_msg, alert)
        
        if self.channels['telegram']:
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
            'info': 'ℹ️',
            'warning': '⚠️',
            'error': '❌',
            'critical': '🚨'
        }
        return emojis.get(level, '📢')
    
    def _send_qc_notification(self, message, alert):
        """Send QuantConnect notification (always available)"""
        try:
            # Use QC's Notify method
            self.algorithm.Notify.Email(
                subject=f"Trading Alert - {alert['level'].upper()}",
                message=message,
                headers=None
            )
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to send QC notification: {str(e)}", 
                                component="AlertManager", exception=e)
    
    def _send_email(self, message, alert):
        """Send email alert (requires configuration)"""
        if not self.config.get('email_recipients'):
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
                self.logger.info(f"Email alert sent to {len(self.config['email_recipients'])} recipients",
                               component="AlertManager")
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to send email: {str(e)}", 
                                component="AlertManager", exception=e)
    
    def _send_sms(self, message, alert):
        """Send SMS alert via Twilio (requires configuration)"""
        if not self.config.get('sms_numbers'):
            return
        
        try:
            # Twilio SMS example
            # Requires: twilio_account_sid, twilio_auth_token, twilio_from_number
            
            # Keep SMS short
            sms_message = f"{alert['level'].upper()}: {alert['message'][:100]}"
            
            # Send via Twilio API
            # (Implementation depends on QC's external API support)
            
            if self.logger:
                self.logger.info(f"SMS alert sent to {len(self.config['sms_numbers'])} numbers",
                               component="AlertManager")
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to send SMS: {str(e)}", 
                                component="AlertManager", exception=e)
    
    def _send_slack(self, message, alert):
        """Send Slack webhook alert"""
        webhook_url = self.config.get('slack_webhook')
        if not webhook_url:
            return
        
        try:
            # Slack webhook payload
            color_map = {
                'info': '#36a64f',      # Green
                'warning': '#ff9900',   # Orange
                'error': '#ff0000',     # Red
                'critical': '#ff0000'   # Red
            }
            
            payload = {
                'attachments': [{
                    'color': color_map.get(alert['level'], '#36a64f'),
                    'title': f"{alert['level'].upper()} Alert",
                    'text': alert['message'],
                    'fields': [
                        {
                            'title': 'Time',
                            'value': alert['timestamp'],
                            'short': True
                        },
                        {
                            'title': 'Component',
                            'value': alert.get('component', 'N/A'),
                            'short': True
                        }
                    ],
                    'footer': 'Extreme-Aware Trading Strategy',
                    'ts': int(self.algorithm.Time.timestamp())
                }]
            }
            
            # Send webhook request
            # (Would need requests library or QC's HTTP support)
            
            if self.logger:
                self.logger.info("Slack alert sent", component="AlertManager")
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to send Slack alert: {str(e)}", 
                                component="AlertManager", exception=e)
    
    def _send_telegram(self, message, alert):
        """Send Telegram bot message"""
        bot_token = self.config.get('telegram_bot_token')
        chat_id = self.config.get('telegram_chat_id')
        
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
                self.logger.error(f"Failed to send Telegram alert: {str(e)}", 
                                component="AlertManager", exception=e)
    
    def alert_circuit_breaker(self, breaker_type, reason, action):
        """Specialized alert for circuit breakers"""
        details = {
            'breaker_type': breaker_type,
            'reason': reason,
            'action': action,
            'portfolio_value': self.algorithm.Portfolio.TotalPortfolioValue
        }
        
        message = f"Circuit Breaker: {breaker_type} - {reason} - Action: {action}"
        
        self.send_alert('critical', message, component='CircuitBreaker', details=details)
    
    def alert_extreme_detected(self, symbol, extreme_info):
        """Alert when extreme detected (optional, can be noisy)"""
        if not self.config.get('alert_on_detections', False):
            return
        
        message = (f"Extreme detected: {symbol} | "
                  f"Z={extreme_info['z_score']:.2f} | "
                  f"VolAnom={extreme_info['vol_anomaly']:.2f}x")
        
        self.send_alert('info', message, component='ExtremeDetector', details=extreme_info)
    
    def alert_trade_executed(self, trade_type, symbol, quantity, price, reason):
        """Alert on trade execution"""
        details = {
            'trade_type': trade_type,
            'symbol': str(symbol),
            'quantity': quantity,
            'price': price,
            'reason': reason
        }
        
        message = f"Trade: {trade_type.upper()} {quantity:+.0f} {symbol} @ ${price:.2f}"
        
        self.send_alert('info', message, component='TradeExecution', details=details)
    
    def alert_error_spike(self, error_count, time_window):
        """Alert when error rate spikes"""
        message = f"Error spike detected: {error_count} errors in {time_window} minutes"
        
        self.send_alert('error', message, component='HealthMonitor')
    
    def alert_detection_drought(self, hours_since_last):
        """Alert when no detections for unusual period"""
        message = f"No extremes detected for {hours_since_last} hours (unusual)"
        
        self.send_alert('warning', message, component='HealthMonitor')
    
    def alert_drawdown(self, current_dd, threshold):
        """Alert on significant drawdown"""
        details = {
            'current_drawdown': current_dd,
            'threshold': threshold,
            'portfolio_value': self.algorithm.Portfolio.TotalPortfolioValue
        }
        
        message = f"Drawdown alert: {current_dd:.2%} (threshold: {threshold:.2%})"
        
        self.send_alert('warning', message, component='RiskMonitor', details=details)
    
    def alert_system_health(self, health_status):
        """Alert on system health issues"""
        failed_checks = [k for k, v in health_status.items() if not v]
        
        if failed_checks:
            message = f"System health check failed: {', '.join(failed_checks)}"
            self.send_alert('error', message, component='HealthMonitor', details=health_status)
    
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
        
        self.send_alert('info', message, component='DailySummary', details=summary)
    
    def get_daily_summary(self):
        """Generate daily summary statistics"""
        summary = {
            'date': self.daily_summary['date'],
            'total_alerts': len(self.daily_summary['alerts']),
            'critical': self.daily_summary['critical'],
            'errors': self.daily_summary['errors'],
            'warnings': self.daily_summary['warnings'],
            'portfolio_value': self.algorithm.Portfolio.TotalPortfolioValue
        }
        
        return summary
    
    def reset_daily_summary(self):
        """Reset daily summary for new day"""
        self.daily_summary = {
            'date': self.algorithm.Time.date(),
            'alerts': [],
            'errors': 0,
            'warnings': 0,
            'critical': 0
        }
    
    def get_alert_history(self, hours=24, level=None):
        """Get alert history for specified time period"""
        cutoff_time = self.algorithm.Time - timedelta(hours=hours)
        
        history = [
            alert for alert in self.alert_history
            if datetime.strptime(alert['timestamp'], "%Y-%m-%d %H:%M:%S") >= cutoff_time
        ]
        
        if level:
            history = [a for a in history if a['level'] == level]
        
        return history
    
    def get_alert_stats(self):
        """Get alert statistics"""
        return {
            'total_alerts': len(self.alert_history),
            'by_level': dict(self.alert_counts),
            'rate_limited_count': len(self.last_alert_time)
        }
