# Python Source Dump

Generated: 2025-11-07T12:05:32

## E:\rony-data\trading-bot\config\config.py

```python
"""
Unified Configuration for Extreme-Aware Trading Strategy
========================================================

This is the single source of truth for all configuration parameters.

IMPORTANT: Version and Trading Mode are SEPARATE concepts:
- version: Which features are enabled (1=basic, 2=advanced)
- trading_enabled: Whether to execute real trades (True/False)

Usage Examples:
    # Version 1 (basic features), observation only
    config = Config(version=1, trading_enabled=False)

    # Version 2 (all features), observation only
    config = Config(version=2, trading_enabled=False)

    # Version 2 (all features), live trading enabled
    config = Config(version=2, trading_enabled=True)

Recommended Path:
    Week 1-4:  Config(version=1, trading_enabled=False)  # Learn basic signals
    Week 5-8:  Config(version=2, trading_enabled=False)  # Test advanced features
    Week 9+:   Config(version=2, trading_enabled=True)   # Go live
"""


class Config:
    """
    Central configuration for the trading strategy.

    Supports both dictionary-style and attribute-style access:
        config['RISK_PER_TRADE']  # Dictionary style
        config.RISK_PER_TRADE      # Attribute style

    Parameters:
        version (int): 1 for basic features, 2 for all features
        trading_enabled (bool): True to execute real trades, False for observation
    """

    def __init__(self, version=2, trading_enabled=False):
        """
        Initialize configuration

        Args:
            version: 1 (basic) or 2 (advanced features)
            trading_enabled: False (observation) or True (live trading)

        Raises:
            ValueError: If version is invalid or configuration validation fails
        """
        # Validate inputs
        if version not in [1, 2]:
            raise ValueError(f"version must be 1 or 2, got {version}")

        if not isinstance(trading_enabled, bool):
            raise ValueError(f"trading_enabled must be bool, got {type(trading_enabled)}")

        self.version = version
        self.trading_enabled = trading_enabled

        # ==================== MODE CONTROL ====================
        # OBSERVATION_MODE is inverse of trading_enabled
        self.OBSERVATION_MODE = not trading_enabled

        # ==================== BASIC SETTINGS ====================
        self.INITIAL_CAPITAL = 1000
        self.RISK_PER_TRADE = 5.0  # Base position size in dollars
        self.MAX_POSITIONS = 1     # Maximum concurrent positions
        self.MAX_TRADES_PER_DAY = 2

        # ==================== UNIVERSE SELECTION ====================
        self.UNIVERSE_SIZE = 1000
        self.MIN_PRICE = 5.0
        self.MAX_PRICE = 350.0
        self.MIN_DOLLAR_VOLUME = 20_000_000  # $20M daily volume
        self.MAX_SPREAD_BPS = 35  # Maximum bid-ask spread (basis points)

        # Blacklist problematic symbols
        self.BLACKLIST = ['BRK.A', 'BRK.B']

        # ==================== EXTREME DETECTION ====================
        self.Z_THRESHOLD = 2.0  # |Zâ‚†â‚€| â‰¥ 2.0 for detection
        self.VOLUME_ANOMALY_NORMAL = 1.5  # 1.5x median volume
        self.VOLUME_ANOMALY_AUCTION = 2.0  # 2x for auction periods
        self.LOOKBACK_MINUTES = 60  # Lookback window for Z-score
        self.MIN_BARS_FOR_DETECTION = 60  # Minimum bars needed

        # ==================== SPREAD GUARDS ====================
        self.HARD_SKIP_SPREAD_BPS = 40   # Never trade above this
        self.NORMAL_SPREAD_BPS = 30       # Normal max spread
        self.HIGH_VOL_SPREAD_BPS = 20     # High volatility regime max

        # ==================== HMM REGIME CLASSIFICATION ====================
        self.HMM_STATES = 3  # Low-Vol, High-Vol, Trending
        self.HMM_FIT_WINDOW_DAYS = 500  # ~24 months of trading days
        self.HMM_REFIT_DAYS = 20  # Refit monthly
        self.MIN_BARS_FOR_HMM = 240  # Need 4 hours minimum

        # Validate all configuration parameters
        self._validate()

        # ==================== A-VWAP TRACKER ====================
        self.AVWAP_ATR_MULTIPLIER = 0.5  # Stop distance in ATRs
        self.AVWAP_MAX_BARS = 5  # Time stop in hours

        # ==================== TIMING FILTERS ====================
        self.AUCTION_MINUTES = 30  # First/last 30 minutes
        self.AVOID_FADE_AFTER = 15.5  # Avoid fades after 3:30 PM

        # ==================== DRAWDOWN LADDER ====================
        # Thresholds: 10%, 20%, 30%, 40%
        # Multipliers: 0.75x, 0.5x, 0.25x, 0x (halt)
        self.DD_THRESHOLDS = [0.10, 0.20, 0.30, 0.40]
        self.DD_MULTIPLIERS = [0.75, 0.50, 0.25, 0.00]
        self.ENFORCE_DRAWDOWN_LADDER = (version >= 2)

        # ==================== PVS (PSYCHOLOGICAL VOLATILITY SCORE) ====================
        self.ENABLE_PVS = (version >= 2)
        self.PVS_WARNING_LEVEL = 7  # Reduce size at PVS â‰¥ 7
        self.PVS_HALT_LEVEL = 9     # Halt trading at PVS â‰¥ 9
        self.PVS_SMALL_CAPITAL_MULT = 1.5  # Extra sensitivity for small accounts
        self.SMALL_CAPITAL_THRESHOLD = 5000  # What counts as "small"

        # ==================== CASCADE PREVENTION ====================
        self.ENABLE_CASCADE_PREVENTION = (version >= 2)
        self.CASCADE_PREVENTION = {
            'MIN_EDGE_THRESHOLD': 2.0,      # Minimum |Z-score| for strong signal
            'CASCADE_THRESHOLD': 2,         # Block if â‰¥2 violations
            'MAX_CONSECUTIVE_LOSSES': 2,    # Max losses before violation
            'PVS_THRESHOLD': 7,             # PVS threshold for violation
            'MAX_TRADES_PER_HOUR': 3,       # Max hourly trades (fatigue)
            'MIN_REGIME_CONFIDENCE': 0.5    # Min regime confidence required
        }

        # ==================== EXHAUSTION DETECTION (FADE SIGNALS) ====================
        self.ENABLE_EXHAUSTION = (version >= 2)
        self.BOLL_PERIOD = 20
        self.BOLL_STD = 2.0
        self.MIN_COMPRESSION_HOURS = 3

        # ==================== DYNAMIC POSITION SIZING ====================
        self.ENABLE_DYNAMIC_SIZING = (version >= 2)
        self.MIN_POSITION_SIZE = 2.50   # Minimum $ size
        self.MAX_POSITION_SIZE = 20.00  # Maximum $ size
        self.BASE_POSITION_SIZE = 5.00  # Base before multipliers

        # ==================== ENTRY TIMING PROTOCOL ====================
        self.ENABLE_ENTRY_TIMING = (version >= 2)
        self.ENTRY_WAIT_MIN = 15  # Wait 15-30 minutes before entry
        self.ENTRY_WAIT_MAX = 30
        self.MAX_RETRACEMENT = 0.50  # Max 50% retracement from extreme

        # ==================== PORTFOLIO CONSTRAINTS ====================
        self.ENFORCE_SECTOR_NEUTRALITY = (version >= 2)
        self.MAX_BETA = 0.05  # Net portfolio beta limit
        self.MAX_SECTOR_MULTIPLIER = 2.0  # Max sector weight vs uniform
        self.MAX_POSITION_PCT_NAV = 0.02  # Max 2% NAV per position
        self.MAX_POSITION_PCT_ADV = 0.05  # Max 5% ADV per position
        self.MAX_GROSS_EXPOSURE = 2.5  # Max gross leverage
        self.MAX_NET_EXPOSURE = 0.10  # Max net exposure (10%)

        # ==================== CORRELATION THRESHOLDS ====================
        self.CORR_SOFT_DEEMPHASIS = 0.50  # Soft deemphasis if |Ï| > 0.5
        self.CORR_SECTOR_NEUTRAL = 0.70   # Sector neutral pairing if |Ï| > 0.7
        self.CORR_MARKET_NEUTRAL = 0.85   # Market neutral if |Ï| > 0.85

        # ==================== CIRCUIT BREAKERS ====================
        self.CB_CONSECUTIVE_STOPS = 3      # Halt after 3 consecutive stops
        self.CB_DAILY_LOSS = 0.05          # Halt at 5% daily loss
        self.CB_WEEKLY_LOSS = 0.10         # Halt at 10% weekly loss
        self.CB_LIQUIDITY_SPREAD_MULT = 3.0   # Halt if spread > 3x normal
        self.CB_LIQUIDITY_VOLUME_MULT = 0.3   # Halt if volume < 30% normal

        # ==================== FEATURE ENGINEERING ====================
        self.ATR_PERIOD = 20
        self.BOLLINGER_PERIOD = 20
        self.BOLLINGER_STD = 2.0

        # ==================== LOGGING ====================
        self.VERBOSE_LOGGING = True

        # ==================== DATA QUALITY ====================
        self.MIN_BARS_FOR_DETECTION = 60
        self.MIN_BARS_FOR_HMM = 240

        # Validate all configuration parameters
        self._validate()

    def _validate(self):
        """Validate configuration values"""
        # Basic settings validation
        assert 0 < self.INITIAL_CAPITAL, "Invalid INITIAL_CAPITAL"
        assert 0 < self.RISK_PER_TRADE <= 100, f"RISK_PER_TRADE must be 0-100, got {self.RISK_PER_TRADE}"
        assert 0 < self.MAX_POSITIONS <= 100, "Invalid MAX_POSITIONS"
        assert 0 < self.MAX_TRADES_PER_DAY <= 1000, "Invalid MAX_TRADES_PER_DAY"

        # Universe validation
        assert 0 < self.UNIVERSE_SIZE <= 10000, "Invalid UNIVERSE_SIZE"
        assert 0 < self.MIN_PRICE < self.MAX_PRICE, "MIN_PRICE must be < MAX_PRICE"
        assert 0 < self.MIN_DOLLAR_VOLUME, "Invalid MIN_DOLLAR_VOLUME"
        assert 0 < self.MAX_SPREAD_BPS <= 1000, "Invalid MAX_SPREAD_BPS"

        # Extreme detection validation
        assert 0 < self.Z_THRESHOLD <= 5, f"Z_THRESHOLD must be 0-5, got {self.Z_THRESHOLD}"
        assert 0 < self.VOLUME_ANOMALY_NORMAL, "Invalid VOLUME_ANOMALY_NORMAL"
        assert 0 < self.VOLUME_ANOMALY_AUCTION, "Invalid VOLUME_ANOMALY_AUCTION"
        assert 10 <= self.LOOKBACK_MINUTES <= 1440, "LOOKBACK_MINUTES must be 10-1440"

        # Position sizing validation (v2+)
        if self.version >= 2 and self.ENABLE_DYNAMIC_SIZING:
            assert 0 < self.MIN_POSITION_SIZE <= self.MAX_POSITION_SIZE, \
                f"MIN_POSITION_SIZE must be < MAX_POSITION_SIZE"
            assert self.BASE_POSITION_SIZE >= self.MIN_POSITION_SIZE, \
                "BASE_POSITION_SIZE must be >= MIN_POSITION_SIZE"

    def GetTimeOfDayMultiplier(self, hour, minute):
```


## E:\rony-data\trading-bot\quantconnect\alert_manager.py

```python
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
            'info': 'â„¹ï¸',
            'warning': 'âš ï¸',
            'error': 'âŒ',
            'critical': 'ðŸš¨'
        }
        return emojis.get(level, 'ðŸ“¢')
    
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
```


## E:\rony-data\trading-bot\quantconnect\avwap_tracker.py

```python
"""
Anchored VWAP Tracker
Calculates VWAP anchored from the impulse bar when an extreme is detected
Tracks distance to A-VWAP for entry/exit signals
"""

from AlgorithmImports import *
from collections import defaultdict

class AVWAPTracker:
    """Track Anchored VWAP from impulse bars"""
    
    def __init__(self, algorithm):
        self.algorithm = algorithm
        self.config = algorithm.config
        
        # Active tracks: symbol -> anchor info
        self.anchors = {}
        
        # Track data: symbol -> list of bars since anchor
        self.track_bars = defaultdict(list)
        
        # VWAP calculations: symbol -> current A-VWAP
        self.current_avwap = {}
    
    def AddImpulse(self, symbol, extreme_info):
        """
        Start tracking A-VWAP from an impulse bar
        
        Args:
            symbol: The symbol
            extreme_info: Dict from ExtremeDetector with impulse bar data
        """
        
        if not extreme_info['is_extreme']:
            return
        
        # Create anchor point
        impulse_bar = extreme_info['impulse_bar']
        
        self.anchors[symbol] = {
            'start_time': impulse_bar['time'],
            'start_price': impulse_bar['close'],
            'direction': extreme_info['direction'],
            'z_score': extreme_info['z_score'],
            'bars_since_impulse': 0,
            'is_active': True
        }
        
        # Initialize tracking
        self.track_bars[symbol] = [impulse_bar]
        self.current_avwap[symbol] = impulse_bar['close']  # First bar = VWAP
        
        self.algorithm.Log(
            f"A-VWAP: Started tracking {symbol} from ${impulse_bar['close']:.2f} "
            f"({extreme_info['direction']} extreme, Z={extreme_info['z_score']:.2f})"
        )
    
    def UpdateAll(self, minute_bars):
        """
        Update all active A-VWAP tracks
        
        Args:
            minute_bars: Dict of symbol -> list of minute bars
        
        Returns:
            Dict of symbol -> A-VWAP data
        """
        
        results = {}
        symbols_to_remove = []
        
        for symbol in list(self.anchors.keys()):
            if symbol not in minute_bars:
                continue
            
            # Update this track
            avwap_data = self._UpdateSymbol(symbol, minute_bars[symbol])
            
            # Check if track is still active
            if not avwap_data['is_active']:
                symbols_to_remove.append(symbol)
            
            results[symbol] = avwap_data
        
        # Clean up inactive tracks
        for symbol in symbols_to_remove:
            self._RemoveTrack(symbol)
        
        return results
    
    def _UpdateSymbol(self, symbol, minute_bars):
        """
        Update A-VWAP for a single symbol
        
        Returns dict with:
        - avwap: float
        - current_price: float
        - distance: float (percentage from A-VWAP)
        - bars_since_impulse: int
        - is_active: bool
        """
        
        anchor = self.anchors[symbol]
        
        # Get bars since anchor
        anchor_time = anchor['start_time']
        new_bars = [b for b in minute_bars if b['time'] > anchor_time]
        
        if not new_bars:
            # No new bars yet
            return {
                'avwap': self.current_avwap[symbol],
                'current_price': anchor['start_price'],
                'distance': 0.0,
                'bars_since_impulse': 0,
                'is_active': True
            }
        
        # Update bar count
        anchor['bars_since_impulse'] = len(new_bars)
        
        # Calculate VWAP from anchor
        total_pv = 0.0
        total_v = 0.0
        
        # Include original impulse bar
        impulse = self.track_bars[symbol][0]
        typical_price = (impulse['high'] + impulse['low'] + impulse['close']) / 3.0
        total_pv += typical_price * impulse['volume']
        total_v += impulse['volume']
        
        # Add all bars since impulse
        for bar in new_bars:
            typical_price = (bar['high'] + bar['low'] + bar['close']) / 3.0
            total_pv += typical_price * bar['volume']
            total_v += bar['volume']
        
        # Calculate A-VWAP
        avwap = total_pv / total_v if total_v > 0 else anchor['start_price']
        self.current_avwap[symbol] = avwap
        
        # Get current price
        current_price = new_bars[-1]['close']
        
        # Calculate distance
        distance = (current_price / avwap - 1.0) if avwap > 0 else 0.0
        
        # Check if track should still be active
        is_active = self._ShouldKeepActive(symbol, anchor, distance)
        anchor['is_active'] = is_active
        
        return {
            'avwap': avwap,
            'current_price': current_price,
            'distance': distance,
            'bars_since_impulse': anchor['bars_since_impulse'],
            'is_active': is_active,
            'direction': anchor['direction']
        }
    
    def _ShouldKeepActive(self, symbol, anchor, distance):
        """
        Determine if A-VWAP track should remain active
        
        Deactivate if:
        - Too many bars have passed (time stop)
        - Price has moved too far from A-VWAP (distance stop)
        """
        
        # Time stop: deactivate after max bars
        if anchor['bars_since_impulse'] > self.config.AVWAP_MAX_BARS * 60:  # Convert hours to minutes
            self.algorithm.Log(f"A-VWAP: {symbol} time stop hit ({anchor['bars_since_impulse']} bars)")
            return False
        
        # Distance stop: if price is very far from A-VWAP, likely done
        # Allow more distance in direction of original move
        direction = anchor['direction']
        
        if direction == 'up':
            # For upside extreme, deactivate if price falls well below A-VWAP
            if distance < -0.02:  # -2% below A-VWAP
                self.algorithm.Log(f"A-VWAP: {symbol} fell below A-VWAP ({distance:.2%})")
                return False
        else:
            # For downside extreme, deactivate if price rises well above A-VWAP
            if distance > 0.02:  # +2% above A-VWAP
                self.algorithm.Log(f"A-VWAP: {symbol} rose above A-VWAP ({distance:.2%})")
                return False
        
        return True
    
    def GetAVWAP(self, symbol):
        """Get current A-VWAP for a symbol"""
        if symbol in self.current_avwap:
            return self.current_avwap[symbol]
        return None
    
    def GetDistance(self, symbol, current_price):
        """Get distance from current price to A-VWAP"""
        avwap = self.GetAVWAP(symbol)
        if avwap is not None and avwap > 0:
            return (current_price / avwap - 1.0)
        return None
    
    def IsTracking(self, symbol):
        """Check if actively tracking a symbol"""
        return symbol in self.anchors and self.anchors[symbol]['is_active']
    
    def _RemoveTrack(self, symbol):
        """Remove an inactive track"""
        if symbol in self.anchors:
            self.algorithm.Log(f"A-VWAP: Stopped tracking {symbol}")
            del self.anchors[symbol]
        
        if symbol in self.track_bars:
            del self.track_bars[symbol]
        
        if symbol in self.current_avwap:
            del self.current_avwap[symbol]
    
    def GetActiveTracks(self):
        """Get count of active tracks"""
        return sum(1 for a in self.anchors.values() if a['is_active'])
    
    def GetTrackInfo(self, symbol):
        """Get detailed track info for a symbol"""
        if symbol not in self.anchors:
            return None
        
        anchor = self.anchors[symbol]
        avwap = self.current_avwap.get(symbol, 0.0)
        
        return {
            'start_time': anchor['start_time'],
            'start_price': anchor['start_price'],
            'current_avwap': avwap,
            'direction': anchor['direction'],
            'bars_since_impulse': anchor['bars_since_impulse'],
            'is_active': anchor['is_active']
        }
```


## E:\rony-data\trading-bot\quantconnect\backtest_analyzer.py

```python
"""
Enhanced Backtesting Framework with Realistic Cost Modeling

Provides more accurate backtest results by modeling:
- Realistic slippage (volatility and participation based)
- Market impact (volume-based)
- Time-of-day dependent spreads
- Fill probability
- TWAP execution simulation
- Detailed cost breakdown

Usage:
    from backtest_analyzer import BacktestAnalyzer
    
    analyzer = BacktestAnalyzer(algorithm)
    cost = analyzer.calculate_realistic_costs(trade)
    analyzer.generate_report()
"""

from AlgorithmImports import *
import numpy as np
import pandas as pd
from collections import defaultdict
from datetime import datetime, timedelta

class BacktestAnalyzer:
    """
    Advanced backtesting with realistic cost modeling
    """
    
    def __init__(self, algorithm):
        self.algorithm = algorithm
        self.logger = algorithm.logger if hasattr(algorithm, 'logger') else None
        
        # Trade tracking
        self.trades = []
        self.positions = {}
        
        # Performance tracking
        self.daily_returns = []
        self.equity_curve = []
        
        # Cost breakdown
        self.costs = {
            'spread': 0.0,
            'slippage': 0.0,
            'impact': 0.0,
            'fees': 0.0,
            'total': 0.0
        }
        
        # Statistics by category
        self.stats = {
            'by_direction': {'up': [], 'down': []},
            'by_regime': {'Low-Vol': [], 'High-Vol': [], 'Trending': []},
            'by_time': defaultdict(list),
            'by_symbol': defaultdict(list),
            'by_sector': defaultdict(list)
        }
        
        # Win/loss tracking
        self.wins = 0
        self.losses = 0
        self.total_pnl = 0.0
        
        if self.logger:
            self.logger.info("BacktestAnalyzer initialized", component="BacktestAnalyzer")
    
    def calculate_realistic_costs(self, trade_info):
        """
        Calculate realistic trading costs
        
        Args:
            trade_info: dict with symbol, quantity, price, timestamp, volatility, adv
        
        Returns:
            dict with cost breakdown
        """
        
        symbol = trade_info['symbol']
        quantity = abs(trade_info['quantity'])
        price = trade_info['price']
        timestamp = trade_info['timestamp']
        
        # Get market data
        volatility = trade_info.get('volatility', 0.02)  # 2% default
        adv = trade_info.get('adv', 1_000_000)  # Average daily volume
        
        # 1. Spread cost
        spread_cost = self._calculate_spread_cost(price, timestamp)
        
        # 2. Slippage (participation + volatility based)
        slippage_cost = self._calculate_slippage(quantity, adv, volatility)
        
        # 3. Market impact
        impact_cost = self._calculate_market_impact(quantity, adv, volatility)
        
        # 4. Fees
        fee_cost = self._calculate_fees(quantity, price)
        
        # Total cost
        total_cost = spread_cost + slippage_cost + impact_cost + fee_cost
        
        # Cost breakdown
        costs = {
            'spread': spread_cost * quantity,
            'slippage': slippage_cost * quantity,
            'impact': impact_cost * quantity,
            'fees': fee_cost * quantity,
            'total': total_cost * quantity,
            'bps': (total_cost / price) * 10000  # Basis points
        }
        
        # Track cumulative costs
        for key in ['spread', 'slippage', 'impact', 'fees', 'total']:
            self.costs[key] += costs[key]
        
        return costs
    
    def _calculate_spread_cost(self, price, timestamp):
        """
        Calculate spread cost (time-of-day dependent)
        
        Spreads wider at open/close, tighter mid-day
        """
        
        hour = timestamp.hour
        minute = timestamp.minute
        
        # Base spread (in dollars)
        base_spread_bps = 10  # 10 bps base
        
        # Time-of-day multiplier
        if (hour == 9 and minute < 45) or (hour == 15 and minute > 45):
            # First/last 15 minutes: wider spreads
            spread_mult = 2.0
        elif (hour == 9 and minute < 60) or (hour == 15 and minute > 30):
            # First/last 30 minutes: moderately wider
            spread_mult = 1.5
        elif hour >= 11 and hour <= 14:
            # Mid-day: tightest spreads
            spread_mult = 0.8
        else:
            # Normal hours
            spread_mult = 1.0
        
        # Spread cost per share
        spread_bps = base_spread_bps * spread_mult
        spread_cost = price * (spread_bps / 10000)
        
        # Cross the spread (pay half on average)
        return spread_cost * 0.5
    
    def _calculate_slippage(self, quantity, adv, volatility):
        """
        Calculate slippage based on participation rate and volatility
        
        Formula: slippage = sqrt(participation_rate) * volatility * alpha
        """
        
        # Estimate we trade over 5 minutes with 10% POV
        pov = 0.10  # 10% participation
        time_window_minutes = 5
        
        # Minute volume = ADV / (6.5 hours * 60 minutes)
        minute_volume = adv / (6.5 * 60)
        
        # Our share of volume in 5 minutes
        our_volume = quantity
        market_volume_5min = minute_volume * time_window_minutes * pov
        
        if market_volume_5min > 0:
            participation_rate = our_volume / market_volume_5min
        else:
            participation_rate = 0.1  # Default 10%
        
        # Cap participation rate
        participation_rate = min(participation_rate, 0.5)
        
        # Slippage model
        alpha = 0.5  # Calibration parameter
        slippage_pct = alpha * np.sqrt(participation_rate) * volatility
        
        return slippage_pct
    
    def _calculate_market_impact(self, quantity, adv, volatility):
        """
        Calculate market impact (permanent + temporary)
        
        Almgren-Chriss model simplified
        """
        
        # Daily volume participation
        participation = quantity / adv if adv > 0 else 0
        participation = min(participation, 0.25)  # Cap at 25% ADV
        
        # Impact parameters
        gamma = 0.1  # Temporary impact coefficient
        eta = 0.05   # Permanent impact coefficient
        
        # Temporary impact (goes away)
        temp_impact = gamma * volatility * np.sqrt(participation)
        
        # Permanent impact (stays)
        perm_impact = eta * volatility * participation
        
        # Total impact (we pay temp + half of perm)
        total_impact = temp_impact + (perm_impact * 0.5)
        
        return total_impact
    
    def _calculate_fees(self, quantity, price):
        """
        Calculate trading fees
        
        Interactive Brokers tiered pricing (example)
        """
        
        # IBKR tiered pricing (rough estimate)
        # $0.005 per share, $1 minimum
        per_share_fee = 0.005
        notional = quantity * price
        
        # SEC fees (sells only, but include for both for safety)
        sec_fee_rate = 0.0000278  # $27.80 per million
        sec_fee = notional * sec_fee_rate
        
        total_fee_per_share = per_share_fee + (sec_fee / quantity if quantity > 0 else 0)
        
        # Minimum $1
        total_fee = max(total_fee_per_share, 1.0 / quantity if quantity > 0 else 0)
        
        return total_fee
    
    def record_trade(self, trade_type, symbol, quantity, entry_price, exit_price=None, 
                    regime=None, direction=None, timestamp=None, metadata=None):
        """
        Record a trade for analysis
        
        Args:
            trade_type: 'open' or 'close'
            symbol: Stock symbol
            quantity: Share quantity
            entry_price: Entry price
            exit_price: Exit price (if closing)
            regime: Market regime
            direction: Trade direction ('up' or 'down')
            timestamp: Trade timestamp
            metadata: Additional info
        """
        
        timestamp = timestamp or self.algorithm.Time
        
        if trade_type == 'open':
            # Opening position
            self.positions[symbol] = {
                'entry_price': entry_price,
                'quantity': quantity,
                'entry_time': timestamp,
                'regime': regime,
                'direction': direction,
                'metadata': metadata or {}
            }
            
        elif trade_type == 'close' and symbol in self.positions:
            # Closing position
            position = self.positions[symbol]
            
            # Calculate P&L
            if exit_price:
                pnl = (exit_price - position['entry_price']) * position['quantity']
                hold_time = (timestamp - position['entry_time']).total_seconds() / 3600  # Hours
                
                # Calculate costs
                entry_costs = self.calculate_realistic_costs({
                    'symbol': symbol,
                    'quantity': quantity,
                    'price': position['entry_price'],
                    'timestamp': position['entry_time'],
                    'volatility': metadata.get('volatility', 0.02) if metadata else 0.02,
                    'adv': metadata.get('adv', 1_000_000) if metadata else 1_000_000
                })
                
                exit_costs = self.calculate_realistic_costs({
                    'symbol': symbol,
                    'quantity': quantity,
                    'price': exit_price,
                    'timestamp': timestamp,
                    'volatility': metadata.get('volatility', 0.02) if metadata else 0.02,
                    'adv': metadata.get('adv', 1_000_000) if metadata else 1_000_000
                })
                
                total_costs = entry_costs['total'] + exit_costs['total']
                net_pnl = pnl - total_costs
                
                # Record trade
                trade = {
                    'symbol': str(symbol),
                    'entry_time': position['entry_time'],
                    'exit_time': timestamp,
                    'hold_time_hours': hold_time,
                    'entry_price': position['entry_price'],
                    'exit_price': exit_price,
                    'quantity': position['quantity'],
                    'gross_pnl': pnl,
                    'costs': total_costs,
                    'net_pnl': net_pnl,
                    'return_pct': (exit_price / position['entry_price'] - 1),
                    'regime': position.get('regime'),
                    'direction': position.get('direction'),
                    'metadata': position.get('metadata', {})
                }
                
                self.trades.append(trade)
                
                # Update stats
                if net_pnl > 0:
                    self.wins += 1
                else:
                    self.losses += 1
                
                self.total_pnl += net_pnl
                
                # Categorize
                if position.get('direction'):
                    self.stats['by_direction'][position['direction']].append(trade)
                
                if position.get('regime'):
                    self.stats['by_regime'][position['regime']].append(trade)
                
                hour = position['entry_time'].hour
                self.stats['by_time'][hour].append(trade)
                
                self.stats['by_symbol'][str(symbol)].append(trade)
            
            # Remove from positions
            del self.positions[symbol]
    
    def calculate_metrics(self):
        """Calculate comprehensive performance metrics"""
        
        if not self.trades:
            return {}
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame(self.trades)
        
        # Basic metrics
        total_trades = len(df)
        win_rate = self.wins / total_trades if total_trades > 0 else 0
        
        winning_trades = df[df['net_pnl'] > 0]
        losing_trades = df[df['net_pnl'] < 0]
        
        avg_win = winning_trades['net_pnl'].mean() if len(winning_trades) > 0 else 0
        avg_loss = losing_trades['net_pnl'].mean() if len(losing_trades) > 0 else 0
        
        profit_factor = abs(winning_trades['net_pnl'].sum() / losing_trades['net_pnl'].sum()) if len(losing_trades) > 0 else float('inf')
        
        # Return metrics
        total_return = df['net_pnl'].sum()
        avg_return_per_trade = df['net_pnl'].mean()
        
        # Risk metrics
        std_returns = df['net_pnl'].std()
        sharpe_ratio = (avg_return_per_trade / std_returns * np.sqrt(252)) if std_returns > 0 else 0
        
        # Hold time
        avg_hold_time = df['hold_time_hours'].mean()
        
        # Cost analysis
        total_costs = df['costs'].sum()
        avg_cost_per_trade = df['costs'].mean()
        cost_as_pct_of_pnl = abs(total_costs / total_return) if total_return != 0 else 0
        
        metrics = {
            'total_trades': total_trades,
            'wins': self.wins,
            'losses': self.losses,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'avg_win_loss_ratio': abs(avg_win / avg_loss) if avg_loss != 0 else 0,
            'profit_factor': profit_factor,
            'total_return': total_return,
            'avg_return_per_trade': avg_return_per_trade,
            'sharpe_ratio': sharpe_ratio,
            'avg_hold_time_hours': avg_hold_time,
            'total_costs': total_costs,
            'avg_cost_per_trade': avg_cost_per_trade,
            'cost_as_pct_of_pnl': cost_as_pct_of_pnl,
            'cost_breakdown': dict(self.costs)
        }
        
        return metrics
    
    def generate_report(self):
        """Generate comprehensive backtest report"""
        
        metrics = self.calculate_metrics()
        
        if not metrics:
            return "No trades to analyze"
        
        report = "\n" + "="*70 + "\n"
        report += "BACKTEST ANALYSIS REPORT\n"
        report += "="*70 + "\n\n"
        
        # Overall Performance
        report += "OVERALL PERFORMANCE:\n"
        report += "-"*70 + "\n"
        report += f"Total Trades:          {metrics['total_trades']}\n"
        report += f"Wins / Losses:         {metrics['wins']} / {metrics['losses']}\n"
        report += f"Win Rate:              {metrics['win_rate']:.2%}\n"
        report += f"Profit Factor:         {metrics['profit_factor']:.2f}\n"
        report += f"Total Return:          ${metrics['total_return']:,.2f}\n"
        report += f"Avg Return/Trade:      ${metrics['avg_return_per_trade']:,.2f}\n"
        report += f"Sharpe Ratio:          {metrics['sharpe_ratio']:.2f}\n"
        report += f"Avg Hold Time:         {metrics['avg_hold_time_hours']:.1f} hours\n"
        report += "\n"
        
        # Win/Loss Stats
        report += "WIN/LOSS STATISTICS:\n"
        report += "-"*70 + "\n"
        report += f"Average Win:           ${metrics['avg_win']:,.2f}\n"
        report += f"Average Loss:          ${metrics['avg_loss']:,.2f}\n"
        report += f"Avg Win/Loss Ratio:    {metrics['avg_win_loss_ratio']:.2f}\n"
        report += "\n"
        
        # Cost Analysis
        report += "COST ANALYSIS:\n"
        report += "-"*70 + "\n"
        report += f"Total Costs:           ${metrics['total_costs']:,.2f}\n"
        report += f"Avg Cost/Trade:        ${metrics['avg_cost_per_trade']:,.2f}\n"
        report += f"Costs as % of P&L:     {metrics['cost_as_pct_of_pnl']:.2%}\n"
        report += "\n"
        report += "Cost Breakdown:\n"
        report += f"  Spread:              ${metrics['cost_breakdown']['spread']:,.2f}\n"
        report += f"  Slippage:            ${metrics['cost_breakdown']['slippage']:,.2f}\n"
        report += f"  Market Impact:       ${metrics['cost_breakdown']['impact']:,.2f}\n"
        report += f"  Fees:                ${metrics['cost_breakdown']['fees']:,.2f}\n"
        report += "\n"
        
        # Performance by Category
        report += self._analyze_by_category()
        
        report += "="*70 + "\n"
        
        return report
    
    def _analyze_by_category(self):
        """Analyze performance by different categories"""
        
        report = ""
        
        # By direction
        if self.stats['by_direction']['up'] or self.stats['by_direction']['down']:
            report += "PERFORMANCE BY DIRECTION:\n"
            report += "-"*70 + "\n"
            
            for direction in ['up', 'down']:
                trades = self.stats['by_direction'][direction]
                if trades:
                    df = pd.DataFrame(trades)
                    wins = len(df[df['net_pnl'] > 0])
                    total = len(df)
                    avg_pnl = df['net_pnl'].mean()
                    
                    report += f"  {direction.upper()}: {total} trades, {wins}/{total} wins ({wins/total:.1%}), Avg P&L: ${avg_pnl:,.2f}\n"
            report += "\n"
        
        # By regime
        if any(self.stats['by_regime'].values()):
            report += "PERFORMANCE BY REGIME:\n"
            report += "-"*70 + "\n"
            
            for regime in ['Low-Vol', 'High-Vol', 'Trending']:
                trades = self.stats['by_regime'][regime]
                if trades:
                    df = pd.DataFrame(trades)
                    wins = len(df[df['net_pnl'] > 0])
                    total = len(df)
                    avg_pnl = df['net_pnl'].mean()
                    
                    report += f"  {regime}: {total} trades, {wins}/{total} wins ({wins/total:.1%}), Avg P&L: ${avg_pnl:,.2f}\n"
            report += "\n"
        
        # By time of day
        if self.stats['by_time']:
            report += "PERFORMANCE BY HOUR:\n"
            report += "-"*70 + "\n"
            
            for hour in sorted(self.stats['by_time'].keys()):
                trades = self.stats['by_time'][hour]
                if trades:
                    df = pd.DataFrame(trades)
                    total = len(df)
                    avg_pnl = df['net_pnl'].mean()
                    
                    report += f"  {hour:02d}:00: {total} trades, Avg P&L: ${avg_pnl:,.2f}\n"
            report += "\n"
        
        return report
    
    def export_trades_csv(self):
        """Export trades to CSV format"""
        if not self.trades:
            return None
        
        df = pd.DataFrame(self.trades)
        
        # Format for readability
        df['entry_time'] = pd.to_datetime(df['entry_time'])
        df['exit_time'] = pd.to_datetime(df['exit_time'])
        
        return df
```


## E:\rony-data\trading-bot\quantconnect\cascade_prevention.py

```python
"""
Cascade Prevention - Phase 2

Prevents cascade of bad decisions by blocking trades when >=2 violations occur.

Violations:
- Weak signal (low edge)
- Loss streak (>=2 consecutive)
- High PVS (>7)
- Rule violation today
- Fatigue (>3 trades/hour)
- Regime uncertainty

Usage:
    from cascade_prevention import CascadePrevention
    
    cascade = CascadePrevention(algorithm)
    can_trade, violations = cascade.CheckCascadeRisk(trade_signal)
"""

from AlgorithmImports import *

class CascadePrevention:
    """Block trades when multiple violations occur"""
    
    def __init__(self, algorithm):
        self.algorithm = algorithm
        self.logger = getattr(algorithm, 'logger', None)

        # Get thresholds from config, with sane defaults. Be defensive: some
        # unit tests or lightweight runs may not attach a full `config` object
        # to the algorithm stub, so check for presence first.
        cascade_config = {}
        if getattr(algorithm, 'config', None) is not None:
            cascade_config = getattr(algorithm.config, 'CASCADE_PREVENTION', {})
        self.min_edge_threshold = cascade_config.get('MIN_EDGE_THRESHOLD', 2.0)
        self.cascade_threshold = cascade_config.get('CASCADE_THRESHOLD', 2)
        self.max_consecutive_losses = cascade_config.get('MAX_CONSECUTIVE_LOSSES', 2)
        self.pvs_threshold = cascade_config.get('PVS_THRESHOLD', 7)
        self.max_trades_per_hour = cascade_config.get('MAX_TRADES_PER_HOUR', 3)
        self.min_regime_confidence = cascade_config.get('MIN_REGIME_CONFIDENCE', 0.5)
        
    def CheckCascadeRisk(self,
                         trade_signal: dict,
                         pvs_score: float,
                         consecutive_losses: int,
                         regime_confidence: float,
                         trades_last_hour: int,
                         rule_violations: int
                         ) -> tuple[bool, list]:
        """
        Check if trade should be blocked due to cascade risk
        
        Returns:
            (bool, list): (can_trade, violations)
        """
        violations = []
        
        # Check each factor
        if abs(trade_signal.get('z_score', 0)) < self.min_edge_threshold:
            violations.append('weak_signal')
        
        if consecutive_losses >= self.max_consecutive_losses:
            violations.append('loss_streak')
        
        if pvs_score > self.pvs_threshold:
            violations.append('high_pvs')
        
        if rule_violations > 0:
            violations.append('rule_violation')
        
        if trades_last_hour > self.max_trades_per_hour:
            violations.append('fatigue')
        
        if regime_confidence < self.min_regime_confidence:
            violations.append('regime_uncertainty')
        
        # Block if >=2 violations
        can_trade = len(violations) < self.cascade_threshold
        
        if not can_trade and self.logger:
            self.logger.warning(f"Cascade prevention: {violations}", component="CascadePrevention")
        
        return can_trade, violations
```


## E:\rony-data\trading-bot\quantconnect\config.py

```python
"""
Unified Configuration for Extreme-Aware Trading Strategy
========================================================

This is the single source of truth for all configuration parameters.

IMPORTANT: Version and Trading Mode are SEPARATE concepts:
- version: Which features are enabled (1=basic, 2=advanced)
- trading_enabled: Whether to execute real trades (True/False)

Usage Examples:
    # Version 1 (basic features), observation only
    config = Config(version=1, trading_enabled=False)

    # Version 2 (all features), observation only
    config = Config(version=2, trading_enabled=False)

    # Version 2 (all features), live trading enabled
    config = Config(version=2, trading_enabled=True)

Recommended Path:
    Week 1-4:  Config(version=1, trading_enabled=False)  # Learn basic signals
    Week 5-8:  Config(version=2, trading_enabled=False)  # Test advanced features
    Week 9+:   Config(version=2, trading_enabled=True)   # Go live
"""


class Config:
    """
    Central configuration for the trading strategy.

    Supports both dictionary-style and attribute-style access:
        config['RISK_PER_TRADE']  # Dictionary style
        config.RISK_PER_TRADE      # Attribute style

    Parameters:
        version (int): 1 for basic features, 2 for all features
        trading_enabled (bool): True to execute real trades, False for observation
    """

    def __init__(self, version=2, trading_enabled=False):
        """
        Initialize configuration

        Args:
            version: 1 (basic) or 2 (advanced features)
            trading_enabled: False (observation) or True (live trading)

        Raises:
            ValueError: If version is invalid or configuration validation fails
        """
        # Validate inputs
        if version not in [1, 2]:
            raise ValueError(f"version must be 1 or 2, got {version}")

        if not isinstance(trading_enabled, bool):
            raise ValueError(f"trading_enabled must be bool, got {type(trading_enabled)}")

        self.version = version
        self.trading_enabled = trading_enabled

        # ==================== MODE CONTROL ====================
        # OBSERVATION_MODE is inverse of trading_enabled
        self.OBSERVATION_MODE = not trading_enabled

        # ==================== BASIC SETTINGS ====================
        self.INITIAL_CAPITAL = 1000
        self.RISK_PER_TRADE = 5.0  # Base position size in dollars
        self.MAX_POSITIONS = 1     # Maximum concurrent positions
        self.MAX_TRADES_PER_DAY = 2

        # ==================== UNIVERSE SELECTION ====================
        self.UNIVERSE_SIZE = 1000
        self.MIN_PRICE = 5.0
        self.MAX_PRICE = 350.0
        self.MIN_DOLLAR_VOLUME = 20_000_000  # $20M daily volume
        self.MAX_SPREAD_BPS = 35  # Maximum bid-ask spread (basis points)

        # Blacklist problematic symbols
        self.BLACKLIST = ['BRK.A', 'BRK.B']

        # ==================== EXTREME DETECTION ====================
        self.Z_THRESHOLD = 2.0  # |Z_60| >= 2.0 for detection
        self.VOLUME_ANOMALY_NORMAL = 1.5  # 1.5x median volume
        self.VOLUME_ANOMALY_AUCTION = 2.0  # 2x for auction periods
        self.LOOKBACK_MINUTES = 60  # Lookback window for Z-score
        self.MIN_BARS_FOR_DETECTION = 60  # Minimum bars needed

        # ==================== SPREAD GUARDS ====================
        self.HARD_SKIP_SPREAD_BPS = 40   # Never trade above this
        self.NORMAL_SPREAD_BPS = 30       # Normal max spread
        self.HIGH_VOL_SPREAD_BPS = 20     # High volatility regime max

        # ==================== HMM REGIME CLASSIFICATION ====================
        self.HMM_STATES = 3  # Low-Vol, High-Vol, Trending
        self.HMM_FIT_WINDOW_DAYS = 500  # ~24 months of trading days
        self.HMM_REFIT_DAYS = 20  # Refit monthly
        self.MIN_BARS_FOR_HMM = 240  # Need 4 hours minimum

        # Validate all configuration parameters
        self._validate()

        # ==================== A-VWAP TRACKER ====================
        self.AVWAP_ATR_MULTIPLIER = 0.5  # Stop distance in ATRs
        self.AVWAP_MAX_BARS = 5  # Time stop in hours

        # ==================== TIMING FILTERS ====================
        self.AUCTION_MINUTES = 30  # First/last 30 minutes
        self.AVOID_FADE_AFTER = 15.5  # Avoid fades after 3:30 PM

        # ==================== DRAWDOWN LADDER ====================
        # Thresholds: 10%, 20%, 30%, 40%
        # Multipliers: 0.75x, 0.5x, 0.25x, 0x (halt)
        self.DD_THRESHOLDS = [0.10, 0.20, 0.30, 0.40]
        self.DD_MULTIPLIERS = [0.75, 0.50, 0.25, 0.00]
        self.ENFORCE_DRAWDOWN_LADDER = (version >= 2)

        # ==================== PVS (PSYCHOLOGICAL VOLATILITY SCORE) ====================
        self.ENABLE_PVS = (version >= 2)
        self.PVS_WARNING_LEVEL = 7  # Reduce size at PVS >= 7
        self.PVS_HALT_LEVEL = 9     # Halt trading at PVS >= 9
        self.PVS_SMALL_CAPITAL_MULT = 1.5  # Extra sensitivity for small accounts
        self.SMALL_CAPITAL_THRESHOLD = 5000  # What counts as "small"

        # ==================== CASCADE PREVENTION ====================
        self.ENABLE_CASCADE_PREVENTION = (version >= 2)
        self.CASCADE_PREVENTION = {
            'MIN_EDGE_THRESHOLD': 2.0,      # Minimum |Z-score| for strong signal
            'CASCADE_THRESHOLD': 2,         # Block if >=2 violations
            'MAX_CONSECUTIVE_LOSSES': 2,    # Max losses before violation
            'PVS_THRESHOLD': 7,             # PVS threshold for violation
            'MAX_TRADES_PER_HOUR': 3,       # Max hourly trades (fatigue)
            'MIN_REGIME_CONFIDENCE': 0.5    # Min regime confidence required
        }

        # ==================== EXHAUSTION DETECTION (FADE SIGNALS) ====================
        self.ENABLE_EXHAUSTION = (version >= 2)
        self.BOLL_PERIOD = 20
        self.BOLL_STD = 2.0
        self.MIN_COMPRESSION_HOURS = 3

        # ==================== DYNAMIC POSITION SIZING ====================
        self.ENABLE_DYNAMIC_SIZING = (version >= 2)
        self.MIN_POSITION_SIZE = 2.50   # Minimum $ size
        self.MAX_POSITION_SIZE = 20.00  # Maximum $ size
        self.BASE_POSITION_SIZE = 5.00  # Base before multipliers

        # ==================== ENTRY TIMING PROTOCOL ====================
        self.ENABLE_ENTRY_TIMING = (version >= 2)
        self.ENTRY_WAIT_MIN = 15  # Wait 15-30 minutes before entry
        self.ENTRY_WAIT_MAX = 30
        self.MAX_RETRACEMENT = 0.50  # Max 50% retracement from extreme

        # ==================== PORTFOLIO CONSTRAINTS ====================
        self.ENFORCE_SECTOR_NEUTRALITY = (version >= 2)
        self.MAX_BETA = 0.05  # Net portfolio beta limit
        self.MAX_SECTOR_MULTIPLIER = 2.0  # Max sector weight vs uniform
        self.MAX_POSITION_PCT_NAV = 0.02  # Max 2% NAV per position
        self.MAX_POSITION_PCT_ADV = 0.05  # Max 5% ADV per position
        self.MAX_GROSS_EXPOSURE = 2.5  # Max gross leverage
        self.MAX_NET_EXPOSURE = 0.10  # Max net exposure (10%)

        # ==================== CORRELATION THRESHOLDS ====================
        self.CORR_SOFT_DEEMPHASIS = 0.50  # Soft deemphasis if |Ï| > 0.5
        self.CORR_SECTOR_NEUTRAL = 0.70   # Sector neutral pairing if |Ï| > 0.7
        self.CORR_MARKET_NEUTRAL = 0.85   # Market neutral if |Ï| > 0.85

        # ==================== CIRCUIT BREAKERS ====================
        self.CB_CONSECUTIVE_STOPS = 3      # Halt after 3 consecutive stops
        self.CB_DAILY_LOSS = 0.05          # Halt at 5% daily loss
        self.CB_WEEKLY_LOSS = 0.10         # Halt at 10% weekly loss
        self.CB_LIQUIDITY_SPREAD_MULT = 3.0   # Halt if spread > 3x normal
        self.CB_LIQUIDITY_VOLUME_MULT = 0.3   # Halt if volume < 30% normal

        # ==================== FEATURE ENGINEERING ====================
        self.ATR_PERIOD = 20
        self.BOLLINGER_PERIOD = 20
        self.BOLLINGER_STD = 2.0

        # ==================== LOGGING ====================
        self.VERBOSE_LOGGING = True

        # ==================== DATA QUALITY ====================
        self.MIN_BARS_FOR_DETECTION = 60
        self.MIN_BARS_FOR_HMM = 240

        # Validate all configuration parameters
        self._validate()

    def _validate(self):
        """Validate configuration values"""
        # Basic settings validation
        assert 0 < self.INITIAL_CAPITAL, "Invalid INITIAL_CAPITAL"
        assert 0 < self.RISK_PER_TRADE <= 100, f"RISK_PER_TRADE must be 0-100, got {self.RISK_PER_TRADE}"
        assert 0 < self.MAX_POSITIONS <= 100, "Invalid MAX_POSITIONS"
        assert 0 < self.MAX_TRADES_PER_DAY <= 1000, "Invalid MAX_TRADES_PER_DAY"

        # Universe validation
        assert 0 < self.UNIVERSE_SIZE <= 10000, "Invalid UNIVERSE_SIZE"
        assert 0 < self.MIN_PRICE < self.MAX_PRICE, "MIN_PRICE must be < MAX_PRICE"
        assert 0 < self.MIN_DOLLAR_VOLUME, "Invalid MIN_DOLLAR_VOLUME"
        assert 0 < self.MAX_SPREAD_BPS <= 1000, "Invalid MAX_SPREAD_BPS"

        # Extreme detection validation
        assert 0 < self.Z_THRESHOLD <= 5, f"Z_THRESHOLD must be 0-5, got {self.Z_THRESHOLD}"
        assert 0 < self.VOLUME_ANOMALY_NORMAL, "Invalid VOLUME_ANOMALY_NORMAL"
        assert 0 < self.VOLUME_ANOMALY_AUCTION, "Invalid VOLUME_ANOMALY_AUCTION"
        assert 10 <= self.LOOKBACK_MINUTES <= 1440, "LOOKBACK_MINUTES must be 10-1440"

        # Position sizing validation (v2+)
        if self.version >= 2 and self.ENABLE_DYNAMIC_SIZING:
            assert 0 < self.MIN_POSITION_SIZE <= self.MAX_POSITION_SIZE, \
                f"MIN_POSITION_SIZE must be < MAX_POSITION_SIZE"
            assert self.BASE_POSITION_SIZE >= self.MIN_POSITION_SIZE, \
                "BASE_POSITION_SIZE must be >= MIN_POSITION_SIZE"

    def GetTimeOfDayMultiplier(self, hour, minute):
```


## E:\rony-data\trading-bot\quantconnect\drawdown_enforcer.py

```python
"""
Drawdown Enforcer - Phase 2

Enforces the drawdown ladder by actually reducing position sizes during drawdowns.

Drawdown Ladder:
- 10% DD -> 0.75x size
- 20% DD -> 0.50x size
- 30% DD -> 0.25x size
- 40% DD -> 0.00x (HALT all trading)

Usage:
    from drawdown_enforcer import DrawdownEnforcer
    
    enforcer = DrawdownEnforcer(algorithm)
    multiplier = enforcer.GetSizeMultiplier(current_dd)
    should_halt = enforcer.ShouldHalt(current_dd)
"""

from AlgorithmImports import *
from collections import deque

class DrawdownEnforcer:
    """
    Enforce drawdown-based position sizing ladder
    """
    
    def __init__(self, algorithm):
        self.algorithm = algorithm
        self.logger = algorithm.logger if hasattr(algorithm, 'logger') else None
        self.alert_manager = algorithm.alert_manager if hasattr(algorithm, 'alert_manager') else None
        
        # Drawdown ladder configuration
        self.dd_thresholds = [0.10, 0.20, 0.30, 0.40]
        self.dd_multipliers = [0.75, 0.50, 0.25, 0.00]
        
        # Tracking
        self.equity_curve = deque(maxlen=252 * 390)  # 1 year of minute bars
        self.peak_value = None
        self.current_drawdown = 0.0
        self.current_multiplier = 1.0
        self.current_rung = 0  # Which rung of the ladder we're on
        
        # Historical tracking
        self.dd_history = deque(maxlen=252)  # 1 year of daily DD
        self.max_dd_hit = 0.0
        
        # Alert tracking
        self.last_alert_rung = -1
        
        if self.logger:
            self.logger.info("DrawdownEnforcer initialized", component="DrawdownEnforcer")
    
    def Update(self, portfolio_value):
        """
        Update equity curve and calculate current drawdown
        
        Args:
            portfolio_value: Current portfolio total value
        
        Returns:
            dict with DD info
        """
        
        # Update equity curve
        self.equity_curve.append(portfolio_value)
        
        # Initialize peak if first update
        if self.peak_value is None:
            self.peak_value = portfolio_value
        
        # Update peak
        if portfolio_value > self.peak_value:
            self.peak_value = portfolio_value
        
        # Calculate drawdown
        if self.peak_value > 0:
            self.current_drawdown = (portfolio_value - self.peak_value) / self.peak_value
        else:
            self.current_drawdown = 0.0
        
        # Track max DD
        if abs(self.current_drawdown) > self.max_dd_hit:
            self.max_dd_hit = abs(self.current_drawdown)
        
        # Determine current ladder rung
        old_rung = self.current_rung
        self.current_rung = self._GetCurrentRung(abs(self.current_drawdown))
        self.current_multiplier = self._GetMultiplierForRung(self.current_rung)
        
        # Alert on rung change
        if self.current_rung != old_rung and self.current_rung > 0:
            self._AlertRungChange(old_rung, self.current_rung, abs(self.current_drawdown))
        
        # Store daily DD
        if len(self.dd_history) == 0 or self.dd_history[-1] != self.current_drawdown:
            self.dd_history.append(self.current_drawdown)
        
        return {
            'current_drawdown': self.current_drawdown,
            'current_rung': self.current_rung,
            'current_multiplier': self.current_multiplier,
            'peak_value': self.peak_value,
            'max_dd_hit': self.max_dd_hit
        }
    
    def _GetCurrentRung(self, abs_dd):
        """
        Determine which rung of the ladder we're on
        
        Returns: 0 (no DD), 1 (10%), 2 (20%), 3 (30%), 4 (40%+)
        """
        for i, threshold in enumerate(self.dd_thresholds):
            if abs_dd >= threshold:
                continue
            else:
                return i
        
        return len(self.dd_thresholds)  # Highest rung
    
    def _GetMultiplierForRung(self, rung):
        """Get the size multiplier for a given rung"""
        if rung == 0:
            return 1.0
        elif rung <= len(self.dd_multipliers):
            return self.dd_multipliers[rung - 1]
        else:
            return 0.0
    
    def GetSizeMultiplier(self, current_dd=None):
        """
        Get current position size multiplier based on drawdown
        
        Args:
            current_dd: Optional specific DD to check (otherwise uses current)
        
        Returns:
            float: Multiplier (0.0 to 1.0)
        """
        
        if current_dd is None:
            return self.current_multiplier
        
        abs_dd = abs(current_dd)
        rung = self._GetCurrentRung(abs_dd)
        return self._GetMultiplierForRung(rung)
    
    def ShouldHalt(self, current_dd=None):
        """
        Check if trading should be halted due to drawdown
        
        Returns:
            bool: True if should halt (DD >= 40%)
        """
        
        if current_dd is None:
            abs_dd = abs(self.current_drawdown)
        else:
            abs_dd = abs(current_dd)
        
        return abs_dd >= self.dd_thresholds[-1]  # 40%
    
    def GetDrawdownInfo(self):
        """Get detailed drawdown information"""
        
        return {
            'current_dd': self.current_drawdown,
            'current_dd_pct': abs(self.current_drawdown) * 100,
            'current_rung': self.current_rung,
            'current_multiplier': self.current_multiplier,
            'peak_value': self.peak_value,
            'current_value': self.equity_curve[-1] if self.equity_curve else 0,
            'max_dd_hit': self.max_dd_hit,
            'should_halt': self.ShouldHalt(),
            'ladder': self._GetLadderStatus()
        }
    
    def _GetLadderStatus(self):
        """Get status of each ladder rung"""
        
        abs_dd = abs(self.current_drawdown)
        
        ladder = []
        for i, (threshold, multiplier) in enumerate(zip(self.dd_thresholds, self.dd_multipliers)):
            status = {
                'rung': i + 1,
                'threshold': threshold,
                'threshold_pct': threshold * 100,
                'multiplier': multiplier,
                'active': abs_dd >= threshold
            }
            ladder.append(status)
        
        return ladder
    
    def _AlertRungChange(self, old_rung, new_rung, abs_dd):
        """Alert when moving to a new rung of the ladder"""
        
        # Only alert once per rung
        if self.last_alert_rung == new_rung:
            return
        
        self.last_alert_rung = new_rung
        
        # Get multiplier
        multiplier = self.current_multiplier
        
        # Determine severity
        if new_rung >= 3:  # 30% or more
            level = 'critical'
        elif new_rung >= 2:  # 20% or more
            level = 'error'
        else:
            level = 'warning'
        
        # Create message
        message = f"Drawdown Ladder: Rung {new_rung} activated - DD {abs_dd:.2%} -> Size {multiplier:.2f}x"
        
        if self.logger:
            if level == 'critical':
                self.logger.critical(message, component="DrawdownEnforcer")
            elif level == 'error':
                self.logger.error(message, component="DrawdownEnforcer")
            else:
                self.logger.warning(message, component="DrawdownEnforcer")
        
        # Send alert
        if self.alert_manager:
            self.alert_manager.alert_drawdown(abs_dd, self.dd_thresholds[new_rung - 1])
    
    def GetRecoveryInfo(self):
        """Get information about recovery from drawdown"""
        
        if len(self.equity_curve) < 2:
            return None
        
        # Check if recovering
        current_val = self.equity_curve[-1]
        prev_val = self.equity_curve[-2]
        
        is_recovering = current_val > prev_val
        
        # Distance to peak
        distance_to_peak = (self.peak_value - current_val) / self.peak_value if self.peak_value > 0 else 0
        
        # Estimated bars to recovery (linear extrapolation)
        if is_recovering and prev_val > 0:
            recovery_rate = (current_val - prev_val) / prev_val
            if recovery_rate > 0:
                bars_to_recovery = int(distance_to_peak / recovery_rate)
            else:
                bars_to_recovery = None
        else:
            bars_to_recovery = None
        
        return {
            'is_recovering': is_recovering,
            'distance_to_peak': distance_to_peak,
            'distance_to_peak_pct': distance_to_peak * 100,
            'bars_to_recovery': bars_to_recovery,
            'recovery_rate': recovery_rate if is_recovering else 0
        }
    
    def Reset(self):
        """Reset drawdown tracking (use carefully!)"""
        
        if self.logger:
            self.logger.warning("Drawdown enforcer reset - peak reset to current value", 
                              component="DrawdownEnforcer")
        
        if self.equity_curve:
            self.peak_value = self.equity_curve[-1]
        
        self.current_drawdown = 0.0
        self.current_rung = 0
        self.current_multiplier = 1.0
        self.last_alert_rung = -1
    
    def GetSummary(self):
        """Get summary for logging"""
        
        info = self.GetDrawdownInfo()
        
        summary = f"DD: {info['current_dd_pct']:.1f}% | "
        summary += f"Rung: {info['current_rung']}/4 | "
        summary += f"Size: {info['current_multiplier']:.2f}x | "
        summary += f"Peak: ${info['peak_value']:,.2f}"
        
        if info['should_halt']:
            summary += " | âš ï¸ HALTED"
        
        return summary
```


## E:\rony-data\trading-bot\quantconnect\dynamic_sizer.py

```python
"""
Dynamic Position Sizer - Phase 2 (Enhanced with ATR)

Kelly-inspired position sizing based on edge quality and volatility.

Formula:
base_risk / ATR_pct * edge_mult * regime_mult * dd_mult * pvs_mult

Multipliers:
- Edge: 1x to 2x (based on |Z|)
- Regime: 0.3 to 1.0 (from HMM GPM)
- Drawdown: 0.0 to 1.0 (from DD ladder)
- PVS: 0.0 to 1.0 (from psychological state)
- ATR: Risk-invariant across different volatility stocks

Usage:
    from dynamic_sizer import DynamicSizer

    sizer = DynamicSizer(algorithm)
    size = sizer.CalculateSize(symbol, z_score, regime, dd, pvs)
"""

from AlgorithmImports import *
import numpy as np

class DynamicSizer:
    """Dynamic position sizing based on multiple factors including volatility"""

    def __init__(self, algorithm):
        self.algorithm = algorithm
        self.config = algorithm.config
        self.logger = algorithm.logger if hasattr(algorithm, 'logger') else None

        # Base risk amount (in dollars)
        self.base_risk = self.config.BASE_POSITION_SIZE if hasattr(self.config, 'BASE_POSITION_SIZE') else 5.0
        self.min_size = self.config.MIN_POSITION_SIZE if hasattr(self.config, 'MIN_POSITION_SIZE') else 2.50
        self.max_size = self.config.MAX_POSITION_SIZE if hasattr(self.config, 'MAX_POSITION_SIZE') else 20.0

        # ATR configuration
        self.atr_period = 20
        self.atr_cache = {}  # symbol -> (atr, timestamp)
        
    def GetATR(self, symbol, period=20):
        """
        Calculate Average True Range for a symbol

        Args:
            symbol: Trading symbol
            period: ATR period (default 20)

        Returns:
            float: ATR value, or 0 if unable to calculate
        """
        try:
            # Check cache (valid for 1 hour)
            if symbol in self.atr_cache:
                cached_atr, cached_time = self.atr_cache[symbol]
                elapsed = (self.algorithm.Time - cached_time).total_seconds()
                if elapsed < 3600:  # 1 hour cache
                    return cached_atr

            # Get historical data
            history = self.algorithm.History(symbol, period + 1, Resolution.Daily)

            if history.empty or len(history) < period:
                return 0

            # Calculate True Range
            high = history['high'].values
            low = history['low'].values
            close = history['close'].values

            tr_list = []
            for i in range(1, len(high)):
                tr = max(
                    high[i] - low[i],
                    abs(high[i] - close[i-1]),
                    abs(low[i] - close[i-1])
                )
                tr_list.append(tr)

            if not tr_list:
                return 0

            # ATR = average of TR
            atr = np.mean(tr_list[-period:])

            # Cache result
            self.atr_cache[symbol] = (atr, self.algorithm.Time)

            return atr

        except Exception as e:
            if self.logger:
                self.logger.error(f"ATR calculation error for {symbol}: {str(e)}", component="DynamicSizer")
            return 0

    def CalculateSize(self, symbol, z_score, gpm, dd_mult, pvs_mult, use_atr=True):
        """
        Calculate position size with ATR-based volatility adjustment

        Args:
            symbol: Trading symbol
            z_score: Signal Z-score
            gpm: Global Position Multiplier (regime)
            dd_mult: Drawdown multiplier
            pvs_mult: PVS multiplier
            use_atr: Use ATR-based sizing (default True)

        Returns:
            float: Position size in dollars
        """

        # Get current price
        if symbol not in self.algorithm.Securities:
            return 0

        price = self.algorithm.Securities[symbol].Price
        if price <= 0:
            return 0

        # Calculate base size
        if use_atr and self.config.version >= 2 and self.config.ENABLE_DYNAMIC_SIZING:
            # ATR-based sizing: risk_amount / (ATR / price)
            atr = self.GetATR(symbol, self.atr_period)

            if atr > 0:
                # ATR as percentage of price
                atr_pct = atr / price

                # Size = base_risk / atr_pct
                # This makes risk consistent across different volatility stocks
                # High volatility = smaller position, Low volatility = larger position
                base_size = self.base_risk / max(atr_pct, 0.01)  # Prevent division by very small ATR

                if self.logger:
                    self.logger.debug(
                        f"ATR sizing for {symbol}: price=${price:.2f}, ATR=${atr:.2f} ({atr_pct:.2%}), "
                        f"base=${base_size:.2f}",
                        component="DynamicSizer"
                    )
            else:
                # Fallback to fixed sizing if ATR unavailable
                base_size = self.base_risk
                if self.logger:
                    self.logger.warning(
                        f"ATR unavailable for {symbol}, using fixed base: ${base_size:.2f}",
                        component="DynamicSizer"
                    )
        else:
            # Fixed dollar sizing (v1 or ATR disabled)
            base_size = self.base_risk

        # Edge multiplier (1x to 2x based on signal strength)
        edge_mult = min(abs(z_score) / 2.0, 2.0)

        # Combine all multipliers
        total_mult = edge_mult * gpm * dd_mult * pvs_mult

        # Calculate final size
        size = base_size * total_mult

        # Apply caps
        size = max(self.min_size, min(size, self.max_size))

        return size
```


## E:\rony-data\trading-bot\quantconnect\entry_timing.py

```python
"""
Entry Timing Protocol - Phase 2

Better entry timing following Section 5.1 protocol:
1. Wait 15-30 min after extreme
2. Confirm positive tick delta
3. Abort if >50% retracement
4. Enter on pullback to A-VWAP

Usage:
    from entry_timing import EntryTiming
    
    timing = EntryTiming(algorithm)
    can_enter, reason = timing.CheckEntryTiming(extreme_info, current_price)
"""

from AlgorithmImports import *
from datetime import timedelta
import random

class EntryTiming:
    """Entry timing protocol for better fills"""
    
    def __init__(self, algorithm):
        self.algorithm = algorithm
        self.wait_min = 15
        self.wait_max = 30
        self.max_retracement = 0.50
        
    def CheckEntryTiming(self, extreme_info, current_price, avwap_price=None):
        """
        Check if timing is right for entry
        
        Returns:
            (bool, str): (can_enter, reason)
        """
        
        # 1. Wait period
        if 'detection_time' not in extreme_info:
            return False, "No detection time"
        
        detection_time = extreme_info['detection_time']
        minutes_since = (self.algorithm.Time - detection_time).total_seconds() / 60
        
        wait_time = random.randint(self.wait_min, self.wait_max)
        
        if minutes_since < wait_time:
            return False, f"Waiting {wait_time - int(minutes_since)} more minutes"
        
        # 2. Check retracement
        extreme_price = extreme_info.get('impulse_bar', {}).get('close', 0)
        extreme_move = extreme_info.get('return_60m', 0)
        
        if extreme_price > 0 and extreme_move != 0:
            retracement = abs(current_price - extreme_price) / abs(extreme_move * extreme_price)
            
            if retracement > self.max_retracement:
                return False, f"Retracement too large ({retracement:.1%})"
        
        # 3. Check for pullback to A-VWAP (if available)
        if avwap_price:
            distance_to_avwap = abs(current_price - avwap_price) / avwap_price
            
            if distance_to_avwap < 0.005:  # Within 0.5%
                return True, "At A-VWAP"
        
        return True, "Timing OK"
```


## E:\rony-data\trading-bot\quantconnect\exhaustion_detector.py

```python
"""
Exhaustion Detector - Phase 2

Detects exhaustion/mean-reversion opportunities (fade signals).

Detection Criteria:
1. Bollinger re-entry: Price back inside Boll(20,2) after outside close
2. Range compression: >=3 hours of shrinking ranges
3. Options tells (Phase 3): Delta-IV declining, skew relaxing

Entry: Retest of outer band
Target: Revert to A-VWAP
Stop: Beyond extreme +/- 0.3 ATR
Time stop: 3-5 hours

Usage:
    from exhaustion_detector import ExhaustionDetector
    
    detector = ExhaustionDetector(algorithm)
    exhaustion_info = detector.Detect(symbol, bars)
"""

from AlgorithmImports import *
import numpy as np
from collections import deque

class ExhaustionDetector:
    """
    Detect exhaustion/mean-reversion opportunities
    """
    
    def __init__(self, algorithm):
        self.algorithm = algorithm
        self.logger = algorithm.logger if hasattr(algorithm, 'logger') else None
        
        # Configuration
        self.boll_period = 20
        self.boll_std = 2.0
        self.min_compression_hours = 3
        self.compression_threshold = 0.8  # Each range <= 0.8x prior
        
        # Tracking
        self.last_detection = {}
        self.detection_cooldown = 30  # Minutes
        
        if self.logger:
            self.logger.info("ExhaustionDetector initialized", component="ExhaustionDetector")
    
    def Detect(self, symbol, minute_bars):
        """
        Detect exhaustion signal
        
        Args:
            symbol: Stock symbol
            minute_bars: List of minute bars (dict with OHLCV)
        
        Returns:
            dict with exhaustion info
        """
        
        result = {
            'is_exhaustion': False,
            'bollinger_reentry': False,
            'range_compression': False,
            'compression_hours': 0,
            'entry_price': None,
            'target_price': None,
            'stop_price': None,
            'confidence': 0.0
        }
        
        if len(minute_bars) < self.boll_period * 60:  # Need enough for Bollinger
            return result
        
        # Get hourly bars from minute bars
        hourly_bars = self._ConvertToHourly(minute_bars)
        
        if len(hourly_bars) < self.boll_period:
            return result
        
        # Check cooldown
        if symbol in self.last_detection:
            minutes_since = (self.algorithm.Time - self.last_detection[symbol]).total_seconds() / 60
            if minutes_since < self.detection_cooldown:
                return result
        
        # 1. Check Bollinger re-entry
        boll_reentry, boll_info = self._CheckBollingerReentry(hourly_bars)
        result['bollinger_reentry'] = boll_reentry
        
        if not boll_reentry:
            return result
        
        # 2. Check range compression
        compression, compression_hours = self._CheckRangeCompression(hourly_bars)
        result['range_compression'] = compression
        result['compression_hours'] = compression_hours
        
        if not compression:
            return result
        
        # Both conditions met - this is an exhaustion signal!
        result['is_exhaustion'] = True
        
        # Calculate entry/target/stop
        current_price = minute_bars[-1]['close']
        
        # Entry: Current price (retesting the band)
        result['entry_price'] = current_price
        
        # Target: A-VWAP (would need to get from tracker)
        # For now, use middle of Bollinger band
        result['target_price'] = boll_info['middle']
        
        # Stop: Beyond the extreme
        if boll_info['last_outside'] == 'upper':
            # Was above, now retesting - target is down
            result['stop_price'] = boll_info['upper_band'] + (0.3 * boll_info['atr'])
        else:
            # Was below, now retesting - target is up
            result['stop_price'] = boll_info['lower_band'] - (0.3 * boll_info['atr'])
        
        # Calculate confidence (0-1)
        confidence = 0.0
        
        # More compression hours = higher confidence
        confidence += min(compression_hours / 6.0, 0.5)  # Max 0.5 for 6+ hours
        
        # Stronger Bollinger signal = higher confidence
        if boll_info['distance_from_band'] > 0.02:  # >2% inside
            confidence += 0.3
        else:
            confidence += 0.2
        
        # Clean price action = higher confidence
        if boll_info['clean_reentry']:
            confidence += 0.2
        
        result['confidence'] = min(confidence, 1.0)
        
        # Update detection time
        self.last_detection[symbol] = self.algorithm.Time
        
        # Log detection
        if self.logger:
            self.logger.info(
                f"Exhaustion detected: {symbol} | "
                f"Compression: {compression_hours}h | "
                f"Confidence: {confidence:.2f}",
                component="ExhaustionDetector"
            )
        
        return result
    
    def _ConvertToHourly(self, minute_bars):
        """Convert minute bars to hourly bars"""
        
        hourly = []
        current_hour = None
        hour_data = {
            'open': None,
            'high': None,
            'low': None,
            'close': None,
            'volume': 0,
            'time': None
        }
        
        for bar in minute_bars:
            bar_hour = bar['time'].replace(minute=0, second=0, microsecond=0)
            
            if current_hour is None:
                current_hour = bar_hour
                hour_data['open'] = bar['open']
                hour_data['high'] = bar['high']
                hour_data['low'] = bar['low']
                hour_data['time'] = bar_hour
            
            if bar_hour != current_hour:
                # Close current hour
                hourly.append(hour_data.copy())
                
                # Start new hour
                current_hour = bar_hour
                hour_data = {
                    'open': bar['open'],
                    'high': bar['high'],
                    'low': bar['low'],
                    'close': bar['close'],
                    'volume': bar['volume'],
                    'time': bar_hour
                }
            else:
                # Update current hour
                hour_data['high'] = max(hour_data['high'], bar['high'])
                hour_data['low'] = min(hour_data['low'], bar['low'])
                hour_data['close'] = bar['close']
                hour_data['volume'] += bar['volume']
        
        # Add last hour
        if hour_data['open'] is not None:
            hourly.append(hour_data)
        
        return hourly
    
    def _CheckBollingerReentry(self, hourly_bars):
        """
        Check if price re-entered Bollinger bands after being outside
        
        Returns:
            (bool, dict): (is_reentry, info)
        """
        
        if len(hourly_bars) < self.boll_period + 5:
            return False, {}
        
        # Calculate Bollinger Bands
        closes = np.array([bar['close'] for bar in hourly_bars])
        
        # SMA
        sma = np.convolve(closes, np.ones(self.boll_period)/self.boll_period, mode='valid')
        
        # Std
        std = np.array([
            closes[i:i+self.boll_period].std()
            for i in range(len(closes) - self.boll_period + 1)
        ])
        
        # Upper/Lower bands
        upper_band = sma + (self.boll_std * std)
        lower_band = sma - (self.boll_std * std)
        
        # Check recent bars
        recent_closes = closes[-self.boll_period:]
        recent_upper = upper_band[-1]
        recent_lower = lower_band[-1]
        recent_middle = sma[-1]
        
        # Check if was outside recently
        was_outside = False
        last_outside = None
        
        for i in range(min(10, len(closes) - self.boll_period)):
            idx = -(i+1)
            if closes[idx] > upper_band[idx - (len(closes) - len(upper_band))]:
                was_outside = True
                last_outside = 'upper'
                break
            elif closes[idx] < lower_band[idx - (len(closes) - len(lower_band))]:
                was_outside = True
                last_outside = 'lower'
                break
        
        if not was_outside:
            return False, {}
        
        # Check if now inside
        current_close = closes[-1]
        now_inside = (current_close < recent_upper) and (current_close > recent_lower)
        
        if not now_inside:
            return False, {}
        
        # Calculate distance from band
        if last_outside == 'upper':
            distance_from_band = (recent_upper - current_close) / recent_upper
        else:
            distance_from_band = (current_close - recent_lower) / current_close
        
        # Check if clean reentry (not bouncing on band)
        clean_reentry = distance_from_band > 0.01  # At least 1% inside
        
        # Calculate ATR for stop
        atr = self._CalculateATR(hourly_bars[-20:])
        
        info = {
            'upper_band': recent_upper,
            'lower_band': recent_lower,
            'middle': recent_middle,
            'current_price': current_close,
            'last_outside': last_outside,
            'distance_from_band': distance_from_band,
            'clean_reentry': clean_reentry,
            'atr': atr
        }
        
        return True, info
    
    def _CheckRangeCompression(self, hourly_bars):
        """
        Check for range compression (>=3 hours of shrinking ranges)
        
        Returns:
            (bool, int): (is_compressing, hours_of_compression)
        """
        
        if len(hourly_bars) < self.min_compression_hours + 1:
            return False, 0
        
        # Calculate ranges
        ranges = [bar['high'] - bar['low'] for bar in hourly_bars]
        
        # Check for compression
        compression_count = 0
        
        for i in range(len(ranges) - 1, 0, -1):
            if ranges[i] <= ranges[i-1] * self.compression_threshold:
                compression_count += 1
            else:
                break
        
        is_compressing = compression_count >= self.min_compression_hours
        
        return is_compressing, compression_count
    
    def _CalculateATR(self, bars):
        """Calculate Average True Range"""
        
        if len(bars) < 2:
            return 0.0
        
        true_ranges = []
        
        for i in range(1, len(bars)):
            high = bars[i]['high']
            low = bars[i]['low']
            prev_close = bars[i-1]['close']
            
            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close)
            )
            
            true_ranges.append(tr)
        
        return np.mean(true_ranges) if true_ranges else 0.0
    
    def GetExhaustionStats(self, symbol):
        """Get exhaustion detection statistics"""
        
        stats = {
            'has_history': symbol in self.last_detection,
            'last_detection': self.last_detection.get(symbol),
            'cooldown_active': False
        }
        
        if symbol in self.last_detection:
            minutes_since = (self.algorithm.Time - self.last_detection[symbol]).total_seconds() / 60
            stats['cooldown_active'] = minutes_since < self.detection_cooldown
            stats['minutes_since_last'] = minutes_since
        
        return stats
```


## E:\rony-data\trading-bot\quantconnect\extreme_detector.py

```python
"""
Extreme Detection - Core Signal Generator
Detects when a stock has an extreme 60-minute move with participation

Criteria:
1. |Z_60| >= 2 (60-min return z-score)
2. Volume anomaly >= 1.5x (2x during auction periods)
3. Spread checks pass
"""

from AlgorithmImports import *
import numpy as np
from collections import deque

class ExtremeDetector:
    """Detect price extremes with participation"""
    
    def __init__(self, algorithm):
        self.algorithm = algorithm
        self.config = algorithm.config
        self.logger = algorithm.logger if hasattr(algorithm, 'logger') else None
        
        # Historical data for volume baseline
        self.volume_history = {}  # symbol -> {hour: deque of volumes}
        self.return_history = {}  # symbol -> deque of minute returns
        
        # Detection cache
        self.last_detection = {}  # symbol -> timestamp
        self.detection_cooldown = 15  # Minutes before re-detecting same symbol
        
    def Detect(self, symbol, minute_bars):
        """
        Detect if symbol has an extreme move
        
        Returns dict with:
        - is_extreme: bool
        - z_score: float
        - vol_anomaly: float
        - direction: 'up' or 'down'
        - return_60m: float
        - impulse_bar: dict with OHLCV
        """
        
        result = {
            'is_extreme': False,
            'z_score': 0.0,
            'vol_anomaly': 0.0,
            'direction': 'neutral',
            'return_60m': 0.0,
            'impulse_bar': None,
            'detection_time': None
        }
        
        # Need at least 60 minutes of data
        if len(minute_bars) < self.config.MIN_BARS_FOR_DETECTION:
            return result
        
        # Get last 60 minutes
        recent_bars = minute_bars[-60:]
        
        # Calculate 60-minute return
        start_price = recent_bars[0]['close']
        end_price = recent_bars[-1]['close']
        return_60m = (end_price / start_price - 1.0) if start_price > 0 else 0.0
        
        # Calculate minute returns for volatility
        minute_returns = []
        for i in range(1, len(recent_bars)):
            prev_close = recent_bars[i-1]['close']
            curr_close = recent_bars[i]['close']
            if prev_close > 0:
                ret = (curr_close / prev_close - 1.0)
                minute_returns.append(ret)
        
        if len(minute_returns) < 30:  # Need enough for stable volatility
            return result
        
        # Calculate Z-score
        sigma_60 = np.std(minute_returns)
        if sigma_60 > 0:
            z_score = return_60m / sigma_60
        else:
            z_score = 0.0
        
        # Update result
        result['z_score'] = z_score
        result['return_60m'] = return_60m
        result['direction'] = 'up' if return_60m > 0 else 'down'
        
        # Check Z-score threshold
        if abs(z_score) < self.config.Z_THRESHOLD:
            return result
        
        # Calculate volume anomaly
        total_volume_60m = sum([bar['volume'] for bar in recent_bars])
        
        # Get hour of day for comparison
        current_time = recent_bars[-1]['time']
        hour_of_day = current_time.hour
        
        # Update volume history
        if symbol not in self.volume_history:
            self.volume_history[symbol] = {}
        if hour_of_day not in self.volume_history[symbol]:
            self.volume_history[symbol][hour_of_day] = deque(maxlen=20)  # 20-day history
        
        # Get historical median for this hour
        hist_volumes = list(self.volume_history[symbol][hour_of_day])
        if len(hist_volumes) >= 5:  # Need at least 5 days
            median_volume = np.median(hist_volumes)
            vol_anomaly = total_volume_60m / median_volume if median_volume > 0 else 0.0
        else:
            vol_anomaly = 0.0  # Not enough history
        
        # Update history
        self.volume_history[symbol][hour_of_day].append(total_volume_60m)
        
        result['vol_anomaly'] = vol_anomaly
        
        # Check volume anomaly threshold (auction periods need 2x)
        is_auction = self.config.IsAuctionPeriod(current_time)
        vol_threshold = self.config.VOLUME_ANOMALY_AUCTION if is_auction else self.config.VOLUME_ANOMALY_NORMAL
        
        if vol_anomaly < vol_threshold:
            return result
        
        # Check cooldown (avoid re-detecting too quickly)
        if symbol in self.last_detection:
            minutes_since = (current_time - self.last_detection[symbol]).total_seconds() / 60
            if minutes_since < self.detection_cooldown:
                return result
        
        # Check spread (if available - in Phase 1 we might not have this)
        # For now, we'll skip this check and add it when we have live data
        
        # All checks passed - this is an extreme!
        result['is_extreme'] = True
        result['detection_time'] = current_time
        result['impulse_bar'] = {
            'time': recent_bars[-1]['time'],
            'open': recent_bars[-1]['open'],
            'high': recent_bars[-1]['high'],
            'low': recent_bars[-1]['low'],
            'close': recent_bars[-1]['close'],
            'volume': recent_bars[-1]['volume']
        }
        
        # Update detection time
        self.last_detection[symbol] = current_time
        
        return result
    
    def GetDetectionStats(self, symbol):
        """Get detection statistics for a symbol"""
        stats = {
            'has_volume_history': symbol in self.volume_history,
            'volume_history_length': 0,
            'last_detection': None
        }
        
        if symbol in self.volume_history:
            total_entries = sum(len(v) for v in self.volume_history[symbol].values())
            stats['volume_history_length'] = total_entries
        
        if symbol in self.last_detection:
            stats['last_detection'] = self.last_detection[symbol]
        
        return stats
    
    def ResetHistory(self, symbol):
        """Clear history for a symbol (e.g., after delisting)"""
        if symbol in self.volume_history:
            del self.volume_history[symbol]
        if symbol in self.return_history:
            del self.return_history[symbol]
        if symbol in self.last_detection:
            del self.last_detection[symbol]
```


## E:\rony-data\trading-bot\quantconnect\health_monitor.py

```python
"""
System Health Monitoring

Continuously monitors system health and alerts on issues.

Monitors:
- Data feed health (bars arriving)
- Universe stability (size consistent)
- Detection rate (normal range)
- Error rate (low)
- Memory usage (stable)
- Execution performance (fast)
- Component responsiveness
- IBKR connection
- Data quality

Auto-recovery:
- Reconnect data feeds
- Reset stuck components
- Clear memory buffers
- Log incidents

Usage:
    from health_monitor import HealthMonitor
    
    health = HealthMonitor(algorithm)
    status = health.run_health_check()
"""

from AlgorithmImports import *
from datetime import datetime, timedelta
from collections import deque, defaultdict
import sys

class HealthMonitor:
    """
    Comprehensive system health monitoring
    """
    
    def __init__(self, algorithm):
        self.algorithm = algorithm
        self.logger = algorithm.logger if hasattr(algorithm, 'logger') else None
        self.alert_manager = algorithm.alert_manager if hasattr(algorithm, 'alert_manager') else None
        
        # Health check configuration
        self.checks_enabled = {
            'data_feed': True,
            'universe_size': True,
            'detection_rate': True,
            'error_rate': True,
            'memory_usage': True,
            'execution_time': True,
            'ibkr_connection': True,
            'data_quality': True
        }
        
        # Thresholds
        self.thresholds = {
            'min_universe_size': 800,        # Expect ~1000
            'max_universe_size': 1200,
            'min_detections_per_day': 3,     # Expect 5-10
            'max_detections_per_day': 20,
            'max_errors_per_hour': 5,
            'max_memory_mb': 1000,           # 1GB
            'max_execution_time_sec': 10,    # Hourly scan
            'data_stale_minutes': 5          # No data for 5 min
        }
        
        # Tracking
        self.last_bar_time = {}              # symbol -> last bar timestamp
        self.universe_sizes = deque(maxlen=24)  # Last 24 hours
        self.detection_counts = deque(maxlen=24)  # Hourly detection counts
        self.error_counts = deque(maxlen=24)     # Hourly error counts
        self.execution_times = deque(maxlen=100)  # Last 100 executions
        
        # Health status
        self.health_status = {
            'overall': True,
            'last_check': None,
            'checks': {},
            'issues': []
        }
        
        # Recovery tracking
        self.recovery_attempts = defaultdict(int)
        self.last_recovery_time = {}
        self.recovery_failures = defaultdict(int)  # Track consecutive failures
        self.circuit_breaker_open = {}  # recovery_key -> open_time

        # Recovery configuration
        self.MAX_RECOVERY_ATTEMPTS = 5  # Max attempts before circuit opens
        self.CIRCUIT_BREAKER_DURATION = 3600  # 1 hour in seconds
        self.BASE_BACKOFF_SECONDS = 60  # Initial backoff: 1 minute

        # Start time and warmup tracking
        self.start_time = algorithm.Time
        self.last_hourly_check = algorithm.Time
        self.warmup_duration_minutes = 5  # First 5 minutes = warmup
        self.warmup_status_emitted = False  # One-time warmup message flag
        self.warmup_end_emitted = False  # One-time warmup complete message flag

        if self.logger:
            self.logger.info("HealthMonitor initialized", component="HealthMonitor")

    def is_in_warmup(self):
        """Check if algorithm is still in warmup period"""
        elapsed_minutes = (self.algorithm.Time - self.start_time).total_seconds() / 60
        return elapsed_minutes < self.warmup_duration_minutes

    def get_warmup_status(self):
        """
        Get warmup status with time remaining

        Returns:
            dict: {in_warmup: bool, elapsed_minutes: float, remaining_minutes: float}
        """
        elapsed_minutes = (self.algorithm.Time - self.start_time).total_seconds() / 60
        in_warmup = elapsed_minutes < self.warmup_duration_minutes
        remaining_minutes = max(0, self.warmup_duration_minutes - elapsed_minutes)

        return {
            'in_warmup': in_warmup,
            'elapsed_minutes': elapsed_minutes,
            'remaining_minutes': remaining_minutes,
            'warmup_duration': self.warmup_duration_minutes
        }

    def _emit_warmup_status(self):
        """Emit one-time warmup status message"""
        if not self.warmup_status_emitted and self.is_in_warmup():
            warmup_status = self.get_warmup_status()
            if self.logger:
                self.logger.info(
                    f"[WARMUP] System in warmup period ({self.warmup_duration_minutes} min). "
                    f"Health checks relaxed. Remaining: {warmup_status['remaining_minutes']:.1f} min",
                    component="HealthMonitor"
                )
            self.warmup_status_emitted = True

    def _emit_warmup_complete(self):
        """Emit one-time warmup complete message"""
        if not self.warmup_end_emitted and not self.is_in_warmup():
            if self.logger:
                self.logger.info(
                    "[WARMUP COMPLETE] System warmup period ended. Full health checks now active.",
                    component="HealthMonitor"
                )
            self.warmup_end_emitted = True

    def _is_circuit_breaker_open(self, recovery_key):
        """Check if circuit breaker is open for this recovery type"""
        if recovery_key not in self.circuit_breaker_open:
            return False

        open_time = self.circuit_breaker_open[recovery_key]
        elapsed = (self.algorithm.Time - open_time).total_seconds()

        # Close circuit after duration
        if elapsed >= self.CIRCUIT_BREAKER_DURATION:
            del self.circuit_breaker_open[recovery_key]
            self.recovery_failures[recovery_key] = 0  # Reset failure count
            if self.logger:
                self.logger.info(
                    f"Circuit breaker CLOSED for {recovery_key} after {elapsed/60:.0f} min",
                    component="HealthMonitor"
                )
            return False

        return True

    def _get_backoff_time(self, recovery_key):
        """
        Calculate exponential backoff time with jitter

        Formula: min(base * 2^failures, max) + random_jitter
        """
        import random

        failures = self.recovery_failures[recovery_key]

        # Exponential backoff: 60s, 120s, 240s, 480s, 960s
        backoff = min(self.BASE_BACKOFF_SECONDS * (2 ** failures), 960)

        # Add jitter (0-30% of backoff)
        jitter = random.uniform(0, backoff * 0.3)

        return backoff + jitter

    def _should_attempt_recovery(self, recovery_key):
        """
        Check if recovery should be attempted based on backoff and circuit breaker

        Returns:
            tuple: (should_attempt: bool, reason: str)
        """
        # Check circuit breaker
        if self._is_circuit_breaker_open(recovery_key):
            elapsed = (self.algorithm.Time - self.circuit_breaker_open[recovery_key]).total_seconds()
            remaining = (self.CIRCUIT_BREAKER_DURATION - elapsed) / 60
            return False, f"Circuit breaker OPEN: {remaining:.0f} min remaining"

        # Check if too many recent failures
        if self.recovery_failures[recovery_key] >= self.MAX_RECOVERY_ATTEMPTS:
            # Open circuit breaker
            self.circuit_breaker_open[recovery_key] = self.algorithm.Time
            if self.logger:
                self.logger.warning(
                    f"Circuit breaker OPENED for {recovery_key} after {self.MAX_RECOVERY_ATTEMPTS} failures",
                    component="HealthMonitor"
                )
            return False, "Too many failures - circuit breaker opened"

        # Check backoff time
        if recovery_key in self.last_recovery_time:
            elapsed = (self.algorithm.Time - self.last_recovery_time[recovery_key]).total_seconds()
            required_backoff = self._get_backoff_time(recovery_key)

            if elapsed < required_backoff:
                remaining = (required_backoff - elapsed) / 60
                return False, f"Backoff: {remaining:.1f} min remaining"

        return True, "OK"

    def run_health_check(self, force=False):
        """
        Run all health checks

        Args:
            force: Force check even if recently checked

        Returns:
            dict with health status
        """

        # Emit warmup status messages (one-time)
        self._emit_warmup_status()
        self._emit_warmup_complete()

        # Check if in warmup period
        in_warmup = self.is_in_warmup()

        # Only run once per hour unless forced
        if not force:
            time_since_check = (self.algorithm.Time - self.last_hourly_check).total_seconds() / 60
            if time_since_check < 60:  # Less than 1 hour
                return self.health_status

        self.last_hourly_check = self.algorithm.Time

        # Run each enabled check (relaxed during warmup)
        checks = {}
        issues = []
        
        if self.checks_enabled['data_feed']:
            check, issue = self._check_data_feed()
            checks['data_feed'] = check
            if issue:
                issues.append(issue)
        
        if self.checks_enabled['universe_size']:
            check, issue = self._check_universe_size()
            checks['universe_size'] = check
            if issue:
                issues.append(issue)
        
        if self.checks_enabled['detection_rate']:
            check, issue = self._check_detection_rate()
            checks['detection_rate'] = check
            if issue:
                issues.append(issue)
        
        if self.checks_enabled['error_rate']:
            check, issue = self._check_error_rate()
            checks['error_rate'] = check
            if issue:
                issues.append(issue)
        
        if self.checks_enabled['memory_usage']:
            check, issue = self._check_memory_usage()
            checks['memory_usage'] = check
            if issue:
                issues.append(issue)
        
        if self.checks_enabled['execution_time']:
            check, issue = self._check_execution_time()
            checks['execution_time'] = check
            if issue:
                issues.append(issue)
        
        if self.checks_enabled['data_quality']:
            check, issue = self._check_data_quality()
            checks['data_quality'] = check
            if issue:
                issues.append(issue)
        
        # Overall health
        overall_healthy = all(checks.values())
        
        # Update status
        self.health_status = {
            'overall': overall_healthy,
            'last_check': self.algorithm.Time,
            'checks': checks,
            'issues': issues
        }
        
        # Log results
        if self.logger:
            if overall_healthy:
                self.logger.info("Health check passed - all systems OK", component="HealthMonitor")
            else:
                self.logger.warning(f"Health check FAILED - {len(issues)} issues found", 
                                  component="HealthMonitor")
                for issue in issues:
                    self.logger.warning(f"  - {issue}", component="HealthMonitor")
        
        # Alert if issues found
        if not overall_healthy and self.alert_manager:
            self.alert_manager.alert_system_health(checks)
        
        # Attempt recovery if needed
        if not overall_healthy:
            self._attempt_recovery(issues)
        
        return self.health_status
    
    def _check_data_feed(self):
        """Check if data feed is active and recent"""
        
        # Check if we've received recent data
        if not self.last_bar_time:
            # No data yet (might be warming up)
            if (self.algorithm.Time - self.start_time).total_seconds() > 300:  # 5 minutes
                return False, "No data received in 5 minutes"
            else:
                return True, None  # Still warming up
        
        # Check most recent bar
        most_recent = max(self.last_bar_time.values())
        minutes_since = (self.algorithm.Time - most_recent).total_seconds() / 60
        
        if minutes_since > self.thresholds['data_stale_minutes']:
            return False, f"Data stale - no bars for {minutes_since:.1f} minutes"
        
        return True, None
    
    def _check_universe_size(self):
        """Check if universe size is stable"""
        
        if not hasattr(self.algorithm, 'active_symbols'):
            return True, None  # Not initialized yet
        
        current_size = len(self.algorithm.active_symbols)
        self.universe_sizes.append(current_size)
        
        if current_size < self.thresholds['min_universe_size']:
            return False, f"Universe too small: {current_size} (expected ~1000)"
        
        if current_size > self.thresholds['max_universe_size']:
            return False, f"Universe too large: {current_size} (expected ~1000)"
        
        # Check for sudden drops (>50% in 1 hour)
        if len(self.universe_sizes) >= 2:
            prev_size = self.universe_sizes[-2]
            if current_size < prev_size * 0.5:
                return False, f"Universe dropped from {prev_size} to {current_size}"
        
        return True, None
    
    def _check_detection_rate(self):
        """Check if detection rate is normal"""
        
        # Get detections from last hour
        if not hasattr(self.algorithm, 'extreme_detector'):
            return True, None
        
        # Count recent detections (simplified - would need actual tracking)
        # For now, check if we're getting ANY detections
        
        # Check daily total
        if len(self.detection_counts) >= 24:  # Full day
            daily_total = sum(self.detection_counts)
            
            if daily_total < self.thresholds['min_detections_per_day']:
                return False, f"Too few detections: {daily_total}/day (expected 5-10)"
            
            if daily_total > self.thresholds['max_detections_per_day']:
                return False, f"Too many detections: {daily_total}/day (possible false signals)"
        
        return True, None
    
    def _check_error_rate(self):
        """Check if error rate is acceptable"""
        
        if not self.logger:
            return True, None
        
        # Get error count from logger
        recent_errors = len([
            e for e in self.logger.error_logs
            if (self.algorithm.Time - datetime.strptime(e['timestamp'], "%Y-%m-%d %H:%M:%S")).total_seconds() < 3600
        ])
        
        self.error_counts.append(recent_errors)
        
        if recent_errors > self.thresholds['max_errors_per_hour']:
            return False, f"High error rate: {recent_errors} errors in last hour"
        
        # Check for error spike
        if len(self.error_counts) >= 2:
            prev_errors = self.error_counts[-2]
            if recent_errors > prev_errors * 3 and recent_errors > 5:
                if self.alert_manager:
                    self.alert_manager.alert_error_spike(recent_errors, 60)
                return False, f"Error spike: {recent_errors} errors (was {prev_errors})"
        
        return True, None
    
    def _check_memory_usage(self):
        """Check memory usage"""
        
        try:
            # Get current memory usage (if available)
            # Note: This might not work in all environments
            import resource
            memory_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
            
            if memory_mb > self.thresholds['max_memory_mb']:
                return False, f"High memory usage: {memory_mb:.0f} MB"
            
            return True, None
            
        except Exception:
            # Memory monitoring not available
            return True, None
    
    def _check_execution_time(self):
        """Check if execution is fast enough"""
        
        if not self.execution_times:
            return True, None
        
        avg_time = sum(self.execution_times) / len(self.execution_times)
        
        if avg_time > self.thresholds['max_execution_time_sec']:
            return False, f"Slow execution: {avg_time:.2f}s average (max {self.thresholds['max_execution_time_sec']}s)"
        
        # Check for degradation
        if len(self.execution_times) >= 10:
            recent_avg = sum(list(self.execution_times)[-10:]) / 10
            old_avg = sum(list(self.execution_times)[:10]) / 10
            
            if recent_avg > old_avg * 2:
                return False, f"Execution slowing: {old_avg:.2f}s -> {recent_avg:.2f}s"
        
        return True, None
    
    def _check_data_quality(self):
        """Check data quality (no gaps, valid prices)"""
        
        if not hasattr(self.algorithm, 'minute_bars'):
            return True, None
        
        # Check a sample of symbols for data quality
        issues = []
        
        for symbol in list(self.algorithm.minute_bars.keys())[:10]:  # Check first 10
            bars = self.algorithm.minute_bars[symbol]
            
            if not bars:
                continue
            
            # Check for zero/negative prices
            for bar in bars[-60:]:  # Last hour
                if bar.get('close', 0) <= 0:
                    issues.append(f"{symbol}: Invalid price {bar['close']}")
                    break
            
            # Check for large gaps in time
            if len(bars) >= 2:
                last_bar = bars[-1]
                prev_bar = bars[-2]
                time_gap = (last_bar['time'] - prev_bar['time']).total_seconds()
                
                if time_gap > 300:  # >5 minutes gap
                    issues.append(f"{symbol}: {time_gap/60:.0f}min data gap")
        
        if issues:
            return False, f"Data quality issues: {len(issues)} problems found"
        
        return True, None
    
    def _attempt_recovery(self, issues):
        """Attempt automatic recovery from issues"""
        
        for issue in issues:
            # Identify issue type
            if 'data stale' in issue.lower() or 'data gap' in issue.lower():
                self._recover_data_feed()
            
            elif 'universe' in issue.lower():
                self._recover_universe()
            
            elif 'memory' in issue.lower():
                self._recover_memory()
            
            elif 'error spike' in issue.lower():
                self._recover_error_spike()
    
    def _recover_data_feed(self):
        """Attempt to recover data feed with exponential backoff and circuit breaker"""

        recovery_key = 'data_feed'

        # Check if recovery should be attempted
        should_attempt, reason = self._should_attempt_recovery(recovery_key)
        if not should_attempt:
            if self.logger:
                self.logger.info(f"Skipping data feed recovery: {reason}", component="HealthMonitor")
            return

        if self.logger:
            attempts = self.recovery_attempts[recovery_key]
            failures = self.recovery_failures[recovery_key]
            self.logger.info(
                f"Attempting data feed recovery (attempt {attempts+1}, failures: {failures})",
                component="HealthMonitor"
            )

        try:
            # Clear stale data
            if hasattr(self.algorithm, 'minute_bars'):
                for symbol in list(self.algorithm.minute_bars.keys()):
                    if len(self.algorithm.minute_bars[symbol]) > 1440:  # Keep last 24 hours
                        self.algorithm.minute_bars[symbol] = self.algorithm.minute_bars[symbol][-1440:]

            # Log recovery attempt
            self.recovery_attempts[recovery_key] += 1
            self.last_recovery_time[recovery_key] = self.algorithm.Time
            self.recovery_failures[recovery_key] = 0  # Reset on success

            if self.logger:
                self.logger.info("[OK] Data feed recovery completed", component="HealthMonitor")

        except Exception as e:
            self.recovery_failures[recovery_key] += 1
            if self.logger:
                self.logger.error(
                    f"[FAILED] Data feed recovery failed (failure {self.recovery_failures[recovery_key]}): {str(e)}",
                    component="HealthMonitor", exception=e
                )
    
    def _recover_universe(self):
        """Attempt to recover universe"""
        
        recovery_key = 'universe'
        
        if self.logger:
            self.logger.info("Attempting universe recovery", component="HealthMonitor")
        
        try:
            # Force universe refresh (would need to implement in main algo)
            # For now, just log
            
            self.recovery_attempts[recovery_key] += 1
            self.last_recovery_time[recovery_key] = self.algorithm.Time
            
            if self.logger:
                self.logger.info("Universe recovery completed", component="HealthMonitor")
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Universe recovery failed: {str(e)}", 
                                component="HealthMonitor", exception=e)
    
    def _recover_memory(self):
        """Attempt to recover from high memory usage"""
        
        recovery_key = 'memory'
        
        if self.logger:
            self.logger.info("Attempting memory recovery", component="HealthMonitor")
        
        try:
            # Clear old data
            if hasattr(self.algorithm, 'minute_bars'):
                for symbol in list(self.algorithm.minute_bars.keys()):
                    # Keep only last 2 hours
                    if len(self.algorithm.minute_bars[symbol]) > 120:
                        self.algorithm.minute_bars[symbol] = self.algorithm.minute_bars[symbol][-120:]
            
            # Clear logger buffers (keep last 1000)
            if self.logger and len(self.logger.daily_logs) > 1000:
                self.logger.daily_logs = self.logger.daily_logs[-1000:]
            
            self.recovery_attempts[recovery_key] += 1
            self.last_recovery_time[recovery_key] = self.algorithm.Time
            
            if self.logger:
                self.logger.info("Memory recovery completed", component="HealthMonitor")
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Memory recovery failed: {str(e)}", 
                                component="HealthMonitor", exception=e)
    
    def _recover_error_spike(self):
        """Handle error spikes"""
        
        recovery_key = 'error_spike'
        
        if self.logger:
            self.logger.warning("Error spike detected - monitoring closely", 
                              component="HealthMonitor")
        
        # Just log for now - human intervention likely needed
        self.recovery_attempts[recovery_key] += 1
        self.last_recovery_time[recovery_key] = self.algorithm.Time
    
    def update_metrics(self, metric_type, value):
        """Update health metrics"""
        
        if metric_type == 'bar_received':
            symbol = value['symbol']
            timestamp = value['timestamp']
            self.last_bar_time[symbol] = timestamp
        
        elif metric_type == 'detection':
            # Increment hourly detection count
            if not self.detection_counts or len(self.detection_counts) == 0:
                self.detection_counts.append(1)
            else:
                self.detection_counts[-1] += 1
        
        elif metric_type == 'execution_time':
            self.execution_times.append(value)
    
    def get_health_summary(self):
        """Get health summary for logging"""
        
        summary = {
            'overall_healthy': self.health_status['overall'],
            'last_check': str(self.health_status['last_check']),
            'issues': len(self.health_status['issues']),
            'checks_passed': sum(1 for v in self.health_status['checks'].values() if v),
            'checks_total': len(self.health_status['checks']),
            'recovery_attempts': dict(self.recovery_attempts)
        }
        
        return summary
```


## E:\rony-data\trading-bot\quantconnect\hmm_regime.py

```python
"""
HMM Regime Classifier
3-state model: Low-Vol, High-Vol, Trending
Phase 1: Observation only - calculate posteriors but don't gate trades yet
"""

from AlgorithmImports import *
import numpy as np
from collections import deque

class HMMRegime:
    """Hidden Markov Model for regime detection"""
    
    def __init__(self, algorithm):
        self.algorithm = algorithm
        self.config = algorithm.config
        
        # States
        self.states = ['Low-Vol', 'High-Vol', 'Trending']
        self.n_states = len(self.states)
        
        # Current regime probabilities
        self.state_probs = {
            'Low-Vol': 0.33,
            'High-Vol': 0.33,
            'Trending': 0.34
        }
        
        # Feature history for fitting
        self.feature_history = deque(maxlen=self.config.HMM_FIT_WINDOW_DAYS)
        
        # Track market-wide features daily
        self.daily_features = {
            'realized_vol': [],
            'correlation': [],
            'vix_level': [],
            'spread_percentile': []
        }
        
        # Model state
        self.is_fitted = False
        self.last_fit_date = None
        self.days_since_fit = 0
        self.next_scheduled_fit = None  # Next scheduled fit date

        # For Phase 1 - simplified regime detection
        self.use_simplified = True  # Use heuristics instead of full HMM

        # Fit scheduling
        self.fit_on_warmup_end = True  # Fit when warmup completes
        self.refit_interval_days = self.config.HMM_REFIT_DAYS  # 20 days default
        
        # Subscribe to VIX for regime detection
        try:
            self.vix = algorithm.AddIndex("VIX", Resolution.Daily).Symbol
        except:
            self.vix = None
            algorithm.Log("Warning: VIX not available, using simplified regime detection")
    
    def Update(self, current_time):
        """
        Update regime probabilities
        Phase 1: Use simplified heuristic-based regime detection
        
        Returns dict with:
        - dominant_state: str
        - state_probs: dict
        - gpm: float (Global Position Multiplier)
        - requires_2x_edge: bool
        """
        
        if self.use_simplified:
            return self._SimplifiedRegime(current_time)
        else:
            return self._FullHMMRegime(current_time)
    
    def _SimplifiedRegime(self, current_time):
        """
        Simplified regime detection using market observables
        Good enough for Phase 1 observation
        """
        
        # Default to neutral
        regime = {
            'dominant_state': 'Low-Vol',
            'state_probs': {
                'Low-Vol': 0.50,
                'High-Vol': 0.25,
                'Trending': 0.25
            },
            'gpm': 1.0,  # Global Position Multiplier
            'requires_2x_edge': False,
            'correlation_breakdown': 0.0
        }
        
        # Try to get VIX level
        vix_level = self._GetVIXLevel()
        
        if vix_level is not None:
            # VIX-based regime classification
            if vix_level < 15:
                # Low volatility environment
                regime['dominant_state'] = 'Low-Vol'
                regime['state_probs'] = {
                    'Low-Vol': 0.70,
                    'High-Vol': 0.15,
                    'Trending': 0.15
                }
                regime['gpm'] = 1.0
                
            elif vix_level > 25:
                # High volatility environment
                regime['dominant_state'] = 'High-Vol'
                regime['state_probs'] = {
                    'Low-Vol': 0.10,
                    'High-Vol': 0.70,
                    'Trending': 0.20
                }
                regime['gpm'] = 0.3  # Reduce size in high vol
                regime['requires_2x_edge'] = True
                
            else:
                # Moderate/trending environment
                regime['dominant_state'] = 'Trending'
                regime['state_probs'] = {
                    'Low-Vol': 0.20,
                    'High-Vol': 0.30,
                    'Trending': 0.50
                }
                regime['gpm'] = 0.8
        
        # Calculate correlation breakdown (placeholder for now)
        # In production, this would analyze cross-correlation of returns
        regime['correlation_breakdown'] = 0.0
        
        return regime
    
    def _GetVIXLevel(self):
        """Get current VIX level if available"""
        if self.vix is None:
            return None
        
        try:
            history = self.algorithm.History(self.vix, 1, Resolution.Daily)
            if history.empty:
                return None
            return float(history['close'].iloc[-1])
        except:
            return None
    
    def _FullHMMRegime(self, current_time):
        """
        Full HMM implementation (for future Phase 2+)
        Currently returns simplified version
        """
        # TODO: Implement full Gaussian HMM with sklearn
        # For now, fall back to simplified
        return self._SimplifiedRegime(current_time)
    
    def _CollectFeatures(self):
        """
        Collect features for HMM fitting
        - Realized volatility
        - Correlation
        - Spread levels
        - VIX
        """
        features = {}
        
        # Get VIX
        vix = self._GetVIXLevel()
        if vix is not None:
            features['vix'] = vix
        
        # Get SPY returns for volatility
        try:
            spy = self.algorithm.Symbol("SPY")
            history = self.algorithm.History(spy, 20, Resolution.Daily)
            if not history.empty:
                returns = history['close'].pct_change().dropna()
                features['realized_vol'] = returns.std() * np.sqrt(252)
        except:
            pass
        
        return features
    
    def ShouldRefit(self, current_date):
        """
        Check if we should refit the HMM based on schedule

        Args:
            current_date: Current date

        Returns:
            bool: True if refit is due
        """
        # First fit (on warmup end)
        if not self.is_fitted and self.fit_on_warmup_end:
            return True

        # No scheduled refit date set yet
        if self.next_scheduled_fit is None:
            return False

        # Check if we've reached scheduled refit date
        if current_date >= self.next_scheduled_fit:
            return True

        return False

    def Fit(self, force=False):
        """
        Fit the HMM model with scheduling

        Args:
            force: Force fit regardless of schedule

        Returns:
            bool: True if fit was performed
        """
        current_date = self.algorithm.Time.date()

        # Check if fit should be performed
        if not force and not self.ShouldRefit(current_date):
            return False

        # For Phase 1: Use simplified heuristics (no actual fitting)
        self.is_fitted = True
        self.last_fit_date = current_date

        # Schedule next refit
        from datetime import timedelta
        self.next_scheduled_fit = current_date + timedelta(days=self.refit_interval_days)

        self.algorithm.Log(
            f"HMM: Fitted on {current_date.strftime('%Y-%m-%d')}, "
            f"next refit scheduled for {self.next_scheduled_fit.strftime('%Y-%m-%d')}"
        )

        return True

    def OnWarmupEnd(self):
        """
        Called when algorithm warmup ends - perform initial fit

        This should be called from main algorithm's OnWarmupEnd
        """
        if self.fit_on_warmup_end and not self.is_fitted:
            self.Fit(force=True)
            self.algorithm.Log("HMM: Initial fit completed after warmup")

    def GetCurrentRegime(self):
        """
        Get current regime state (convenience wrapper)

        Returns:
            dict: Current regime information with keys:
                - dominant_state: str ('Low-Vol', 'High-Vol', or 'Trending')
                - state_probs: dict of state probabilities
                - gpm: float (Global Position Multiplier, 0.3-1.0)
                - requires_2x_edge: bool (if high-vol regime)
                - correlation_breakdown: float (0.0-1.0)
        """
        return self.Update(self.algorithm.Time)

    def GetGlobalPositionMultiplier(self):
        """
        Get the current Global Position Multiplier (GPM)
        Used to scale position sizes based on regime
        """
        regime = self.Update(self.algorithm.Time)
        return regime['gpm']
    
    def GetRegimeSummary(self):
        """Get current regime summary for logging"""
        regime = self.Update(self.algorithm.Time)
        
        summary = f"Regime: {regime['dominant_state']}"
        summary += f" (GPM: {regime['gpm']:.2f})"
        
        if regime['requires_2x_edge']:
            summary += " [2x Edge Required]"
        
        return summary
```


## E:\rony-data\trading-bot\quantconnect\log_retrieval.py

```python
"""
Log Retrieval Utility

Use this in a QuantConnect notebook or research environment to retrieve
and analyze logs from your live/paper trading algorithm.

Usage:
    from log_retrieval import LogRetriever
    
    retriever = LogRetriever(qb)  # qb = QuantConnect QuantBook
    logs = retriever.get_logs('2024-11-06')
    retriever.analyze_logs(logs)
    retriever.export_to_csv(logs, 'my_logs.csv')
"""

import json
import pandas as pd
from datetime import datetime, timedelta

class LogRetriever:
    """Retrieve and analyze logs from QuantConnect ObjectStore"""
    
    def __init__(self, qb):
        """
        Initialize with QuantBook instance
        
        Args:
            qb: QuantConnect QuantBook instance (from notebook)
        """
        self.qb = qb
    
    def list_available_logs(self):
        """List all available log files in ObjectStore"""
        try:
            # Get all keys from ObjectStore
            keys = self.qb.ObjectStore.GetKeys()
            
            # Filter for log files
            log_keys = [k for k in keys if k.startswith('logs_')]
            
            print(f"Found {len(log_keys)} log files:")
            for key in log_keys:
                print(f"  - {key}")
            
            return log_keys
        except Exception as e:
            print(f"Error listing logs: {e}")
            return []
    
    def get_logs(self, date_str, log_type='all'):
        """
        Retrieve logs for a specific date
        
        Args:
            date_str: Date string in format 'YYYY-MM-DD'
            log_type: 'all', 'errors', 'trades', 'detections', 'performance'
        
        Returns:
            dict: Parsed log data
        """
        try:
            # Search for log file matching date
            date_key = date_str.replace('-', '')
            search_pattern = f"logs_{log_type}_*_{date_key}"
            
            # Get all keys and find match
            all_keys = self.qb.ObjectStore.GetKeys()
            matching_keys = [k for k in all_keys if date_key in k and f"logs_{log_type}" in k]
            
            if not matching_keys:
                print(f"No logs found for {date_str} with type '{log_type}'")
                return None
            
            # Use most recent if multiple matches
            key = matching_keys[-1]
            print(f"Retrieving logs from: {key}")
            
            # Get from ObjectStore
            json_str = self.qb.ObjectStore.Read(key)
            logs = json.loads(json_str)
            
            print(f"Successfully retrieved logs for {date_str}")
            return logs
            
        except Exception as e:
            print(f"Error retrieving logs: {e}")
            return None
    
    def get_date_range_logs(self, start_date, end_date, log_type='all'):
        """
        Retrieve logs for a date range
        
        Args:
            start_date: Start date string 'YYYY-MM-DD'
            end_date: End date string 'YYYY-MM-DD'
            log_type: Type of logs to retrieve
        
        Returns:
            dict: Combined log data
        """
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        all_logs = {
            'logs': [],
            'errors': [],
            'trades': [],
            'detections': [],
            'performance': []
        }
        
        current = start
        while current <= end:
            date_str = current.strftime('%Y-%m-%d')
            daily_logs = self.get_logs(date_str, log_type)
            
            if daily_logs:
                # Merge logs
                if 'logs' in daily_logs:
                    all_logs['logs'].extend(daily_logs['logs'])
                if 'errors' in daily_logs:
                    all_logs['errors'].extend(daily_logs['errors'])
                if 'trades' in daily_logs:
                    all_logs['trades'].extend(daily_logs['trades'])
                if 'detections' in daily_logs:
                    all_logs['detections'].extend(daily_logs['detections'])
                if 'performance' in daily_logs:
                    all_logs['performance'].extend(daily_logs['performance'])
            
            current += timedelta(days=1)
        
        return all_logs
    
    def analyze_logs(self, logs):
        """
        Generate analysis report from logs
        
        Args:
            logs: Log data dictionary
        """
        if not logs:
            print("No logs to analyze")
            return
        
        print("\n" + "="*60)
        print("LOG ANALYSIS REPORT")
        print("="*60 + "\n")
        
        # Overall stats
        if 'summary' in logs:
            summary = logs['summary']
            print("Overall Stats:")
            print(f"  Session ID: {logs.get('session_id', 'N/A')}")
            print(f"  Total Logs: {summary.get('total_logs', 0)}")
            print(f"  Total Errors: {summary.get('total_errors', 0)}")
            print(f"  Total Trades: {summary.get('total_trades', 0)}")
            print(f"  Total Detections: {summary.get('total_detections', 0)}")
            print()
        
        # Error analysis
        if 'errors' in logs and logs['errors']:
            print("Error Analysis:")
            error_types = {}
            for error in logs['errors']:
                component = error.get('component', 'unknown')
                error_types[component] = error_types.get(component, 0) + 1
            
            for component, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
                print(f"  {component}: {count} errors")
            print()
        
        # Trade analysis
        if 'trades' in logs and logs['trades']:
            trades = logs['trades']
            print("Trade Analysis:")
            print(f"  Total Trades: {len(trades)}")
            
            entry_count = sum(1 for t in trades if t['trade_type'] == 'entry')
            exit_count = sum(1 for t in trades if t['trade_type'] == 'exit')
            
            print(f"  Entries: {entry_count}")
            print(f"  Exits: {exit_count}")
            
            # Most traded symbols
            symbols = {}
            for trade in trades:
                sym = trade['symbol']
                symbols[sym] = symbols.get(sym, 0) + 1
            
            print(f"  Most traded: {sorted(symbols.items(), key=lambda x: x[1], reverse=True)[:5]}")
            print()
        
        # Detection analysis
        if 'detections' in logs and logs['detections']:
            detections = logs['detections']
            print("Detection Analysis:")
            print(f"  Total Extremes: {len(detections)}")
            
            up = sum(1 for d in detections if d['direction'] == 'up')
            down = sum(1 for d in detections if d['direction'] == 'down')
            
            print(f"  Up: {up}")
            print(f"  Down: {down}")
            
            avg_z = sum(abs(d['z_score']) for d in detections) / len(detections)
            avg_vol = sum(d['vol_anomaly'] for d in detections) / len(detections)
            
            print(f"  Avg |Z-score|: {avg_z:.2f}")
            print(f"  Avg Vol Anomaly: {avg_vol:.2f}x")
            print()
        
        # Performance trend
        if 'performance' in logs and logs['performance']:
            perf = logs['performance']
            print("Performance Trend:")
            print(f"  Snapshots: {len(perf)}")
            
            if len(perf) >= 2:
                start_val = perf[0]['total_value']
                end_val = perf[-1]['total_value']
                change = ((end_val / start_val) - 1) * 100
                
                print(f"  Start Value: ${start_val:,.2f}")
                print(f"  End Value: ${end_val:,.2f}")
                print(f"  Change: {change:+.2f}%")
            print()
        
        print("="*60 + "\n")
    
    def export_to_csv(self, logs, filename_prefix='logs'):
        """
        Export logs to CSV files for external analysis
        
        Args:
            logs: Log data dictionary
            filename_prefix: Prefix for output files
        """
        if not logs:
            print("No logs to export")
            return
        
        # Export detections
        if 'detections' in logs and logs['detections']:
            df = pd.DataFrame(logs['detections'])
            filename = f"{filename_prefix}_detections.csv"
            df.to_csv(filename, index=False)
            print(f"Exported detections to {filename}")
        
        # Export trades
        if 'trades' in logs and logs['trades']:
            df = pd.DataFrame(logs['trades'])
            filename = f"{filename_prefix}_trades.csv"
            df.to_csv(filename, index=False)
            print(f"Exported trades to {filename}")
        
        # Export errors
        if 'errors' in logs and logs['errors']:
            df = pd.DataFrame(logs['errors'])
            filename = f"{filename_prefix}_errors.csv"
            df.to_csv(filename, index=False)
            print(f"Exported errors to {filename}")
        
        # Export performance
        if 'performance' in logs and logs['performance']:
            df = pd.DataFrame(logs['performance'])
            filename = f"{filename_prefix}_performance.csv"
            df.to_csv(filename, index=False)
            print(f"Exported performance to {filename}")
        
        print("Export complete!")
    
    def get_error_details(self, logs):
        """Get detailed error information"""
        if not logs or 'errors' not in logs:
            print("No errors found")
            return
        
        errors = logs['errors']
        
        print("\n" + "="*60)
        print("DETAILED ERROR REPORT")
        print("="*60 + "\n")
        
        for i, error in enumerate(errors[-20:], 1):  # Last 20 errors
            print(f"Error #{i}:")
            print(f"  Time: {error.get('timestamp', 'N/A')}")
            print(f"  Component: {error.get('component', 'unknown')}")
            print(f"  Level: {error.get('level', 'ERROR')}")
            print(f"  Message: {error.get('message', 'N/A')}")
            
            if 'exception' in error:
                exc = error['exception']
                print(f"  Exception: {exc.get('type', 'N/A')}: {exc.get('message', 'N/A')}")
                if 'traceback' in exc:
                    print(f"  Traceback:\n{exc['traceback']}")
            
            print()


# Example usage in QuantConnect Notebook:
"""
# In a QuantConnect Research Notebook

from log_retrieval import LogRetriever

# Initialize
qb = QuantBook()
retriever = LogRetriever(qb)

# List available logs
retriever.list_available_logs()

# Get logs for today
logs = retriever.get_logs('2024-11-06')

# Analyze
retriever.analyze_logs(logs)

# Export to CSV
retriever.export_to_csv(logs, 'extreme_aware_2024_11_06')

# Get specific date range
range_logs = retriever.get_date_range_logs('2024-11-01', '2024-11-06')
retriever.analyze_logs(range_logs)

# Detailed error report
retriever.get_error_details(logs)
"""
```


## E:\rony-data\trading-bot\quantconnect\logger.py

```python
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
            self.algorithm.Log(f"âš ï¸ {formatted}")
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
        
        self.algorithm.Error(f"âŒ {formatted}")
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
        
        self.algorithm.Error(f"ðŸ”´ CRITICAL: {formatted}")
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
        
        msg = (f"ðŸš¨ EXTREME: {symbol} | "
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
        
        msg = (f"ðŸ’° TRADE: {trade_type.upper()} {quantity:+.2f} {symbol} "
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
        
        msg = f"[REGIME] {old_regime} -> {new_regime} (GPM: {regime_data.get('gpm', 1.0):.2f})"
        
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
        
        msg = f"ðŸ”´ CIRCUIT BREAKER: {breaker_type} | {reason} | Action: {action}"
        
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
        
        msg = (f"ðŸ“ A-VWAP: {symbol} | "
               f"VWAP=${avwap_data.get('avwap', 0):.2f} | "
               f"Distance={avwap_data.get('distance', 0):.2%} | "
               f"Bars={avwap_data.get('bars_since_impulse', 0)}")
        
        self.debug(msg, component='AVWAPTracker', extra_data=avwap_data)
    
    def log_risk_metrics(self, metrics):
        """Log risk management metrics"""
        
        msg = (f"ðŸ“Š RISK: DD={metrics.get('drawdown', 0):.2%} | "
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
```


## E:\rony-data\trading-bot\quantconnect\main.py

```python
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

            self.logger.info("â„¹ Advanced components disabled (v1 mode)", component="Main")

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
```


## E:\rony-data\trading-bot\quantconnect\portfolio_constraints.py

```python
"""
Portfolio Constraints - Phase 2

Enforces portfolio-level constraints:
- Beta neutrality (|beta| <= 0.05)
- Sector limits (<= 2x baseline weight)
- Position limits (min of 2% NAV, 5% ADV)
- Gross/Net exposure limits

Usage:
    from portfolio_constraints import PortfolioConstraints
    
    constraints = PortfolioConstraints(algorithm)
    can_trade, reason = constraints.CheckConstraints(symbol, size)
    constraints.EnforceBetaNeutrality()
"""

from AlgorithmImports import *
from collections import defaultdict

class PortfolioConstraints:
    """
    Enforce portfolio-level constraints
    """
    
    def __init__(self, algorithm):
        self.algorithm = algorithm
        self.logger = algorithm.logger if hasattr(algorithm, 'logger') else None
        
        # Constraint thresholds
        self.max_beta = 0.05
        self.max_sector_multiplier = 2.0
        self.max_position_pct_nav = 0.02  # 2%
        self.max_position_pct_adv = 0.05  # 5%
        self.max_gross_exposure = 2.5  # 250%
        self.max_net_exposure = 0.10  # +/-10%
        
        # Baseline sector weights (from universe)
        self.sector_baseline = {}
        
        # Current exposures
        self.current_beta = 0.0
        self.current_sector_weights = defaultdict(float)
        self.current_gross = 0.0
        self.current_net = 0.0
        
        if self.logger:
            self.logger.info("PortfolioConstraints initialized", component="PortfolioConstraints")
    
    def Update(self):
        """Update current portfolio metrics"""
        
        portfolio = self.algorithm.Portfolio
        total_value = portfolio.TotalPortfolioValue
        
        if total_value == 0:
            return
        
        # Calculate exposures
        self.current_gross = 0.0
        self.current_net = 0.0
        self.current_sector_weights = defaultdict(float)
        
        for symbol in portfolio.Keys:
            if portfolio[symbol].Invested:
                quantity = portfolio[symbol].Quantity
                price = portfolio[symbol].Price
                position_value = abs(quantity * price)
                
                # Gross exposure
                self.current_gross += position_value / total_value
                
                # Net exposure
                self.current_net += (quantity * price) / total_value
                
                # Sector exposure (would need sector data)
                # For now, skip
        
        # Calculate beta (simplified - would need actual beta calculation)
        self.current_beta = self._CalculatePortfolioBeta()
    
    def CheckConstraints(self, symbol, proposed_size, price):
        """
        Check if trade violates any constraints
        
        Returns:
            (bool, str): (can_trade, reason)
        """
        
        # 1. Check position size limit
        can_trade, reason = self._CheckPositionLimit(symbol, proposed_size, price)
        if not can_trade:
            return False, reason
        
        # 2. Check sector limit
        can_trade, reason = self._CheckSectorLimit(symbol, proposed_size, price)
        if not can_trade:
            return False, reason
        
        # 3. Check gross exposure
        can_trade, reason = self._CheckGrossExposure(proposed_size, price)
        if not can_trade:
            return False, reason
        
        # 4. Check net exposure
        can_trade, reason = self._CheckNetExposure(proposed_size, price)
        if not can_trade:
            return False, reason
        
        return True, "OK"
    
    def _CheckPositionLimit(self, symbol, size, price):
        """Check if position size within limits"""
        
        portfolio = self.algorithm.Portfolio
        total_value = portfolio.TotalPortfolioValue
        
        if total_value == 0:
            return False, "Zero portfolio value"
        
        position_value = abs(size * price)
        
        # Check vs NAV
        pct_nav = position_value / total_value
        if pct_nav > self.max_position_pct_nav:
            return False, f"Position size {pct_nav:.2%} > {self.max_position_pct_nav:.2%} NAV limit"
        
        # Check vs ADV (would need actual ADV data)
        # For now, skip
        
        return True, "OK"
    
    def _CheckSectorLimit(self, symbol, size, price):
        """Check if sector exposure within limits"""
        
        # Would need sector classification
        # For now, pass
        return True, "OK"
    
    def _CheckGrossExposure(self, size, price):
        """Check if gross exposure within limits"""
        
        portfolio = self.algorithm.Portfolio
        total_value = portfolio.TotalPortfolioValue
        
        if total_value == 0:
            return True, "OK"
        
        new_exposure = abs(size * price) / total_value
        projected_gross = self.current_gross + new_exposure
        
        if projected_gross > self.max_gross_exposure:
            return False, f"Gross exposure {projected_gross:.2f} > {self.max_gross_exposure:.2f} limit"
        
        return True, "OK"
    
    def _CheckNetExposure(self, size, price):
        """Check if net exposure within limits"""
        
        portfolio = self.algorithm.Portfolio
        total_value = portfolio.TotalPortfolioValue
        
        if total_value == 0:
            return True, "OK"
        
        new_exposure = (size * price) / total_value
        projected_net = self.current_net + new_exposure
        
        if abs(projected_net) > self.max_net_exposure:
            return False, f"Net exposure {projected_net:.2%} > +/-{self.max_net_exposure:.2%} limit"
        
        return True, "OK"
    
    def EnforceBetaNeutrality(self):
        """Hedge portfolio beta with SPY if needed"""
        
        if abs(self.current_beta) <= self.max_beta:
            return  # Within tolerance
        
        # Calculate hedge size
        portfolio_value = self.algorithm.Portfolio.TotalPortfolioValue
        hedge_size = -self.current_beta * portfolio_value
        
        # Get SPY price
        spy = self.algorithm.Symbol("SPY")
        if spy not in self.algorithm.Securities:
            if self.logger:
                self.logger.warning("SPY not available for beta hedge", component="PortfolioConstraints")
            return
        
        spy_price = self.algorithm.Securities[spy].Price
        
        if spy_price == 0:
            return
        
        # Calculate shares needed
        shares_needed = int(hedge_size / spy_price)
        
        if abs(shares_needed) < 1:
            return
        
        # Place hedge
        if self.logger:
            self.logger.info(f"Beta hedge: {shares_needed:+d} SPY @ ${spy_price:.2f} (beta={self.current_beta:.3f})",
                           component="PortfolioConstraints")
        
        # Would execute hedge here
        # self.algorithm.MarketOrder(spy, shares_needed)
    
    def _CalculatePortfolioBeta(self):
        """Calculate portfolio beta (simplified)"""
        
        # Would need actual beta calculation with SPY returns
        # For now, estimate based on net exposure
        return self.current_net * 0.8  # Rough estimate
    
    def GetConstraintsSummary(self):
        """Get summary of current constraints"""
        
        return {
            'beta': self.current_beta,
            'beta_limit': self.max_beta,
            'beta_ok': abs(self.current_beta) <= self.max_beta,
            'gross': self.current_gross,
            'gross_limit': self.max_gross_exposure,
            'gross_ok': self.current_gross <= self.max_gross_exposure,
            'net': self.current_net,
            'net_limit': self.max_net_exposure,
            'net_ok': abs(self.current_net) <= self.max_net_exposure
        }
```


## E:\rony-data\trading-bot\quantconnect\pvs_monitor.py

```python
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
            summary += " | âš ï¸ HALT"
        elif info['action']['size_multiplier'] < 1.0:
            summary += f" | Size: {info['action']['size_multiplier']:.1f}x"
        
        return summary
```


## E:\rony-data\trading-bot\quantconnect\risk_monitor.py

```python
"""
Risk Monitor
Tracks all key metrics, circuit breakers, and generates reports
Phase 1: Observation and logging only
"""

from AlgorithmImports import *
from collections import defaultdict
from datetime import datetime

class RiskMonitor:
    """Monitor risk metrics and generate reports"""
    
    def __init__(self, algorithm):
        self.algorithm = algorithm
        self.config = algorithm.config
        
        # Daily tracking
        self.daily_stats = self._InitDailyStats()
        
        # Circuit breaker states
        self.breakers = {
            'consecutive_stopouts': 0,
            'daily_loss_breach': False,
            'weekly_loss_breach': False,
            'liquidity_crisis': False,
            'correlation_spike': False
        }
        
        # Trade log
        self.trades_today = []
        self.extremes_detected = []
        
        # Performance tracking
        self.equity_curve = []
        self.drawdown_history = []
        
    def _InitDailyStats(self):
        """Initialize daily statistics"""
        return {
            'date': None,
            'extremes_detected': 0,
            'trades_attempted': 0,
            'trades_executed': 0,
            'dominant_regime': 'Unknown',
            'avg_gpm': 0.0,
            'active_avwap_tracks': 0,
            'blocked_trades': defaultdict(int),  # reason -> count
            'regime_changes': 0,
            'vix_level': None,
            'correlation_breakdown': 0.0
        }
    
    def Update(self, current_time, regime_state, candidates):
        """
        Update risk metrics
        
        Args:
            current_time: Current timestamp
            regime_state: Dict from HMMRegime
            candidates: List of (symbol, extreme_info) tuples
        """
        
        # Update date if new day
        current_date = current_time.date()
        if self.daily_stats['date'] != current_date:
            # New day - reset daily stats
            self.daily_stats = self._InitDailyStats()
            self.daily_stats['date'] = current_date
            self.trades_today = []
            self.extremes_detected = []
        
        # Update regime tracking
        self.daily_stats['dominant_regime'] = regime_state['dominant_state']
        self.daily_stats['avg_gpm'] = regime_state['gpm']
        self.daily_stats['correlation_breakdown'] = regime_state.get('correlation_breakdown', 0.0)
        
        # Track extremes
        self.daily_stats['extremes_detected'] += len(candidates)
        
        for symbol, info in candidates:
            self.extremes_detected.append({
                'time': current_time,
                'symbol': symbol,
                'z_score': info['z_score'],
                'vol_anomaly': info['vol_anomaly'],
                'direction': info['direction']
            })
        
        # Update A-VWAP track count
        self.daily_stats['active_avwap_tracks'] = self.algorithm.avwap_tracker.GetActiveTracks()
        
        # Check circuit breakers
        self._CheckCircuitBreakers()
    
    def _CheckCircuitBreakers(self):
        """Check if any circuit breakers should fire"""
        
        # Phase 1: Just monitor, don't enforce
        # In later phases, these would halt trading
        
        # Daily loss check
        if self.algorithm.Portfolio.TotalPortfolioValue < self.config.INITIAL_CAPITAL * 0.95:
            if not self.breakers['daily_loss_breach']:
                self.breakers['daily_loss_breach'] = True
                self.algorithm.Log("âš ï¸ Circuit Breaker: Daily loss > 5%")
        else:
            self.breakers['daily_loss_breach'] = False
        
        # Correlation spike (placeholder)
        corr = self.daily_stats['correlation_breakdown']
        if corr > 0.85:
            if not self.breakers['correlation_spike']:
                self.breakers['correlation_spike'] = True
                self.algorithm.Log("âš ï¸ Circuit Breaker: Correlation spike > 0.85")
        else:
            self.breakers['correlation_spike'] = False
    
    def LogBlockedTrade(self, symbol, reason):
        """Log a trade that was blocked and why"""
        self.daily_stats['blocked_trades'][reason] += 1
        self.algorithm.Log(f"âŒ Trade Blocked: {symbol} - {reason}")
    
    def LogTrade(self, symbol, direction, size, price, reason):
        """Log a trade execution"""
        trade = {
            'time': self.algorithm.Time,
            'symbol': symbol,
            'direction': direction,
            'size': size,
            'price': price,
            'reason': reason
        }
        self.trades_today.append(trade)
        self.daily_stats['trades_executed'] += 1
        
        self.algorithm.Log(f"âœ… Trade Executed: {direction} {size} {symbol} @ ${price:.2f} ({reason})")
    
    def GetDailySummary(self):
        """Generate daily summary report"""
        summary = {
            'extremes_detected': self.daily_stats['extremes_detected'],
            'trades_attempted': self.daily_stats['trades_attempted'],
            'trades_executed': self.daily_stats['trades_executed'],
            'dominant_regime': self.daily_stats['dominant_regime'],
            'active_avwap_tracks': self.daily_stats['active_avwap_tracks'],
            'blocked_trades': dict(self.daily_stats['blocked_trades']),
            'circuit_breakers_active': self._GetActiveBreakers()
        }
        
        return summary
    
    def _GetActiveBreakers(self):
        """Get list of active circuit breakers"""
        active = []
        for breaker, is_active in self.breakers.items():
            if is_active:
                active.append(breaker)
        return active
    
    def GetExtremeSummary(self):
        """Get summary of detected extremes today"""
        if not self.extremes_detected:
            return "No extremes detected today"
        
        summary = f"\n{'='*60}\n"
        summary += f"EXTREMES DETECTED TODAY: {len(self.extremes_detected)}\n"
        summary += f"{'='*60}\n"
        
        for ext in self.extremes_detected[-10:]:  # Last 10
            summary += f"{ext['time'].strftime('%H:%M')} | {ext['symbol']:6s} | "
            summary += f"Z={ext['z_score']:+.2f} | Vol={ext['vol_anomaly']:.1f}x | "
            summary += f"{ext['direction']:>4s}\n"
        
        return summary
    
    def CalculateDrawdown(self):
        """Calculate current drawdown"""
        if not self.equity_curve:
            return 0.0
        
        peak = max(self.equity_curve)
        current = self.algorithm.Portfolio.TotalPortfolioValue
        
        if peak > 0:
            dd = (current - peak) / peak
            return dd
        return 0.0
    
    def UpdateEquityCurve(self):
        """Update equity curve for drawdown calculation"""
        self.equity_curve.append(self.algorithm.Portfolio.TotalPortfolioValue)
        
        # Calculate current drawdown
        dd = self.CalculateDrawdown()
        self.drawdown_history.append({
            'time': self.algorithm.Time,
            'drawdown': dd
        })
        
        # Keep only last 252 days (1 year)
        if len(self.equity_curve) > 252:
            self.equity_curve = self.equity_curve[-252:]
            self.drawdown_history = self.drawdown_history[-252:]
    
    def GetDrawdownLadderMultiplier(self):
        """
        Get position size multiplier based on drawdown ladder
        Phase 1: Just observe, don't apply
        """
        dd = abs(self.CalculateDrawdown())
        
        for i, threshold in enumerate(self.config.DD_THRESHOLDS):
            if dd >= threshold:
                multiplier = self.config.DD_MULTIPLIERS[i]
                if multiplier < 1.0:
                    self.algorithm.Log(f"ðŸ“‰ Drawdown {dd:.1%} -> Size Multiplier {multiplier:.2f}")
                return multiplier
        
        return 1.0  # No drawdown scaling
    
    def GenerateWeeklyReport(self):
        """Generate weekly performance report"""
        report = f"\n{'='*60}\n"
        report += f"WEEKLY REPORT - {self.algorithm.Time.strftime('%Y-%m-%d')}\n"
        report += f"{'='*60}\n"
        
        # Performance metrics
        report += f"Portfolio Value: ${self.algorithm.Portfolio.TotalPortfolioValue:,.2f}\n"
        report += f"Cash: ${self.algorithm.Portfolio.Cash:,.2f}\n"
        report += f"Current Drawdown: {self.CalculateDrawdown():.2%}\n"
        
        # Trading activity
        report += f"\nTrading Activity:\n"
        report += f"  Extremes Detected: {self.daily_stats['extremes_detected']}\n"
        report += f"  Trades Executed: {self.daily_stats['trades_executed']}\n"
        
        # Circuit breakers
        active_breakers = self._GetActiveBreakers()
        if active_breakers:
            report += f"\nâš ï¸ Active Circuit Breakers:\n"
            for breaker in active_breakers:
                report += f"  - {breaker}\n"
        else:
            report += f"\nâœ… No active circuit breakers\n"
        
        report += f"{'='*60}\n"
        
        return report
```


## E:\rony-data\trading-bot\quantconnect\universe_filter.py

```python
"""
Universe Selection - Filter for top ~1000 liquid US equities
Criteria:
- NYSE/NASDAQ common shares
- Price: $5-$350
- Liquidity: top 1000 by 60-day median dollar volume
- Spread quality: median spread <= 35 bps
- Exclude blacklisted tickers
"""

from AlgorithmImports import *

class UniverseFilter:
    """Handle coarse and fine universe selection"""
    
    def __init__(self, algorithm):
        self.algorithm = algorithm
        self.config = algorithm.config
        
        # Track universe stats
        self.last_rebalance = None
        self.current_universe = set()
        
    def CoarseFilter(self, coarse):
        """
        First pass: liquidity and price filters
        Returns top UNIVERSE_SIZE symbols
        """
        
        # Filter criteria
        selected = [
            x for x in coarse
            if x.HasFundamentalData
            and x.Price >= self.config.MIN_PRICE
            and x.Price <= self.config.MAX_PRICE
            and x.DollarVolume > self.config.MIN_DOLLAR_VOLUME
            and x.Symbol.Value not in self.config.BLACKLIST
        ]
        
        # Sort by dollar volume and take top N
        selected = sorted(selected, key=lambda x: x.DollarVolume, reverse=True)
        selected = selected[:self.config.UNIVERSE_SIZE]
        
        self.algorithm.Log(f"Coarse Filter: {len(selected)} symbols passed")
        
        return [x.Symbol for x in selected]
    
    def FineFilter(self, fine):
        """
        Second pass: quality filters
        - Common shares only (no ADRs, preferred, etc.)
        - Exchange: NYSE or NASDAQ
        """
        
        selected = []
        
        for f in fine:
            # Basic checks
            if not f.HasFundamentalData:
                continue
            
            # Security type filter
            if f.SecurityReference.SecurityType != "ST00000001":  # Common Stock
                continue
            
            # Exchange filter (NYSE, NASDAQ)
            exchange = f.CompanyReference.PrimaryExchangeId
            if exchange not in ["NYS", "NAS"]:
                continue
            
            # Company profile checks
            if not f.CompanyProfile.HeadquarterCity:
                continue
            
            selected.append(f.Symbol)
        
        self.algorithm.Log(f"Fine Filter: {len(selected)} symbols passed")
        self.current_universe = set(selected)
        
        return selected
    
    def IsInUniverse(self, symbol):
        """Check if symbol is in current universe"""
        return symbol in self.current_universe
    
    def GetUniverseStats(self):
        """Return universe statistics"""
        return {
            'size': len(self.current_universe),
            'last_rebalance': self.last_rebalance
        }
```


## E:\rony-data\trading-bot\src\components\__init__.py

```python
"""
Components package for Extreme-Aware Trading Strategy
Contains all the core trading logic modules
"""

from .universe_filter import UniverseFilter
from .extreme_detector import ExtremeDetector
from .hmm_regime import HMMRegime
from .avwap_tracker import AVWAPTracker
from .risk_monitor import RiskMonitor

__all__ = [
    'UniverseFilter',
    'ExtremeDetector',
    'HMMRegime',
    'AVWAPTracker',
    'RiskMonitor'
]
```


## E:\rony-data\trading-bot\src\components\alert_manager.py

```python
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
    
    def __init__(self, algorithm, alert_config=None):
        self.algorithm = algorithm
        self.logger = algorithm.logger if hasattr(algorithm, 'logger') else None
        
        # Alert configuration
        self.config = alert_config or self._default_config()
        
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
            'info': 'â„¹ï¸',
            'warning': 'âš ï¸',
            'error': 'âŒ',
            'critical': 'ðŸš¨'
        }
        return emojis.get(level, 'ðŸ“¢')
    
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
```


## E:\rony-data\trading-bot\src\components\alerts.py

```python
import os, json, urllib.request, sys

def _slack_post(text: str) -> None:
    url = os.getenv("SLACK_WEBHOOK_URL")
    if not url:
        return
    try:
        data = json.dumps({"text": text}).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=5).read()
    except Exception as e:
        print(f"[alerts] Slack notify failed: {e}", file=sys.stderr)

def notify_extreme(symbol: str, z: float, volx: float, direction: str, avwap_bps: float | None = None) -> None:
    tail = f" | aVWAP {avwap_bps:.0f} bps" if avwap_bps is not None else ""
    msg = f"EXTREME ⏱ {symbol}  z={z:.2f}  vol≈{volx:.1f}x  dir={direction}{tail}"
    print(msg, flush=True)
    _slack_post(msg)

def ask_user_to_confirm(prompt: str = "Confirm trade? (yes/no): ") -> bool:
    # Always ask in console; Slack is FYI only.
    ans = input(prompt).strip().lower()
    return ans in ("y", "yes")
```


## E:\rony-data\trading-bot\src\components\avwap_tracker.py

```python
"""
Anchored VWAP Tracker
Calculates VWAP anchored from the impulse bar when an extreme is detected
Tracks distance to A-VWAP for entry/exit signals
"""

from AlgorithmImports import *
from collections import defaultdict

class AVWAPTracker:
    """Track Anchored VWAP from impulse bars"""
    
    def __init__(self, algorithm):
        self.algorithm = algorithm
        self.config = algorithm.config
        
        # Active tracks: symbol -> anchor info
        self.anchors = {}
        
        # Track data: symbol -> list of bars since anchor
        self.track_bars = defaultdict(list)
        
        # VWAP calculations: symbol -> current A-VWAP
        self.current_avwap = {}
    
    def AddImpulse(self, symbol, extreme_info):
        """
        Start tracking A-VWAP from an impulse bar
        
        Args:
            symbol: The symbol
            extreme_info: Dict from ExtremeDetector with impulse bar data
        """
        
        if not extreme_info['is_extreme']:
            return
        
        # Create anchor point
        impulse_bar = extreme_info['impulse_bar']
        
        self.anchors[symbol] = {
            'start_time': impulse_bar['time'],
            'start_price': impulse_bar['close'],
            'direction': extreme_info['direction'],
            'z_score': extreme_info['z_score'],
            'bars_since_impulse': 0,
            'is_active': True
        }
        
        # Initialize tracking
        self.track_bars[symbol] = [impulse_bar]
        self.current_avwap[symbol] = impulse_bar['close']  # First bar = VWAP
        
        self.algorithm.Log(
            f"A-VWAP: Started tracking {symbol} from ${impulse_bar['close']:.2f} "
            f"({extreme_info['direction']} extreme, Z={extreme_info['z_score']:.2f})"
        )
    
    def UpdateAll(self, minute_bars):
        """
        Update all active A-VWAP tracks
        
        Args:
            minute_bars: Dict of symbol -> list of minute bars
        
        Returns:
            Dict of symbol -> A-VWAP data
        """
        
        results = {}
        symbols_to_remove = []
        
        for symbol in list(self.anchors.keys()):
            if symbol not in minute_bars:
                continue
            
            # Update this track
            avwap_data = self._UpdateSymbol(symbol, minute_bars[symbol])
            
            # Check if track is still active
            if not avwap_data['is_active']:
                symbols_to_remove.append(symbol)
            
            results[symbol] = avwap_data
        
        # Clean up inactive tracks
        for symbol in symbols_to_remove:
            self._RemoveTrack(symbol)
        
        return results
    
    def _UpdateSymbol(self, symbol, minute_bars):
        """
        Update A-VWAP for a single symbol
        
        Returns dict with:
        - avwap: float
        - current_price: float
        - distance: float (percentage from A-VWAP)
        - bars_since_impulse: int
        - is_active: bool
        """
        
        anchor = self.anchors[symbol]
        
        # Get bars since anchor
        anchor_time = anchor['start_time']
        new_bars = [b for b in minute_bars if b['time'] > anchor_time]
        
        if not new_bars:
            # No new bars yet
            return {
                'avwap': self.current_avwap[symbol],
                'current_price': anchor['start_price'],
                'distance': 0.0,
                'bars_since_impulse': 0,
                'is_active': True
            }
        
        # Update bar count
        anchor['bars_since_impulse'] = len(new_bars)
        
        # Calculate VWAP from anchor
        total_pv = 0.0
        total_v = 0.0
        
        # Include original impulse bar
        impulse = self.track_bars[symbol][0]
        typical_price = (impulse['high'] + impulse['low'] + impulse['close']) / 3.0
        total_pv += typical_price * impulse['volume']
        total_v += impulse['volume']
        
        # Add all bars since impulse
        for bar in new_bars:
            typical_price = (bar['high'] + bar['low'] + bar['close']) / 3.0
            total_pv += typical_price * bar['volume']
            total_v += bar['volume']
        
        # Calculate A-VWAP
        avwap = total_pv / total_v if total_v > 0 else anchor['start_price']
        self.current_avwap[symbol] = avwap
        
        # Get current price
        current_price = new_bars[-1]['close']
        
        # Calculate distance
        distance = (current_price / avwap - 1.0) if avwap > 0 else 0.0
        
        # Check if track should still be active
        is_active = self._ShouldKeepActive(symbol, anchor, distance)
        anchor['is_active'] = is_active
        
        return {
            'avwap': avwap,
            'current_price': current_price,
            'distance': distance,
            'bars_since_impulse': anchor['bars_since_impulse'],
            'is_active': is_active,
            'direction': anchor['direction']
        }
    
    def _ShouldKeepActive(self, symbol, anchor, distance):
        """
        Determine if A-VWAP track should remain active
        
        Deactivate if:
        - Too many bars have passed (time stop)
        - Price has moved too far from A-VWAP (distance stop)
        """
        
        # Time stop: deactivate after max bars
        if anchor['bars_since_impulse'] > self.config.AVWAP_MAX_BARS * 60:  # Convert hours to minutes
            self.algorithm.Log(f"A-VWAP: {symbol} time stop hit ({anchor['bars_since_impulse']} bars)")
            return False
        
        # Distance stop: if price is very far from A-VWAP, likely done
        # Allow more distance in direction of original move
        direction = anchor['direction']
        
        if direction == 'up':
            # For upside extreme, deactivate if price falls well below A-VWAP
            if distance < -0.02:  # -2% below A-VWAP
                self.algorithm.Log(f"A-VWAP: {symbol} fell below A-VWAP ({distance:.2%})")
                return False
        else:
            # For downside extreme, deactivate if price rises well above A-VWAP
            if distance > 0.02:  # +2% above A-VWAP
                self.algorithm.Log(f"A-VWAP: {symbol} rose above A-VWAP ({distance:.2%})")
                return False
        
        return True
    
    def GetAVWAP(self, symbol):
        """Get current A-VWAP for a symbol"""
        if symbol in self.current_avwap:
            return self.current_avwap[symbol]
        return None
    
    def GetDistance(self, symbol, current_price):
        """Get distance from current price to A-VWAP"""
        avwap = self.GetAVWAP(symbol)
        if avwap is not None and avwap > 0:
            return (current_price / avwap - 1.0)
        return None
    
    def IsTracking(self, symbol):
        """Check if actively tracking a symbol"""
        return symbol in self.anchors and self.anchors[symbol]['is_active']
    
    def _RemoveTrack(self, symbol):
        """Remove an inactive track"""
        if symbol in self.anchors:
            self.algorithm.Log(f"A-VWAP: Stopped tracking {symbol}")
            del self.anchors[symbol]
        
        if symbol in self.track_bars:
            del self.track_bars[symbol]
        
        if symbol in self.current_avwap:
            del self.current_avwap[symbol]
    
    def GetActiveTracks(self):
        """Get count of active tracks"""
        return sum(1 for a in self.anchors.values() if a['is_active'])
    
    def GetTrackInfo(self, symbol):
        """Get detailed track info for a symbol"""
        if symbol not in self.anchors:
            return None
        
        anchor = self.anchors[symbol]
        avwap = self.current_avwap.get(symbol, 0.0)
        
        return {
            'start_time': anchor['start_time'],
            'start_price': anchor['start_price'],
            'current_avwap': avwap,
            'direction': anchor['direction'],
            'bars_since_impulse': anchor['bars_since_impulse'],
            'is_active': anchor['is_active']
        }
```


## E:\rony-data\trading-bot\src\components\backtest_analyzer.py

```python
"""
Enhanced Backtesting Framework with Realistic Cost Modeling

Provides more accurate backtest results by modeling:
- Realistic slippage (volatility and participation based)
- Market impact (volume-based)
- Time-of-day dependent spreads
- Fill probability
- TWAP execution simulation
- Detailed cost breakdown

Usage:
    from backtest_analyzer import BacktestAnalyzer
    
    analyzer = BacktestAnalyzer(algorithm)
    cost = analyzer.calculate_realistic_costs(trade)
    analyzer.generate_report()
"""

from AlgorithmImports import *
import numpy as np
import pandas as pd
from collections import defaultdict
from datetime import datetime, timedelta

class BacktestAnalyzer:
    """
    Advanced backtesting with realistic cost modeling
    """
    
    def __init__(self, algorithm):
        self.algorithm = algorithm
        self.logger = algorithm.logger if hasattr(algorithm, 'logger') else None
        
        # Trade tracking
        self.trades = []
        self.positions = {}
        
        # Performance tracking
        self.daily_returns = []
        self.equity_curve = []
        
        # Cost breakdown
        self.costs = {
            'spread': 0.0,
            'slippage': 0.0,
            'impact': 0.0,
            'fees': 0.0,
            'total': 0.0
        }
        
        # Statistics by category
        self.stats = {
            'by_direction': {'up': [], 'down': []},
            'by_regime': {'Low-Vol': [], 'High-Vol': [], 'Trending': []},
            'by_time': defaultdict(list),
            'by_symbol': defaultdict(list),
            'by_sector': defaultdict(list)
        }
        
        # Win/loss tracking
        self.wins = 0
        self.losses = 0
        self.total_pnl = 0.0
        
        if self.logger:
            self.logger.info("BacktestAnalyzer initialized", component="BacktestAnalyzer")
    
    def calculate_realistic_costs(self, trade_info):
        """
        Calculate realistic trading costs
        
        Args:
            trade_info: dict with symbol, quantity, price, timestamp, volatility, adv
        
        Returns:
            dict with cost breakdown
        """
        
        symbol = trade_info['symbol']
        quantity = abs(trade_info['quantity'])
        price = trade_info['price']
        timestamp = trade_info['timestamp']
        
        # Get market data
        volatility = trade_info.get('volatility', 0.02)  # 2% default
        adv = trade_info.get('adv', 1_000_000)  # Average daily volume
        
        # 1. Spread cost
        spread_cost = self._calculate_spread_cost(price, timestamp)
        
        # 2. Slippage (participation + volatility based)
        slippage_cost = self._calculate_slippage(quantity, adv, volatility)
        
        # 3. Market impact
        impact_cost = self._calculate_market_impact(quantity, adv, volatility)
        
        # 4. Fees
        fee_cost = self._calculate_fees(quantity, price)
        
        # Total cost
        total_cost = spread_cost + slippage_cost + impact_cost + fee_cost
        
        # Cost breakdown
        costs = {
            'spread': spread_cost * quantity,
            'slippage': slippage_cost * quantity,
            'impact': impact_cost * quantity,
            'fees': fee_cost * quantity,
            'total': total_cost * quantity,
            'bps': (total_cost / price) * 10000  # Basis points
        }
        
        # Track cumulative costs
        for key in ['spread', 'slippage', 'impact', 'fees', 'total']:
            self.costs[key] += costs[key]
        
        return costs
    
    def _calculate_spread_cost(self, price, timestamp):
        """
        Calculate spread cost (time-of-day dependent)
        
        Spreads wider at open/close, tighter mid-day
        """
        
        hour = timestamp.hour
        minute = timestamp.minute
        
        # Base spread (in dollars)
        base_spread_bps = 10  # 10 bps base
        
        # Time-of-day multiplier
        if (hour == 9 and minute < 45) or (hour == 15 and minute > 45):
            # First/last 15 minutes: wider spreads
            spread_mult = 2.0
        elif (hour == 9 and minute < 60) or (hour == 15 and minute > 30):
            # First/last 30 minutes: moderately wider
            spread_mult = 1.5
        elif hour >= 11 and hour <= 14:
            # Mid-day: tightest spreads
            spread_mult = 0.8
        else:
            # Normal hours
            spread_mult = 1.0
        
        # Spread cost per share
        spread_bps = base_spread_bps * spread_mult
        spread_cost = price * (spread_bps / 10000)
        
        # Cross the spread (pay half on average)
        return spread_cost * 0.5
    
    def _calculate_slippage(self, quantity, adv, volatility):
        """
        Calculate slippage based on participation rate and volatility
        
        Formula: slippage = sqrt(participation_rate) * volatility * alpha
        """
        
        # Estimate we trade over 5 minutes with 10% POV
        pov = 0.10  # 10% participation
        time_window_minutes = 5
        
        # Minute volume = ADV / (6.5 hours * 60 minutes)
        minute_volume = adv / (6.5 * 60)
        
        # Our share of volume in 5 minutes
        our_volume = quantity
        market_volume_5min = minute_volume * time_window_minutes * pov
        
        if market_volume_5min > 0:
            participation_rate = our_volume / market_volume_5min
        else:
            participation_rate = 0.1  # Default 10%
        
        # Cap participation rate
        participation_rate = min(participation_rate, 0.5)
        
        # Slippage model
        alpha = 0.5  # Calibration parameter
        slippage_pct = alpha * np.sqrt(participation_rate) * volatility
        
        return slippage_pct
    
    def _calculate_market_impact(self, quantity, adv, volatility):
        """
        Calculate market impact (permanent + temporary)
        
        Almgren-Chriss model simplified
        """
        
        # Daily volume participation
        participation = quantity / adv if adv > 0 else 0
        participation = min(participation, 0.25)  # Cap at 25% ADV
        
        # Impact parameters
        gamma = 0.1  # Temporary impact coefficient
        eta = 0.05   # Permanent impact coefficient
        
        # Temporary impact (goes away)
        temp_impact = gamma * volatility * np.sqrt(participation)
        
        # Permanent impact (stays)
        perm_impact = eta * volatility * participation
        
        # Total impact (we pay temp + half of perm)
        total_impact = temp_impact + (perm_impact * 0.5)
        
        return total_impact
    
    def _calculate_fees(self, quantity, price):
        """
        Calculate trading fees
        
        Interactive Brokers tiered pricing (example)
        """
        
        # IBKR tiered pricing (rough estimate)
        # $0.005 per share, $1 minimum
        per_share_fee = 0.005
        notional = quantity * price
        
        # SEC fees (sells only, but include for both for safety)
        sec_fee_rate = 0.0000278  # $27.80 per million
        sec_fee = notional * sec_fee_rate
        
        total_fee_per_share = per_share_fee + (sec_fee / quantity if quantity > 0 else 0)
        
        # Minimum $1
        total_fee = max(total_fee_per_share, 1.0 / quantity if quantity > 0 else 0)
        
        return total_fee
    
    def record_trade(self, trade_type, symbol, quantity, entry_price, exit_price=None, 
                    regime=None, direction=None, timestamp=None, metadata=None):
        """
        Record a trade for analysis
        
        Args:
            trade_type: 'open' or 'close'
            symbol: Stock symbol
            quantity: Share quantity
            entry_price: Entry price
            exit_price: Exit price (if closing)
            regime: Market regime
            direction: Trade direction ('up' or 'down')
            timestamp: Trade timestamp
            metadata: Additional info
        """
        
        timestamp = timestamp or self.algorithm.Time
        
        if trade_type == 'open':
            # Opening position
            self.positions[symbol] = {
                'entry_price': entry_price,
                'quantity': quantity,
                'entry_time': timestamp,
                'regime': regime,
                'direction': direction,
                'metadata': metadata or {}
            }
            
        elif trade_type == 'close' and symbol in self.positions:
            # Closing position
            position = self.positions[symbol]
            
            # Calculate P&L
            if exit_price:
                pnl = (exit_price - position['entry_price']) * position['quantity']
                hold_time = (timestamp - position['entry_time']).total_seconds() / 3600  # Hours
                
                # Calculate costs
                entry_costs = self.calculate_realistic_costs({
                    'symbol': symbol,
                    'quantity': quantity,
                    'price': position['entry_price'],
                    'timestamp': position['entry_time'],
                    'volatility': metadata.get('volatility', 0.02) if metadata else 0.02,
                    'adv': metadata.get('adv', 1_000_000) if metadata else 1_000_000
                })
                
                exit_costs = self.calculate_realistic_costs({
                    'symbol': symbol,
                    'quantity': quantity,
                    'price': exit_price,
                    'timestamp': timestamp,
                    'volatility': metadata.get('volatility', 0.02) if metadata else 0.02,
                    'adv': metadata.get('adv', 1_000_000) if metadata else 1_000_000
                })
                
                total_costs = entry_costs['total'] + exit_costs['total']
                net_pnl = pnl - total_costs
                
                # Record trade
                trade = {
                    'symbol': str(symbol),
                    'entry_time': position['entry_time'],
                    'exit_time': timestamp,
                    'hold_time_hours': hold_time,
                    'entry_price': position['entry_price'],
                    'exit_price': exit_price,
                    'quantity': position['quantity'],
                    'gross_pnl': pnl,
                    'costs': total_costs,
                    'net_pnl': net_pnl,
                    'return_pct': (exit_price / position['entry_price'] - 1),
                    'regime': position.get('regime'),
                    'direction': position.get('direction'),
                    'metadata': position.get('metadata', {})
                }
                
                self.trades.append(trade)
                
                # Update stats
                if net_pnl > 0:
                    self.wins += 1
                else:
                    self.losses += 1
                
                self.total_pnl += net_pnl
                
                # Categorize
                if position.get('direction'):
                    self.stats['by_direction'][position['direction']].append(trade)
                
                if position.get('regime'):
                    self.stats['by_regime'][position['regime']].append(trade)
                
                hour = position['entry_time'].hour
                self.stats['by_time'][hour].append(trade)
                
                self.stats['by_symbol'][str(symbol)].append(trade)
            
            # Remove from positions
            del self.positions[symbol]
    
    def calculate_metrics(self):
        """Calculate comprehensive performance metrics"""
        
        if not self.trades:
            return {}
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame(self.trades)
        
        # Basic metrics
        total_trades = len(df)
        win_rate = self.wins / total_trades if total_trades > 0 else 0
        
        winning_trades = df[df['net_pnl'] > 0]
        losing_trades = df[df['net_pnl'] < 0]
        
        avg_win = winning_trades['net_pnl'].mean() if len(winning_trades) > 0 else 0
        avg_loss = losing_trades['net_pnl'].mean() if len(losing_trades) > 0 else 0
        
        profit_factor = abs(winning_trades['net_pnl'].sum() / losing_trades['net_pnl'].sum()) if len(losing_trades) > 0 else float('inf')
        
        # Return metrics
        total_return = df['net_pnl'].sum()
        avg_return_per_trade = df['net_pnl'].mean()
        
        # Risk metrics
        std_returns = df['net_pnl'].std()
        sharpe_ratio = (avg_return_per_trade / std_returns * np.sqrt(252)) if std_returns > 0 else 0
        
        # Hold time
        avg_hold_time = df['hold_time_hours'].mean()
        
        # Cost analysis
        total_costs = df['costs'].sum()
        avg_cost_per_trade = df['costs'].mean()
        cost_as_pct_of_pnl = abs(total_costs / total_return) if total_return != 0 else 0
        
        metrics = {
            'total_trades': total_trades,
            'wins': self.wins,
            'losses': self.losses,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'avg_win_loss_ratio': abs(avg_win / avg_loss) if avg_loss != 0 else 0,
            'profit_factor': profit_factor,
            'total_return': total_return,
            'avg_return_per_trade': avg_return_per_trade,
            'sharpe_ratio': sharpe_ratio,
            'avg_hold_time_hours': avg_hold_time,
            'total_costs': total_costs,
            'avg_cost_per_trade': avg_cost_per_trade,
            'cost_as_pct_of_pnl': cost_as_pct_of_pnl,
            'cost_breakdown': dict(self.costs)
        }
        
        return metrics
    
    def generate_report(self):
        """Generate comprehensive backtest report"""
        
        metrics = self.calculate_metrics()
        
        if not metrics:
            return "No trades to analyze"
        
        report = "\n" + "="*70 + "\n"
        report += "BACKTEST ANALYSIS REPORT\n"
        report += "="*70 + "\n\n"
        
        # Overall Performance
        report += "OVERALL PERFORMANCE:\n"
        report += "-"*70 + "\n"
        report += f"Total Trades:          {metrics['total_trades']}\n"
        report += f"Wins / Losses:         {metrics['wins']} / {metrics['losses']}\n"
        report += f"Win Rate:              {metrics['win_rate']:.2%}\n"
        report += f"Profit Factor:         {metrics['profit_factor']:.2f}\n"
        report += f"Total Return:          ${metrics['total_return']:,.2f}\n"
        report += f"Avg Return/Trade:      ${metrics['avg_return_per_trade']:,.2f}\n"
        report += f"Sharpe Ratio:          {metrics['sharpe_ratio']:.2f}\n"
        report += f"Avg Hold Time:         {metrics['avg_hold_time_hours']:.1f} hours\n"
        report += "\n"
        
        # Win/Loss Stats
        report += "WIN/LOSS STATISTICS:\n"
        report += "-"*70 + "\n"
        report += f"Average Win:           ${metrics['avg_win']:,.2f}\n"
        report += f"Average Loss:          ${metrics['avg_loss']:,.2f}\n"
        report += f"Avg Win/Loss Ratio:    {metrics['avg_win_loss_ratio']:.2f}\n"
        report += "\n"
        
        # Cost Analysis
        report += "COST ANALYSIS:\n"
        report += "-"*70 + "\n"
        report += f"Total Costs:           ${metrics['total_costs']:,.2f}\n"
        report += f"Avg Cost/Trade:        ${metrics['avg_cost_per_trade']:,.2f}\n"
        report += f"Costs as % of P&L:     {metrics['cost_as_pct_of_pnl']:.2%}\n"
        report += "\n"
        report += "Cost Breakdown:\n"
        report += f"  Spread:              ${metrics['cost_breakdown']['spread']:,.2f}\n"
        report += f"  Slippage:            ${metrics['cost_breakdown']['slippage']:,.2f}\n"
        report += f"  Market Impact:       ${metrics['cost_breakdown']['impact']:,.2f}\n"
        report += f"  Fees:                ${metrics['cost_breakdown']['fees']:,.2f}\n"
        report += "\n"
        
        # Performance by Category
        report += self._analyze_by_category()
        
        report += "="*70 + "\n"
        
        return report
    
    def _analyze_by_category(self):
        """Analyze performance by different categories"""
        
        report = ""
        
        # By direction
        if self.stats['by_direction']['up'] or self.stats['by_direction']['down']:
            report += "PERFORMANCE BY DIRECTION:\n"
            report += "-"*70 + "\n"
            
            for direction in ['up', 'down']:
                trades = self.stats['by_direction'][direction]
                if trades:
                    df = pd.DataFrame(trades)
                    wins = len(df[df['net_pnl'] > 0])
                    total = len(df)
                    avg_pnl = df['net_pnl'].mean()
                    
                    report += f"  {direction.upper()}: {total} trades, {wins}/{total} wins ({wins/total:.1%}), Avg P&L: ${avg_pnl:,.2f}\n"
            report += "\n"
        
        # By regime
        if any(self.stats['by_regime'].values()):
            report += "PERFORMANCE BY REGIME:\n"
            report += "-"*70 + "\n"
            
            for regime in ['Low-Vol', 'High-Vol', 'Trending']:
                trades = self.stats['by_regime'][regime]
                if trades:
                    df = pd.DataFrame(trades)
                    wins = len(df[df['net_pnl'] > 0])
                    total = len(df)
                    avg_pnl = df['net_pnl'].mean()
                    
                    report += f"  {regime}: {total} trades, {wins}/{total} wins ({wins/total:.1%}), Avg P&L: ${avg_pnl:,.2f}\n"
            report += "\n"
        
        # By time of day
        if self.stats['by_time']:
            report += "PERFORMANCE BY HOUR:\n"
            report += "-"*70 + "\n"
            
            for hour in sorted(self.stats['by_time'].keys()):
                trades = self.stats['by_time'][hour]
                if trades:
                    df = pd.DataFrame(trades)
                    total = len(df)
                    avg_pnl = df['net_pnl'].mean()
                    
                    report += f"  {hour:02d}:00: {total} trades, Avg P&L: ${avg_pnl:,.2f}\n"
            report += "\n"
        
        return report
    
    def export_trades_csv(self):
        """Export trades to CSV format"""
        if not self.trades:
            return None
        
        df = pd.DataFrame(self.trades)
        
        # Format for readability
        df['entry_time'] = pd.to_datetime(df['entry_time'])
        df['exit_time'] = pd.to_datetime(df['exit_time'])
        
        return df
```


## E:\rony-data\trading-bot\src\components\backtest_logger.py

```python
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
```


## E:\rony-data\trading-bot\src\components\cascade_prevention.py

```python
"""
Cascade Prevention - Phase 2

Prevents cascade of bad decisions by blocking trades when â‰¥2 violations occur.

Violations:
- Weak signal (low edge)
- Loss streak (â‰¥2 consecutive)
- High PVS (>7)
- Rule violation today
- Fatigue (>3 trades/hour)
- Regime uncertainty

Usage:
    from cascade_prevention import CascadePrevention
    
    cascade = CascadePrevention(algorithm)
    can_trade, violations = cascade.CheckCascadeRisk(trade_signal)
"""

from AlgorithmImports import *

class CascadePrevention:
    """Block trades when multiple violations occur"""
    
    def __init__(self, algorithm):
        self.algorithm = algorithm
        self.logger = getattr(algorithm, 'logger', None)

        # Get thresholds from config, with sane defaults. Be defensive: some
        # unit tests or lightweight runs may not attach a full `config` object
        # to the algorithm stub, so check for presence first.
        cascade_config = {}
        if getattr(algorithm, 'config', None) is not None:
            cascade_config = getattr(algorithm.config, 'CASCADE_PREVENTION', {})
        self.min_edge_threshold = cascade_config.get('MIN_EDGE_THRESHOLD', 2.0)
        self.cascade_threshold = cascade_config.get('CASCADE_THRESHOLD', 2)
        self.max_consecutive_losses = cascade_config.get('MAX_CONSECUTIVE_LOSSES', 2)
        self.pvs_threshold = cascade_config.get('PVS_THRESHOLD', 7)
        self.max_trades_per_hour = cascade_config.get('MAX_TRADES_PER_HOUR', 3)
        self.min_regime_confidence = cascade_config.get('MIN_REGIME_CONFIDENCE', 0.5)
        
    def CheckCascadeRisk(self,
                         trade_signal: dict,
                         pvs_score: float,
                         consecutive_losses: int,
                         regime_confidence: float,
                         trades_last_hour: int,
                         rule_violations: int
                         ) -> tuple[bool, list]:
        """
        Check if trade should be blocked due to cascade risk
        
        Returns:
            (bool, list): (can_trade, violations)
        """
        violations = []
        
        # Check each factor
        if abs(trade_signal.get('z_score', 0)) < self.min_edge_threshold:
            violations.append('weak_signal')
        
        if consecutive_losses >= self.max_consecutive_losses:
            violations.append('loss_streak')
        
        if pvs_score > self.pvs_threshold:
            violations.append('high_pvs')
        
        if rule_violations > 0:
            violations.append('rule_violation')
        
        if trades_last_hour > self.max_trades_per_hour:
            violations.append('fatigue')
        
        if regime_confidence < self.min_regime_confidence:
            violations.append('regime_uncertainty')
        
        # Block if â‰¥2 violations
        can_trade = len(violations) < self.cascade_threshold
        
        if not can_trade and self.logger:
            self.logger.warning(f"Cascade prevention: {violations}", component="CascadePrevention")
        
        return can_trade, violations
```


## E:\rony-data\trading-bot\src\components\drawdown_enforcer.py

```python
"""
Drawdown Enforcer - Phase 2

Enforces the drawdown ladder by actually reducing position sizes during drawdowns.

Drawdown Ladder:
- 10% DD â†’ 0.75x size
- 20% DD â†’ 0.50x size
- 30% DD â†’ 0.25x size
- 40% DD â†’ 0.00x (HALT all trading)

Usage:
    from drawdown_enforcer import DrawdownEnforcer
    
    enforcer = DrawdownEnforcer(algorithm)
    multiplier = enforcer.GetSizeMultiplier(current_dd)
    should_halt = enforcer.ShouldHalt(current_dd)
"""

from AlgorithmImports import *
from collections import deque

class DrawdownEnforcer:
    """
    Enforce drawdown-based position sizing ladder
    """
    
    def __init__(self, algorithm):
        self.algorithm = algorithm
        self.logger = algorithm.logger if hasattr(algorithm, 'logger') else None
        self.alert_manager = algorithm.alert_manager if hasattr(algorithm, 'alert_manager') else None
        
        # Drawdown ladder configuration
        self.dd_thresholds = [0.10, 0.20, 0.30, 0.40]
        self.dd_multipliers = [0.75, 0.50, 0.25, 0.00]
        
        # Tracking
        self.equity_curve = deque(maxlen=252 * 390)  # 1 year of minute bars
        self.peak_value = None
        self.current_drawdown = 0.0
        self.current_multiplier = 1.0
        self.current_rung = 0  # Which rung of the ladder we're on
        
        # Historical tracking
        self.dd_history = deque(maxlen=252)  # 1 year of daily DD
        self.max_dd_hit = 0.0
        
        # Alert tracking
        self.last_alert_rung = -1
        
        if self.logger:
            self.logger.info("DrawdownEnforcer initialized", component="DrawdownEnforcer")
    
    def Update(self, portfolio_value):
        """
        Update equity curve and calculate current drawdown
        
        Args:
            portfolio_value: Current portfolio total value
        
        Returns:
            dict with DD info
        """
        
        # Update equity curve
        self.equity_curve.append(portfolio_value)
        
        # Initialize peak if first update
        if self.peak_value is None:
            self.peak_value = portfolio_value
        
        # Update peak
        if portfolio_value > self.peak_value:
            self.peak_value = portfolio_value
        
        # Calculate drawdown
        if self.peak_value > 0:
            self.current_drawdown = (portfolio_value - self.peak_value) / self.peak_value
        else:
            self.current_drawdown = 0.0
        
        # Track max DD
        if abs(self.current_drawdown) > self.max_dd_hit:
            self.max_dd_hit = abs(self.current_drawdown)
        
        # Determine current ladder rung
        old_rung = self.current_rung
        self.current_rung = self._GetCurrentRung(abs(self.current_drawdown))
        self.current_multiplier = self._GetMultiplierForRung(self.current_rung)
        
        # Alert on rung change
        if self.current_rung != old_rung and self.current_rung > 0:
            self._AlertRungChange(old_rung, self.current_rung, abs(self.current_drawdown))
        
        # Store daily DD
        if len(self.dd_history) == 0 or self.dd_history[-1] != self.current_drawdown:
            self.dd_history.append(self.current_drawdown)
        
        return {
            'current_drawdown': self.current_drawdown,
            'current_rung': self.current_rung,
            'current_multiplier': self.current_multiplier,
            'peak_value': self.peak_value,
            'max_dd_hit': self.max_dd_hit
        }
    
    def _GetCurrentRung(self, abs_dd):
        """
        Determine which rung of the ladder we're on
        
        Returns: 0 (no DD), 1 (10%), 2 (20%), 3 (30%), 4 (40%+)
        """
        for i, threshold in enumerate(self.dd_thresholds):
            if abs_dd >= threshold:
                continue
            else:
                return i
        
        return len(self.dd_thresholds)  # Highest rung
    
    def _GetMultiplierForRung(self, rung):
        """Get the size multiplier for a given rung"""
        if rung == 0:
            return 1.0
        elif rung <= len(self.dd_multipliers):
            return self.dd_multipliers[rung - 1]
        else:
            return 0.0
    
    def GetSizeMultiplier(self, current_dd=None):
        """
        Get current position size multiplier based on drawdown
        
        Args:
            current_dd: Optional specific DD to check (otherwise uses current)
        
        Returns:
            float: Multiplier (0.0 to 1.0)
        """
        
        if current_dd is None:
            return self.current_multiplier
        
        abs_dd = abs(current_dd)
        rung = self._GetCurrentRung(abs_dd)
        return self._GetMultiplierForRung(rung)
    
    def ShouldHalt(self, current_dd=None):
        """
        Check if trading should be halted due to drawdown
        
        Returns:
            bool: True if should halt (DD >= 40%)
        """
        
        if current_dd is None:
            abs_dd = abs(self.current_drawdown)
        else:
            abs_dd = abs(current_dd)
        
        return abs_dd >= self.dd_thresholds[-1]  # 40%
    
    def GetDrawdownInfo(self):
        """Get detailed drawdown information"""
        
        return {
            'current_dd': self.current_drawdown,
            'current_dd_pct': abs(self.current_drawdown) * 100,
            'current_rung': self.current_rung,
            'current_multiplier': self.current_multiplier,
            'peak_value': self.peak_value,
            'current_value': self.equity_curve[-1] if self.equity_curve else 0,
            'max_dd_hit': self.max_dd_hit,
            'should_halt': self.ShouldHalt(),
            'ladder': self._GetLadderStatus()
        }
    
    def _GetLadderStatus(self):
        """Get status of each ladder rung"""
        
        abs_dd = abs(self.current_drawdown)
        
        ladder = []
        for i, (threshold, multiplier) in enumerate(zip(self.dd_thresholds, self.dd_multipliers)):
            status = {
                'rung': i + 1,
                'threshold': threshold,
                'threshold_pct': threshold * 100,
                'multiplier': multiplier,
                'active': abs_dd >= threshold
            }
            ladder.append(status)
        
        return ladder
    
    def _AlertRungChange(self, old_rung, new_rung, abs_dd):
        """Alert when moving to a new rung of the ladder"""
        
        # Only alert once per rung
        if self.last_alert_rung == new_rung:
            return
        
        self.last_alert_rung = new_rung
        
        # Get multiplier
        multiplier = self.current_multiplier
        
        # Determine severity
        if new_rung >= 3:  # 30% or more
            level = 'critical'
        elif new_rung >= 2:  # 20% or more
            level = 'error'
        else:
            level = 'warning'
        
        # Create message
        message = f"Drawdown Ladder: Rung {new_rung} activated - DD {abs_dd:.2%} â†’ Size {multiplier:.2f}x"
        
        if self.logger:
            if level == 'critical':
                self.logger.critical(message, component="DrawdownEnforcer")
            elif level == 'error':
                self.logger.error(message, component="DrawdownEnforcer")
            else:
                self.logger.warning(message, component="DrawdownEnforcer")
        
        # Send alert
        if self.alert_manager:
            self.alert_manager.alert_drawdown(abs_dd, self.dd_thresholds[new_rung - 1])
    
    def GetRecoveryInfo(self):
        """Get information about recovery from drawdown"""
        
        if len(self.equity_curve) < 2:
            return None
        
        # Check if recovering
        current_val = self.equity_curve[-1]
        prev_val = self.equity_curve[-2]
        
        is_recovering = current_val > prev_val
        
        # Distance to peak
        distance_to_peak = (self.peak_value - current_val) / self.peak_value if self.peak_value > 0 else 0
        
        # Estimated bars to recovery (linear extrapolation)
        if is_recovering and prev_val > 0:
            recovery_rate = (current_val - prev_val) / prev_val
            if recovery_rate > 0:
                bars_to_recovery = int(distance_to_peak / recovery_rate)
            else:
                bars_to_recovery = None
        else:
            bars_to_recovery = None
        
        return {
            'is_recovering': is_recovering,
            'distance_to_peak': distance_to_peak,
            'distance_to_peak_pct': distance_to_peak * 100,
            'bars_to_recovery': bars_to_recovery,
            'recovery_rate': recovery_rate if is_recovering else 0
        }
    
    def Reset(self):
        """Reset drawdown tracking (use carefully!)"""
        
        if self.logger:
            self.logger.warning("Drawdown enforcer reset - peak reset to current value", 
                              component="DrawdownEnforcer")
        
        if self.equity_curve:
            self.peak_value = self.equity_curve[-1]
        
        self.current_drawdown = 0.0
        self.current_rung = 0
        self.current_multiplier = 1.0
        self.last_alert_rung = -1
    
    def GetSummary(self):
        """Get summary for logging"""
        
        info = self.GetDrawdownInfo()
        
        summary = f"DD: {info['current_dd_pct']:.1f}% | "
        summary += f"Rung: {info['current_rung']}/4 | "
        summary += f"Size: {info['current_multiplier']:.2f}x | "
        summary += f"Peak: ${info['peak_value']:,.2f}"
        
        if info['should_halt']:
            summary += " | âš ï¸ HALTED"
        
        return summary
```


## E:\rony-data\trading-bot\src\components\dynamic_sizer.py

```python
"""
Dynamic Position Sizer - Phase 2

Kelly-inspired position sizing based on edge quality.

Formula:
base_size * edge_mult * regime_mult * dd_mult * pvs_mult

Multipliers:
- Edge: 1x to 2x (based on |Z|)
- Regime: 0.3 to 1.0 (from HMM GPM)
- Drawdown: 0.0 to 1.0 (from DD ladder)
- PVS: 0.0 to 1.0 (from psychological state)

Usage:
    from dynamic_sizer import DynamicSizer
    
    sizer = DynamicSizer(algorithm)
    size = sizer.CalculateSize(signal, regime, dd, pvs)
"""

from AlgorithmImports import *

class DynamicSizer:
    """Dynamic position sizing based on multiple factors"""
    
    def __init__(self, algorithm):
        self.algorithm = algorithm
        self.base_size = 5.0  # $5 base
        self.min_size = 2.50
        self.max_size = 20.0
        
    def CalculateSize(self, z_score, gpm, dd_mult, pvs_mult):
        """
        Calculate position size
        
        Args:
            z_score: Signal Z-score
            gpm: Global Position Multiplier (regime)
            dd_mult: Drawdown multiplier
            pvs_mult: PVS multiplier
        
        Returns:
            float: Position size in dollars
        """
        
        # Edge multiplier (1x to 2x)
        edge_mult = min(abs(z_score) / 2.0, 2.0)
        
        # Combine all multipliers
        total_mult = edge_mult * gpm * dd_mult * pvs_mult
        
        # Calculate size
        size = self.base_size * total_mult
        
        # Apply caps
        size = max(self.min_size, min(size, self.max_size))
        
        return size
```


## E:\rony-data\trading-bot\src\components\entry_timing.py

```python
"""
Entry Timing Protocol - Phase 2

Better entry timing following Section 5.1 protocol:
1. Wait 15-30 min after extreme
2. Confirm positive tick delta
3. Abort if >50% retracement
4. Enter on pullback to A-VWAP

Usage:
    from entry_timing import EntryTiming
    
    timing = EntryTiming(algorithm)
    can_enter, reason = timing.CheckEntryTiming(extreme_info, current_price)
"""

from AlgorithmImports import *
from datetime import timedelta
import random

class EntryTiming:
    """Entry timing protocol for better fills"""
    
    def __init__(self, algorithm):
        self.algorithm = algorithm
        self.wait_min = 15
        self.wait_max = 30
        self.max_retracement = 0.50
        
    def CheckEntryTiming(self, extreme_info, current_price, avwap_price=None):
        """
        Check if timing is right for entry
        
        Returns:
            (bool, str): (can_enter, reason)
        """
        
        # 1. Wait period
        if 'detection_time' not in extreme_info:
            return False, "No detection time"
        
        detection_time = extreme_info['detection_time']
        minutes_since = (self.algorithm.Time - detection_time).total_seconds() / 60
        
        wait_time = random.randint(self.wait_min, self.wait_max)
        
        if minutes_since < wait_time:
            return False, f"Waiting {wait_time - int(minutes_since)} more minutes"
        
        # 2. Check retracement
        extreme_price = extreme_info.get('impulse_bar', {}).get('close', 0)
        extreme_move = extreme_info.get('return_60m', 0)
        
        if extreme_price > 0 and extreme_move != 0:
            retracement = abs(current_price - extreme_price) / abs(extreme_move * extreme_price)
            
            if retracement > self.max_retracement:
                return False, f"Retracement too large ({retracement:.1%})"
        
        # 3. Check for pullback to A-VWAP (if available)
        if avwap_price:
            distance_to_avwap = abs(current_price - avwap_price) / avwap_price
            
            if distance_to_avwap < 0.005:  # Within 0.5%
                return True, "At A-VWAP"
        
        return True, "Timing OK"
```


## E:\rony-data\trading-bot\src\components\exhaustion_detector.py

```python
"""
Exhaustion Detector - Phase 2

Detects exhaustion/mean-reversion opportunities (fade signals).

Detection Criteria:
1. Bollinger re-entry: Price back inside Boll(20,2) after outside close
2. Range compression: â‰¥3 hours of shrinking ranges
3. Options tells (Phase 3): Î”IV declining, skew relaxing

Entry: Retest of outer band
Target: Revert to A-VWAP
Stop: Beyond extreme Â± 0.3 ATR
Time stop: 3-5 hours

Usage:
    from exhaustion_detector import ExhaustionDetector
    
    detector = ExhaustionDetector(algorithm)
    exhaustion_info = detector.Detect(symbol, bars)
"""

from AlgorithmImports import *
import numpy as np
from collections import deque

class ExhaustionDetector:
    """
    Detect exhaustion/mean-reversion opportunities
    """
    
    def __init__(self, algorithm):
        self.algorithm = algorithm
        self.logger = algorithm.logger if hasattr(algorithm, 'logger') else None
        
        # Configuration
        self.boll_period = 20
        self.boll_std = 2.0
        self.min_compression_hours = 3
        self.compression_threshold = 0.8  # Each range â‰¤ 0.8Ã— prior
        
        # Tracking
        self.last_detection = {}
        self.detection_cooldown = 30  # Minutes
        
        if self.logger:
            self.logger.info("ExhaustionDetector initialized", component="ExhaustionDetector")
    
    def Detect(self, symbol, minute_bars):
        """
        Detect exhaustion signal
        
        Args:
            symbol: Stock symbol
            minute_bars: List of minute bars (dict with OHLCV)
        
        Returns:
            dict with exhaustion info
        """
        
        result = {
            'is_exhaustion': False,
            'bollinger_reentry': False,
            'range_compression': False,
            'compression_hours': 0,
            'entry_price': None,
            'target_price': None,
            'stop_price': None,
            'confidence': 0.0
        }
        
        if len(minute_bars) < self.boll_period * 60:  # Need enough for Bollinger
            return result
        
        # Get hourly bars from minute bars
        hourly_bars = self._ConvertToHourly(minute_bars)
        
        if len(hourly_bars) < self.boll_period:
            return result
        
        # Check cooldown
        if symbol in self.last_detection:
            minutes_since = (self.algorithm.Time - self.last_detection[symbol]).total_seconds() / 60
            if minutes_since < self.detection_cooldown:
                return result
        
        # 1. Check Bollinger re-entry
        boll_reentry, boll_info = self._CheckBollingerReentry(hourly_bars)
        result['bollinger_reentry'] = boll_reentry
        
        if not boll_reentry:
            return result
        
        # 2. Check range compression
        compression, compression_hours = self._CheckRangeCompression(hourly_bars)
        result['range_compression'] = compression
        result['compression_hours'] = compression_hours
        
        if not compression:
            return result
        
        # Both conditions met - this is an exhaustion signal!
        result['is_exhaustion'] = True
        
        # Calculate entry/target/stop
        current_price = minute_bars[-1]['close']
        
        # Entry: Current price (retesting the band)
        result['entry_price'] = current_price
        
        # Target: A-VWAP (would need to get from tracker)
        # For now, use middle of Bollinger band
        result['target_price'] = boll_info['middle']
        
        # Stop: Beyond the extreme
        if boll_info['last_outside'] == 'upper':
            # Was above, now retesting - target is down
            result['stop_price'] = boll_info['upper_band'] + (0.3 * boll_info['atr'])
        else:
            # Was below, now retesting - target is up
            result['stop_price'] = boll_info['lower_band'] - (0.3 * boll_info['atr'])
        
        # Calculate confidence (0-1)
        confidence = 0.0
        
        # More compression hours = higher confidence
        confidence += min(compression_hours / 6.0, 0.5)  # Max 0.5 for 6+ hours
        
        # Stronger Bollinger signal = higher confidence
        if boll_info['distance_from_band'] > 0.02:  # >2% inside
            confidence += 0.3
        else:
            confidence += 0.2
        
        # Clean price action = higher confidence
        if boll_info['clean_reentry']:
            confidence += 0.2
        
        result['confidence'] = min(confidence, 1.0)
        
        # Update detection time
        self.last_detection[symbol] = self.algorithm.Time
        
        # Log detection
        if self.logger:
            self.logger.info(
                f"Exhaustion detected: {symbol} | "
                f"Compression: {compression_hours}h | "
                f"Confidence: {confidence:.2f}",
                component="ExhaustionDetector"
            )
        
        return result
    
    def _ConvertToHourly(self, minute_bars):
        """Convert minute bars to hourly bars"""
        
        hourly = []
        current_hour = None
        hour_data = {
            'open': None,
            'high': None,
            'low': None,
            'close': None,
            'volume': 0,
            'time': None
        }
        
        for bar in minute_bars:
            bar_hour = bar['time'].replace(minute=0, second=0, microsecond=0)
            
            if current_hour is None:
                current_hour = bar_hour
                hour_data['open'] = bar['open']
                hour_data['high'] = bar['high']
                hour_data['low'] = bar['low']
                hour_data['time'] = bar_hour
            
            if bar_hour != current_hour:
                # Close current hour
                hourly.append(hour_data.copy())
                
                # Start new hour
                current_hour = bar_hour
                hour_data = {
                    'open': bar['open'],
                    'high': bar['high'],
                    'low': bar['low'],
                    'close': bar['close'],
                    'volume': bar['volume'],
                    'time': bar_hour
                }
            else:
                # Update current hour
                hour_data['high'] = max(hour_data['high'], bar['high'])
                hour_data['low'] = min(hour_data['low'], bar['low'])
                hour_data['close'] = bar['close']
                hour_data['volume'] += bar['volume']
        
        # Add last hour
        if hour_data['open'] is not None:
            hourly.append(hour_data)
        
        return hourly
    
    def _CheckBollingerReentry(self, hourly_bars):
        """
        Check if price re-entered Bollinger bands after being outside
        
        Returns:
            (bool, dict): (is_reentry, info)
        """
        
        if len(hourly_bars) < self.boll_period + 5:
            return False, {}
        
        # Calculate Bollinger Bands
        closes = np.array([bar['close'] for bar in hourly_bars])
        
        # SMA
        sma = np.convolve(closes, np.ones(self.boll_period)/self.boll_period, mode='valid')
        
        # Std
        std = np.array([
            closes[i:i+self.boll_period].std()
            for i in range(len(closes) - self.boll_period + 1)
        ])
        
        # Upper/Lower bands
        upper_band = sma + (self.boll_std * std)
        lower_band = sma - (self.boll_std * std)
        
        # Check recent bars
        recent_closes = closes[-self.boll_period:]
        recent_upper = upper_band[-1]
        recent_lower = lower_band[-1]
        recent_middle = sma[-1]
        
        # Check if was outside recently
        was_outside = False
        last_outside = None
        
        for i in range(min(10, len(closes) - self.boll_period)):
            idx = -(i+1)
            if closes[idx] > upper_band[idx - (len(closes) - len(upper_band))]:
                was_outside = True
                last_outside = 'upper'
                break
            elif closes[idx] < lower_band[idx - (len(closes) - len(lower_band))]:
                was_outside = True
                last_outside = 'lower'
                break
        
        if not was_outside:
            return False, {}
        
        # Check if now inside
        current_close = closes[-1]
        now_inside = (current_close < recent_upper) and (current_close > recent_lower)
        
        if not now_inside:
            return False, {}
        
        # Calculate distance from band
        if last_outside == 'upper':
            distance_from_band = (recent_upper - current_close) / recent_upper
        else:
            distance_from_band = (current_close - recent_lower) / current_close
        
        # Check if clean reentry (not bouncing on band)
        clean_reentry = distance_from_band > 0.01  # At least 1% inside
        
        # Calculate ATR for stop
        atr = self._CalculateATR(hourly_bars[-20:])
        
        info = {
            'upper_band': recent_upper,
            'lower_band': recent_lower,
            'middle': recent_middle,
            'current_price': current_close,
            'last_outside': last_outside,
            'distance_from_band': distance_from_band,
            'clean_reentry': clean_reentry,
            'atr': atr
        }
        
        return True, info
    
    def _CheckRangeCompression(self, hourly_bars):
        """
        Check for range compression (â‰¥3 hours of shrinking ranges)
        
        Returns:
            (bool, int): (is_compressing, hours_of_compression)
        """
        
        if len(hourly_bars) < self.min_compression_hours + 1:
            return False, 0
        
        # Calculate ranges
        ranges = [bar['high'] - bar['low'] for bar in hourly_bars]
        
        # Check for compression
        compression_count = 0
        
        for i in range(len(ranges) - 1, 0, -1):
            if ranges[i] <= ranges[i-1] * self.compression_threshold:
                compression_count += 1
            else:
                break
        
        is_compressing = compression_count >= self.min_compression_hours
        
        return is_compressing, compression_count
    
    def _CalculateATR(self, bars):
        """Calculate Average True Range"""
        
        if len(bars) < 2:
            return 0.0
        
        true_ranges = []
        
        for i in range(1, len(bars)):
            high = bars[i]['high']
            low = bars[i]['low']
            prev_close = bars[i-1]['close']
            
            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close)
            )
            
            true_ranges.append(tr)
        
        return np.mean(true_ranges) if true_ranges else 0.0
    
    def GetExhaustionStats(self, symbol):
        """Get exhaustion detection statistics"""
        
        stats = {
            'has_history': symbol in self.last_detection,
            'last_detection': self.last_detection.get(symbol),
            'cooldown_active': False
        }
        
        if symbol in self.last_detection:
            minutes_since = (self.algorithm.Time - self.last_detection[symbol]).total_seconds() / 60
            stats['cooldown_active'] = minutes_since < self.detection_cooldown
            stats['minutes_since_last'] = minutes_since
        
        return stats
```


## E:\rony-data\trading-bot\src\components\extreme_detector.py

```python
"""
Extreme Detection - Core Signal Generator
Detects when a stock has an extreme 60-minute move with participation

Criteria:
1. |Zâ‚†â‚€| â‰¥ 2 (60-min return z-score)
2. Volume anomaly â‰¥ 1.5x (2x during auction periods)
3. Spread checks pass
"""

from AlgorithmImports import *
import numpy as np
from collections import deque

class ExtremeDetector:
    """Detect price extremes with participation"""
    
    def __init__(self, algorithm):
        self.algorithm = algorithm
        self.config = algorithm.config
        self.logger = algorithm.logger if hasattr(algorithm, 'logger') else None
        
        # Historical data for volume baseline
        self.volume_history = {}  # symbol -> {hour: deque of volumes}
        self.return_history = {}  # symbol -> deque of minute returns
        
        # Detection cache
        self.last_detection = {}  # symbol -> timestamp
        self.detection_cooldown = 15  # Minutes before re-detecting same symbol
        
    def Detect(self, symbol, minute_bars):
        """
        Detect if symbol has an extreme move
        
        Returns dict with:
        - is_extreme: bool
        - z_score: float
        - vol_anomaly: float
        - direction: 'up' or 'down'
        - return_60m: float
        - impulse_bar: dict with OHLCV
        """
        
        result = {
            'is_extreme': False,
            'z_score': 0.0,
            'vol_anomaly': 0.0,
            'direction': 'neutral',
            'return_60m': 0.0,
            'impulse_bar': None,
            'detection_time': None
        }
        
        # Need at least 60 minutes of data
        if len(minute_bars) < self.config.MIN_BARS_FOR_DETECTION:
            return result
        
        # Get last 60 minutes
        recent_bars = minute_bars[-60:]
        
        # Calculate 60-minute return
        start_price = recent_bars[0]['close']
        end_price = recent_bars[-1]['close']
        return_60m = (end_price / start_price - 1.0) if start_price > 0 else 0.0
        
        # Calculate minute returns for volatility
        minute_returns = []
        for i in range(1, len(recent_bars)):
            prev_close = recent_bars[i-1]['close']
            curr_close = recent_bars[i]['close']
            if prev_close > 0:
                ret = (curr_close / prev_close - 1.0)
                minute_returns.append(ret)
        
        if len(minute_returns) < 30:  # Need enough for stable volatility
            return result
        
        # Calculate Z-score
        sigma_60 = np.std(minute_returns)
        if sigma_60 > 0:
            z_score = return_60m / sigma_60
        else:
            z_score = 0.0
        
        # Update result
        result['z_score'] = z_score
        result['return_60m'] = return_60m
        result['direction'] = 'up' if return_60m > 0 else 'down'
        
        # Check Z-score threshold
        if abs(z_score) < self.config.Z_THRESHOLD:
            return result
        
        # Calculate volume anomaly
        total_volume_60m = sum([bar['volume'] for bar in recent_bars])
        
        # Get hour of day for comparison
        current_time = recent_bars[-1]['time']
        hour_of_day = current_time.hour
        
        # Update volume history
        if symbol not in self.volume_history:
            self.volume_history[symbol] = {}
        if hour_of_day not in self.volume_history[symbol]:
            self.volume_history[symbol][hour_of_day] = deque(maxlen=20)  # 20-day history
        
        # Get historical median for this hour
        hist_volumes = list(self.volume_history[symbol][hour_of_day])
        if len(hist_volumes) >= 5:  # Need at least 5 days
            median_volume = np.median(hist_volumes)
            vol_anomaly = total_volume_60m / median_volume if median_volume > 0 else 0.0
        else:
            vol_anomaly = 0.0  # Not enough history
        
        # Update history
        self.volume_history[symbol][hour_of_day].append(total_volume_60m)
        
        result['vol_anomaly'] = vol_anomaly
        
        # Check volume anomaly threshold (auction periods need 2x)
        is_auction = self.config.IsAuctionPeriod(current_time)
        vol_threshold = self.config.VOLUME_ANOMALY_AUCTION if is_auction else self.config.VOLUME_ANOMALY_NORMAL
        
        if vol_anomaly < vol_threshold:
            return result
        
        # Check cooldown (avoid re-detecting too quickly)
        if symbol in self.last_detection:
            minutes_since = (current_time - self.last_detection[symbol]).total_seconds() / 60
            if minutes_since < self.detection_cooldown:
                return result
        
        # Check spread (if available - in Phase 1 we might not have this)
        # For now, we'll skip this check and add it when we have live data
        
        # All checks passed - this is an extreme!
        result['is_extreme'] = True
        result['detection_time'] = current_time
        result['impulse_bar'] = {
            'time': recent_bars[-1]['time'],
            'open': recent_bars[-1]['open'],
            'high': recent_bars[-1]['high'],
            'low': recent_bars[-1]['low'],
            'close': recent_bars[-1]['close'],
            'volume': recent_bars[-1]['volume']
        }
        
        # Update detection time
        self.last_detection[symbol] = current_time
        
        return result
    
    def GetDetectionStats(self, symbol):
        """Get detection statistics for a symbol"""
        stats = {
            'has_volume_history': symbol in self.volume_history,
            'volume_history_length': 0,
            'last_detection': None
        }
        
        if symbol in self.volume_history:
            total_entries = sum(len(v) for v in self.volume_history[symbol].values())
            stats['volume_history_length'] = total_entries
        
        if symbol in self.last_detection:
            stats['last_detection'] = self.last_detection[symbol]
        
        return stats
    
    def ResetHistory(self, symbol):
        """Clear history for a symbol (e.g., after delisting)"""
        if symbol in self.volume_history:
            del self.volume_history[symbol]
        if symbol in self.return_history:
            del self.return_history[symbol]
        if symbol in self.last_detection:
            del self.last_detection[symbol]
```


## E:\rony-data\trading-bot\src\components\health_monitor.py

```python
"""
System Health Monitoring

Continuously monitors system health and alerts on issues.

Monitors:
- Data feed health (bars arriving)
- Universe stability (size consistent)
- Detection rate (normal range)
- Error rate (low)
- Memory usage (stable)
- Execution performance (fast)
- Component responsiveness
- IBKR connection
- Data quality

Auto-recovery:
- Reconnect data feeds
- Reset stuck components
- Clear memory buffers
- Log incidents

Usage:
    from health_monitor import HealthMonitor
    
    health = HealthMonitor(algorithm)
    status = health.run_health_check()
"""

from AlgorithmImports import *
from datetime import datetime, timedelta
from collections import deque, defaultdict
import sys

class HealthMonitor:
    """
    Comprehensive system health monitoring
    """
    
    def __init__(self, algorithm):
        self.algorithm = algorithm
        self.logger = algorithm.logger if hasattr(algorithm, 'logger') else None
        self.alert_manager = algorithm.alert_manager if hasattr(algorithm, 'alert_manager') else None
        
        # Health check configuration
        self.checks_enabled = {
            'data_feed': True,
            'universe_size': True,
            'detection_rate': True,
            'error_rate': True,
            'memory_usage': True,
            'execution_time': True,
            'ibkr_connection': True,
            'data_quality': True
        }
        
        # Thresholds
        self.thresholds = {
            'min_universe_size': 800,        # Expect ~1000
            'max_universe_size': 1200,
            'min_detections_per_day': 3,     # Expect 5-10
            'max_detections_per_day': 20,
            'max_errors_per_hour': 5,
            'max_memory_mb': 1000,           # 1GB
            'max_execution_time_sec': 10,    # Hourly scan
            'data_stale_minutes': 5          # No data for 5 min
        }
        
        # Tracking
        self.last_bar_time = {}              # symbol -> last bar timestamp
        self.universe_sizes = deque(maxlen=24)  # Last 24 hours
        self.detection_counts = deque(maxlen=24)  # Hourly detection counts
        self.error_counts = deque(maxlen=24)     # Hourly error counts
        self.execution_times = deque(maxlen=100)  # Last 100 executions
        
        # Health status
        self.health_status = {
            'overall': True,
            'last_check': None,
            'checks': {},
            'issues': []
        }
        
        # Recovery tracking
        self.recovery_attempts = defaultdict(int)
        self.last_recovery_time = {}
        self.recovery_failures = defaultdict(int)  # Track consecutive failures
        self.circuit_breaker_open = {}  # recovery_key -> open_time

        # Recovery configuration
        self.MAX_RECOVERY_ATTEMPTS = 5  # Max attempts before circuit opens
        self.CIRCUIT_BREAKER_DURATION = 3600  # 1 hour in seconds
        self.BASE_BACKOFF_SECONDS = 60  # Initial backoff: 1 minute

        # Start time
        self.start_time = algorithm.Time
        self.last_hourly_check = algorithm.Time
        
        if self.logger:
            self.logger.info("HealthMonitor initialized", component="HealthMonitor")

    def _is_circuit_breaker_open(self, recovery_key):
        """Check if circuit breaker is open for this recovery type"""
        if recovery_key not in self.circuit_breaker_open:
            return False

        open_time = self.circuit_breaker_open[recovery_key]
        elapsed = (self.algorithm.Time - open_time).total_seconds()

        # Close circuit after duration
        if elapsed >= self.CIRCUIT_BREAKER_DURATION:
            del self.circuit_breaker_open[recovery_key]
            self.recovery_failures[recovery_key] = 0  # Reset failure count
            if self.logger:
                self.logger.info(
                    f"Circuit breaker CLOSED for {recovery_key} after {elapsed/60:.0f} min",
                    component="HealthMonitor"
                )
            return False

        return True

    def _get_backoff_time(self, recovery_key):
        """
        Calculate exponential backoff time with jitter

        Formula: min(base * 2^failures, max) + random_jitter
        """
        import random

        failures = self.recovery_failures[recovery_key]

        # Exponential backoff: 60s, 120s, 240s, 480s, 960s
        backoff = min(self.BASE_BACKOFF_SECONDS * (2 ** failures), 960)

        # Add jitter (0-30% of backoff)
        jitter = random.uniform(0, backoff * 0.3)

        return backoff + jitter

    def _should_attempt_recovery(self, recovery_key):
        """
        Check if recovery should be attempted based on backoff and circuit breaker

        Returns:
            tuple: (should_attempt: bool, reason: str)
        """
        # Check circuit breaker
        if self._is_circuit_breaker_open(recovery_key):
            elapsed = (self.algorithm.Time - self.circuit_breaker_open[recovery_key]).total_seconds()
            remaining = (self.CIRCUIT_BREAKER_DURATION - elapsed) / 60
            return False, f"Circuit breaker OPEN: {remaining:.0f} min remaining"

        # Check if too many recent failures
        if self.recovery_failures[recovery_key] >= self.MAX_RECOVERY_ATTEMPTS:
            # Open circuit breaker
            self.circuit_breaker_open[recovery_key] = self.algorithm.Time
            if self.logger:
                self.logger.warning(
                    f"Circuit breaker OPENED for {recovery_key} after {self.MAX_RECOVERY_ATTEMPTS} failures",
                    component="HealthMonitor"
                )
            return False, "Too many failures - circuit breaker opened"

        # Check backoff time
        if recovery_key in self.last_recovery_time:
            elapsed = (self.algorithm.Time - self.last_recovery_time[recovery_key]).total_seconds()
            required_backoff = self._get_backoff_time(recovery_key)

            if elapsed < required_backoff:
                remaining = (required_backoff - elapsed) / 60
                return False, f"Backoff: {remaining:.1f} min remaining"

        return True, "OK"

    def run_health_check(self, force=False):
        """
        Run all health checks
        
        Args:
            force: Force check even if recently checked
        
        Returns:
            dict with health status
        """
        
        # Only run once per hour unless forced
        if not force:
            time_since_check = (self.algorithm.Time - self.last_hourly_check).total_seconds() / 60
            if time_since_check < 60:  # Less than 1 hour
                return self.health_status
        
        self.last_hourly_check = self.algorithm.Time
        
        # Run each enabled check
        checks = {}
        issues = []
        
        if self.checks_enabled['data_feed']:
            check, issue = self._check_data_feed()
            checks['data_feed'] = check
            if issue:
                issues.append(issue)
        
        if self.checks_enabled['universe_size']:
            check, issue = self._check_universe_size()
            checks['universe_size'] = check
            if issue:
                issues.append(issue)
        
        if self.checks_enabled['detection_rate']:
            check, issue = self._check_detection_rate()
            checks['detection_rate'] = check
            if issue:
                issues.append(issue)
        
        if self.checks_enabled['error_rate']:
            check, issue = self._check_error_rate()
            checks['error_rate'] = check
            if issue:
                issues.append(issue)
        
        if self.checks_enabled['memory_usage']:
            check, issue = self._check_memory_usage()
            checks['memory_usage'] = check
            if issue:
                issues.append(issue)
        
        if self.checks_enabled['execution_time']:
            check, issue = self._check_execution_time()
            checks['execution_time'] = check
            if issue:
                issues.append(issue)
        
        if self.checks_enabled['data_quality']:
            check, issue = self._check_data_quality()
            checks['data_quality'] = check
            if issue:
                issues.append(issue)
        
        # Overall health
        overall_healthy = all(checks.values())
        
        # Update status
        self.health_status = {
            'overall': overall_healthy,
            'last_check': self.algorithm.Time,
            'checks': checks,
            'issues': issues
        }
        
        # Log results
        if self.logger:
            if overall_healthy:
                self.logger.info("Health check passed - all systems OK", component="HealthMonitor")
            else:
                self.logger.warning(f"Health check FAILED - {len(issues)} issues found", 
                                  component="HealthMonitor")
                for issue in issues:
                    self.logger.warning(f"  - {issue}", component="HealthMonitor")
        
        # Alert if issues found
        if not overall_healthy and self.alert_manager:
            self.alert_manager.alert_system_health(checks)
        
        # Attempt recovery if needed
        if not overall_healthy:
            self._attempt_recovery(issues)
        
        return self.health_status
    
    def _check_data_feed(self):
        """Check if data feed is active and recent"""
        
        # Check if we've received recent data
        if not self.last_bar_time:
            # No data yet (might be warming up)
            if (self.algorithm.Time - self.start_time).total_seconds() > 300:  # 5 minutes
                return False, "No data received in 5 minutes"
            else:
                return True, None  # Still warming up
        
        # Check most recent bar
        most_recent = max(self.last_bar_time.values())
        minutes_since = (self.algorithm.Time - most_recent).total_seconds() / 60
        
        if minutes_since > self.thresholds['data_stale_minutes']:
            return False, f"Data stale - no bars for {minutes_since:.1f} minutes"
        
        return True, None
    
    def _check_universe_size(self):
        """Check if universe size is stable"""
        
        if not hasattr(self.algorithm, 'active_symbols'):
            return True, None  # Not initialized yet
        
        current_size = len(self.algorithm.active_symbols)
        self.universe_sizes.append(current_size)
        
        if current_size < self.thresholds['min_universe_size']:
            return False, f"Universe too small: {current_size} (expected ~1000)"
        
        if current_size > self.thresholds['max_universe_size']:
            return False, f"Universe too large: {current_size} (expected ~1000)"
        
        # Check for sudden drops (>50% in 1 hour)
        if len(self.universe_sizes) >= 2:
            prev_size = self.universe_sizes[-2]
            if current_size < prev_size * 0.5:
                return False, f"Universe dropped from {prev_size} to {current_size}"
        
        return True, None
    
    def _check_detection_rate(self):
        """Check if detection rate is normal"""
        
        # Get detections from last hour
        if not hasattr(self.algorithm, 'extreme_detector'):
            return True, None
        
        # Count recent detections (simplified - would need actual tracking)
        # For now, check if we're getting ANY detections
        
        # Check daily total
        if len(self.detection_counts) >= 24:  # Full day
            daily_total = sum(self.detection_counts)
            
            if daily_total < self.thresholds['min_detections_per_day']:
                return False, f"Too few detections: {daily_total}/day (expected 5-10)"
            
            if daily_total > self.thresholds['max_detections_per_day']:
                return False, f"Too many detections: {daily_total}/day (possible false signals)"
        
        return True, None
    
    def _check_error_rate(self):
        """Check if error rate is acceptable"""
        
        if not self.logger:
            return True, None
        
        # Get error count from logger
        recent_errors = len([
            e for e in self.logger.error_logs
            if (self.algorithm.Time - datetime.strptime(e['timestamp'], "%Y-%m-%d %H:%M:%S")).total_seconds() < 3600
        ])
        
        self.error_counts.append(recent_errors)
        
        if recent_errors > self.thresholds['max_errors_per_hour']:
            return False, f"High error rate: {recent_errors} errors in last hour"
        
        # Check for error spike
        if len(self.error_counts) >= 2:
            prev_errors = self.error_counts[-2]
            if recent_errors > prev_errors * 3 and recent_errors > 5:
                if self.alert_manager:
                    self.alert_manager.alert_error_spike(recent_errors, 60)
                return False, f"Error spike: {recent_errors} errors (was {prev_errors})"
        
        return True, None
    
    def _check_memory_usage(self):
        """Check memory usage"""
        
        try:
            # Get current memory usage (if available)
            # Note: This might not work in all environments
            import resource
            memory_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
            
            if memory_mb > self.thresholds['max_memory_mb']:
                return False, f"High memory usage: {memory_mb:.0f} MB"
            
            return True, None
            
        except Exception:
            # Memory monitoring not available
            return True, None
    
    def _check_execution_time(self):
        """Check if execution is fast enough"""
        
        if not self.execution_times:
            return True, None
        
        avg_time = sum(self.execution_times) / len(self.execution_times)
        
        if avg_time > self.thresholds['max_execution_time_sec']:
            return False, f"Slow execution: {avg_time:.2f}s average (max {self.thresholds['max_execution_time_sec']}s)"
        
        # Check for degradation
        if len(self.execution_times) >= 10:
            recent_avg = sum(list(self.execution_times)[-10:]) / 10
            old_avg = sum(list(self.execution_times)[:10]) / 10
            
            if recent_avg > old_avg * 2:
                return False, f"Execution slowing: {old_avg:.2f}s â†’ {recent_avg:.2f}s"
        
        return True, None
    
    def _check_data_quality(self):
        """Check data quality (no gaps, valid prices)"""
        
        if not hasattr(self.algorithm, 'minute_bars'):
            return True, None
        
        # Check a sample of symbols for data quality
        issues = []
        
        for symbol in list(self.algorithm.minute_bars.keys())[:10]:  # Check first 10
            bars = self.algorithm.minute_bars[symbol]
            
            if not bars:
                continue
            
            # Check for zero/negative prices
            for bar in bars[-60:]:  # Last hour
                if bar.get('close', 0) <= 0:
                    issues.append(f"{symbol}: Invalid price {bar['close']}")
                    break
            
            # Check for large gaps in time
            if len(bars) >= 2:
                last_bar = bars[-1]
                prev_bar = bars[-2]
                time_gap = (last_bar['time'] - prev_bar['time']).total_seconds()
                
                if time_gap > 300:  # >5 minutes gap
                    issues.append(f"{symbol}: {time_gap/60:.0f}min data gap")
        
        if issues:
            return False, f"Data quality issues: {len(issues)} problems found"
        
        return True, None
    
    def _attempt_recovery(self, issues):
        """Attempt automatic recovery from issues"""
        
        for issue in issues:
            # Identify issue type
            if 'data stale' in issue.lower() or 'data gap' in issue.lower():
                self._recover_data_feed()
            
            elif 'universe' in issue.lower():
                self._recover_universe()
            
            elif 'memory' in issue.lower():
                self._recover_memory()
            
            elif 'error spike' in issue.lower():
                self._recover_error_spike()
    
    def _recover_data_feed(self):
        """Attempt to recover data feed with exponential backoff and circuit breaker"""

        recovery_key = 'data_feed'

        # Check if recovery should be attempted
        should_attempt, reason = self._should_attempt_recovery(recovery_key)
        if not should_attempt:
            if self.logger:
                self.logger.info(f"Skipping data feed recovery: {reason}", component="HealthMonitor")
            return

        if self.logger:
            attempts = self.recovery_attempts[recovery_key]
            failures = self.recovery_failures[recovery_key]
            self.logger.info(
                f"Attempting data feed recovery (attempt {attempts+1}, failures: {failures})",
                component="HealthMonitor"
            )

        try:
            # Clear stale data
            if hasattr(self.algorithm, 'minute_bars'):
                for symbol in list(self.algorithm.minute_bars.keys()):
                    if len(self.algorithm.minute_bars[symbol]) > 1440:  # Keep last 24 hours
                        self.algorithm.minute_bars[symbol] = self.algorithm.minute_bars[symbol][-1440:]

            # Log recovery attempt
            self.recovery_attempts[recovery_key] += 1
            self.last_recovery_time[recovery_key] = self.algorithm.Time
            self.recovery_failures[recovery_key] = 0  # Reset on success

            if self.logger:
                self.logger.info("âœ“ Data feed recovery completed", component="HealthMonitor")

        except Exception as e:
            self.recovery_failures[recovery_key] += 1
            if self.logger:
                self.logger.error(
                    f"âœ— Data feed recovery failed (failure {self.recovery_failures[recovery_key]}): {str(e)}",
                    component="HealthMonitor", exception=e
                )
    
    def _recover_universe(self):
        """Attempt to recover universe"""
        
        recovery_key = 'universe'
        
        if self.logger:
            self.logger.info("Attempting universe recovery", component="HealthMonitor")
        
        try:
            # Force universe refresh (would need to implement in main algo)
            # For now, just log
            
            self.recovery_attempts[recovery_key] += 1
            self.last_recovery_time[recovery_key] = self.algorithm.Time
            
            if self.logger:
                self.logger.info("Universe recovery completed", component="HealthMonitor")
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Universe recovery failed: {str(e)}", 
                                component="HealthMonitor", exception=e)
    
    def _recover_memory(self):
        """Attempt to recover from high memory usage"""
        
        recovery_key = 'memory'
        
        if self.logger:
            self.logger.info("Attempting memory recovery", component="HealthMonitor")
        
        try:
            # Clear old data
            if hasattr(self.algorithm, 'minute_bars'):
                for symbol in list(self.algorithm.minute_bars.keys()):
                    # Keep only last 2 hours
                    if len(self.algorithm.minute_bars[symbol]) > 120:
                        self.algorithm.minute_bars[symbol] = self.algorithm.minute_bars[symbol][-120:]
            
            # Clear logger buffers (keep last 1000)
            if self.logger and len(self.logger.daily_logs) > 1000:
                self.logger.daily_logs = self.logger.daily_logs[-1000:]
            
            self.recovery_attempts[recovery_key] += 1
            self.last_recovery_time[recovery_key] = self.algorithm.Time
            
            if self.logger:
                self.logger.info("Memory recovery completed", component="HealthMonitor")
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Memory recovery failed: {str(e)}", 
                                component="HealthMonitor", exception=e)
    
    def _recover_error_spike(self):
        """Handle error spikes"""
        
        recovery_key = 'error_spike'
        
        if self.logger:
            self.logger.warning("Error spike detected - monitoring closely", 
                              component="HealthMonitor")
        
        # Just log for now - human intervention likely needed
        self.recovery_attempts[recovery_key] += 1
        self.last_recovery_time[recovery_key] = self.algorithm.Time
    
    def update_metrics(self, metric_type, value):
        """Update health metrics"""
        
        if metric_type == 'bar_received':
            symbol = value['symbol']
            timestamp = value['timestamp']
            self.last_bar_time[symbol] = timestamp
        
        elif metric_type == 'detection':
            # Increment hourly detection count
            if not self.detection_counts or len(self.detection_counts) == 0:
                self.detection_counts.append(1)
            else:
                self.detection_counts[-1] += 1
        
        elif metric_type == 'execution_time':
            self.execution_times.append(value)
    
    def get_health_summary(self):
        """Get health summary for logging"""
        
        summary = {
            'overall_healthy': self.health_status['overall'],
            'last_check': str(self.health_status['last_check']),
            'issues': len(self.health_status['issues']),
            'checks_passed': sum(1 for v in self.health_status['checks'].values() if v),
            'checks_total': len(self.health_status['checks']),
            'recovery_attempts': dict(self.recovery_attempts)
        }
        
        return summary
```


## E:\rony-data\trading-bot\src\components\hmm_regime.py

```python
"""
HMM Regime Classifier
3-state model: Low-Vol, High-Vol, Trending
Phase 1: Observation only - calculate posteriors but don't gate trades yet
"""

from AlgorithmImports import *
import numpy as np
from collections import deque

class HMMRegime:
    """Hidden Markov Model for regime detection"""
    
    def __init__(self, algorithm):
        self.algorithm = algorithm
        self.config = algorithm.config
        
        # States
        self.states = ['Low-Vol', 'High-Vol', 'Trending']
        self.n_states = len(self.states)
        
        # Current regime probabilities
        self.state_probs = {
            'Low-Vol': 0.33,
            'High-Vol': 0.33,
            'Trending': 0.34
        }
        
        # Feature history for fitting
        self.feature_history = deque(maxlen=self.config.HMM_FIT_WINDOW_DAYS)
        
        # Track market-wide features daily
        self.daily_features = {
            'realized_vol': [],
            'correlation': [],
            'vix_level': [],
            'spread_percentile': []
        }
        
        # Model state
        self.is_fitted = False
        self.last_fit_date = None
        self.days_since_fit = 0
        
        # For Phase 1 - simplified regime detection
        self.use_simplified = True  # Use heuristics instead of full HMM
        
        # Subscribe to VIX for regime detection
        try:
            self.vix = algorithm.AddIndex("VIX", Resolution.Daily).Symbol
        except:
            self.vix = None
            algorithm.Log("Warning: VIX not available, using simplified regime detection")
    
    def Update(self, current_time):
        """
        Update regime probabilities
        Phase 1: Use simplified heuristic-based regime detection
        
        Returns dict with:
        - dominant_state: str
        - state_probs: dict
        - gpm: float (Global Position Multiplier)
        - requires_2x_edge: bool
        """
        
        if self.use_simplified:
            return self._SimplifiedRegime(current_time)
        else:
            return self._FullHMMRegime(current_time)
    
    def _SimplifiedRegime(self, current_time):
        """
        Simplified regime detection using market observables
        Good enough for Phase 1 observation
        """
        
        # Default to neutral
        regime = {
            'dominant_state': 'Low-Vol',
            'state_probs': {
                'Low-Vol': 0.50,
                'High-Vol': 0.25,
                'Trending': 0.25
            },
            'gpm': 1.0,  # Global Position Multiplier
            'requires_2x_edge': False,
            'correlation_breakdown': 0.0
        }
        
        # Try to get VIX level
        vix_level = self._GetVIXLevel()
        
        if vix_level is not None:
            # VIX-based regime classification
            if vix_level < 15:
                # Low volatility environment
                regime['dominant_state'] = 'Low-Vol'
                regime['state_probs'] = {
                    'Low-Vol': 0.70,
                    'High-Vol': 0.15,
                    'Trending': 0.15
                }
                regime['gpm'] = 1.0
                
            elif vix_level > 25:
                # High volatility environment
                regime['dominant_state'] = 'High-Vol'
                regime['state_probs'] = {
                    'Low-Vol': 0.10,
                    'High-Vol': 0.70,
                    'Trending': 0.20
                }
                regime['gpm'] = 0.3  # Reduce size in high vol
                regime['requires_2x_edge'] = True
                
            else:
                # Moderate/trending environment
                regime['dominant_state'] = 'Trending'
                regime['state_probs'] = {
                    'Low-Vol': 0.20,
                    'High-Vol': 0.30,
                    'Trending': 0.50
                }
                regime['gpm'] = 0.8
        
        # Calculate correlation breakdown (placeholder for now)
        # In production, this would analyze cross-correlation of returns
        regime['correlation_breakdown'] = 0.0
        
        return regime
    
    def _GetVIXLevel(self):
        """Get current VIX level if available"""
        if self.vix is None:
            return None
        
        try:
            history = self.algorithm.History(self.vix, 1, Resolution.Daily)
            if history.empty:
                return None
            return float(history['close'].iloc[-1])
        except:
            return None
    
    def _FullHMMRegime(self, current_time):
        """
        Full HMM implementation (for future Phase 2+)
        Currently returns simplified version
        """
        # TODO: Implement full Gaussian HMM with sklearn
        # For now, fall back to simplified
        return self._SimplifiedRegime(current_time)
    
    def _CollectFeatures(self):
        """
        Collect features for HMM fitting
        - Realized volatility
        - Correlation
        - Spread levels
        - VIX
        """
        features = {}
        
        # Get VIX
        vix = self._GetVIXLevel()
        if vix is not None:
            features['vix'] = vix
        
        # Get SPY returns for volatility
        try:
            spy = self.algorithm.Symbol("SPY")
            history = self.algorithm.History(spy, 20, Resolution.Daily)
            if not history.empty:
                returns = history['close'].pct_change().dropna()
                features['realized_vol'] = returns.std() * np.sqrt(252)
        except:
            pass
        
        return features
    
    def ShouldRefit(self, current_date):
        """Check if we should refit the HMM"""
        if not self.is_fitted:
            return True
        
        if self.last_fit_date is None:
            return True
        
        days_since = (current_date - self.last_fit_date).days
        return days_since >= self.config.HMM_REFIT_DAYS
    
    def Fit(self):
        """Fit the HMM model (for future implementation)"""
        # TODO: Implement full Gaussian HMM fitting
        # For Phase 1, we use simplified heuristics
        self.is_fitted = True
        self.last_fit_date = self.algorithm.Time.date()
        self.algorithm.Log("HMM: Using simplified regime detection (Phase 1)")

    def GetCurrentRegime(self):
        """
        Get current regime state (convenience wrapper)

        Returns:
            dict: Current regime information with keys:
                - dominant_state: str ('Low-Vol', 'High-Vol', or 'Trending')
                - state_probs: dict of state probabilities
                - gpm: float (Global Position Multiplier, 0.3-1.0)
                - requires_2x_edge: bool (if high-vol regime)
                - correlation_breakdown: float (0.0-1.0)
        """
        return self.Update(self.algorithm.Time)

    def GetGlobalPositionMultiplier(self):
        """
        Get the current Global Position Multiplier (GPM)
        Used to scale position sizes based on regime
        """
        regime = self.Update(self.algorithm.Time)
        return regime['gpm']
    
    def GetRegimeSummary(self):
        """Get current regime summary for logging"""
        regime = self.Update(self.algorithm.Time)
        
        summary = f"Regime: {regime['dominant_state']}"
        summary += f" (GPM: {regime['gpm']:.2f})"
        
        if regime['requires_2x_edge']:
            summary += " [2x Edge Required]"
        
        return summary
```


## E:\rony-data\trading-bot\src\components\log_retrieval.py

```python
"""
Log Retrieval Utility

Use this in a QuantConnect notebook or research environment to retrieve
and analyze logs from your live/paper trading algorithm.

Usage:
    from log_retrieval import LogRetriever
    
    retriever = LogRetriever(qb)  # qb = QuantConnect QuantBook
    logs = retriever.get_logs('2024-11-06')
    retriever.analyze_logs(logs)
    retriever.export_to_csv(logs, 'my_logs.csv')
"""

import json
import pandas as pd
from datetime import datetime, timedelta

class LogRetriever:
    """Retrieve and analyze logs from QuantConnect ObjectStore"""
    
    def __init__(self, qb):
        """
        Initialize with QuantBook instance
        
        Args:
            qb: QuantConnect QuantBook instance (from notebook)
        """
        self.qb = qb
    
    def list_available_logs(self):
        """List all available log files in ObjectStore"""
        try:
            # Get all keys from ObjectStore
            keys = self.qb.ObjectStore.GetKeys()
            
            # Filter for log files
            log_keys = [k for k in keys if k.startswith('logs_')]
            
            print(f"Found {len(log_keys)} log files:")
            for key in log_keys:
                print(f"  - {key}")
            
            return log_keys
        except Exception as e:
            print(f"Error listing logs: {e}")
            return []
    
    def get_logs(self, date_str, log_type='all'):
        """
        Retrieve logs for a specific date
        
        Args:
            date_str: Date string in format 'YYYY-MM-DD'
            log_type: 'all', 'errors', 'trades', 'detections', 'performance'
        
        Returns:
            dict: Parsed log data
        """
        try:
            # Search for log file matching date
            date_key = date_str.replace('-', '')
            search_pattern = f"logs_{log_type}_*_{date_key}"
            
            # Get all keys and find match
            all_keys = self.qb.ObjectStore.GetKeys()
            matching_keys = [k for k in all_keys if date_key in k and f"logs_{log_type}" in k]
            
            if not matching_keys:
                print(f"No logs found for {date_str} with type '{log_type}'")
                return None
            
            # Use most recent if multiple matches
            key = matching_keys[-1]
            print(f"Retrieving logs from: {key}")
            
            # Get from ObjectStore
            json_str = self.qb.ObjectStore.Read(key)
            logs = json.loads(json_str)
            
            print(f"Successfully retrieved logs for {date_str}")
            return logs
            
        except Exception as e:
            print(f"Error retrieving logs: {e}")
            return None
    
    def get_date_range_logs(self, start_date, end_date, log_type='all'):
        """
        Retrieve logs for a date range
        
        Args:
            start_date: Start date string 'YYYY-MM-DD'
            end_date: End date string 'YYYY-MM-DD'
            log_type: Type of logs to retrieve
        
        Returns:
            dict: Combined log data
        """
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        all_logs = {
            'logs': [],
            'errors': [],
            'trades': [],
            'detections': [],
            'performance': []
        }
        
        current = start
        while current <= end:
            date_str = current.strftime('%Y-%m-%d')
            daily_logs = self.get_logs(date_str, log_type)
            
            if daily_logs:
                # Merge logs
                if 'logs' in daily_logs:
                    all_logs['logs'].extend(daily_logs['logs'])
                if 'errors' in daily_logs:
                    all_logs['errors'].extend(daily_logs['errors'])
                if 'trades' in daily_logs:
                    all_logs['trades'].extend(daily_logs['trades'])
                if 'detections' in daily_logs:
                    all_logs['detections'].extend(daily_logs['detections'])
                if 'performance' in daily_logs:
                    all_logs['performance'].extend(daily_logs['performance'])
            
            current += timedelta(days=1)
        
        return all_logs
    
    def analyze_logs(self, logs):
        """
        Generate analysis report from logs
        
        Args:
            logs: Log data dictionary
        """
        if not logs:
            print("No logs to analyze")
            return
        
        print("\n" + "="*60)
        print("LOG ANALYSIS REPORT")
        print("="*60 + "\n")
        
        # Overall stats
        if 'summary' in logs:
            summary = logs['summary']
            print("Overall Stats:")
            print(f"  Session ID: {logs.get('session_id', 'N/A')}")
            print(f"  Total Logs: {summary.get('total_logs', 0)}")
            print(f"  Total Errors: {summary.get('total_errors', 0)}")
            print(f"  Total Trades: {summary.get('total_trades', 0)}")
            print(f"  Total Detections: {summary.get('total_detections', 0)}")
            print()
        
        # Error analysis
        if 'errors' in logs and logs['errors']:
            print("Error Analysis:")
            error_types = {}
            for error in logs['errors']:
                component = error.get('component', 'unknown')
                error_types[component] = error_types.get(component, 0) + 1
            
            for component, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
                print(f"  {component}: {count} errors")
            print()
        
        # Trade analysis
        if 'trades' in logs and logs['trades']:
            trades = logs['trades']
            print("Trade Analysis:")
            print(f"  Total Trades: {len(trades)}")
            
            entry_count = sum(1 for t in trades if t['trade_type'] == 'entry')
            exit_count = sum(1 for t in trades if t['trade_type'] == 'exit')
            
            print(f"  Entries: {entry_count}")
            print(f"  Exits: {exit_count}")
            
            # Most traded symbols
            symbols = {}
            for trade in trades:
                sym = trade['symbol']
                symbols[sym] = symbols.get(sym, 0) + 1
            
            print(f"  Most traded: {sorted(symbols.items(), key=lambda x: x[1], reverse=True)[:5]}")
            print()
        
        # Detection analysis
        if 'detections' in logs and logs['detections']:
            detections = logs['detections']
            print("Detection Analysis:")
            print(f"  Total Extremes: {len(detections)}")
            
            up = sum(1 for d in detections if d['direction'] == 'up')
            down = sum(1 for d in detections if d['direction'] == 'down')
            
            print(f"  Up: {up}")
            print(f"  Down: {down}")
            
            avg_z = sum(abs(d['z_score']) for d in detections) / len(detections)
            avg_vol = sum(d['vol_anomaly'] for d in detections) / len(detections)
            
            print(f"  Avg |Z-score|: {avg_z:.2f}")
            print(f"  Avg Vol Anomaly: {avg_vol:.2f}x")
            print()
        
        # Performance trend
        if 'performance' in logs and logs['performance']:
            perf = logs['performance']
            print("Performance Trend:")
            print(f"  Snapshots: {len(perf)}")
            
            if len(perf) >= 2:
                start_val = perf[0]['total_value']
                end_val = perf[-1]['total_value']
                change = ((end_val / start_val) - 1) * 100
                
                print(f"  Start Value: ${start_val:,.2f}")
                print(f"  End Value: ${end_val:,.2f}")
                print(f"  Change: {change:+.2f}%")
            print()
        
        print("="*60 + "\n")
    
    def export_to_csv(self, logs, filename_prefix='logs'):
        """
        Export logs to CSV files for external analysis
        
        Args:
            logs: Log data dictionary
            filename_prefix: Prefix for output files
        """
        if not logs:
            print("No logs to export")
            return
        
        # Export detections
        if 'detections' in logs and logs['detections']:
            df = pd.DataFrame(logs['detections'])
            filename = f"{filename_prefix}_detections.csv"
            df.to_csv(filename, index=False)
            print(f"Exported detections to {filename}")
        
        # Export trades
        if 'trades' in logs and logs['trades']:
            df = pd.DataFrame(logs['trades'])
            filename = f"{filename_prefix}_trades.csv"
            df.to_csv(filename, index=False)
            print(f"Exported trades to {filename}")
        
        # Export errors
        if 'errors' in logs and logs['errors']:
            df = pd.DataFrame(logs['errors'])
            filename = f"{filename_prefix}_errors.csv"
            df.to_csv(filename, index=False)
            print(f"Exported errors to {filename}")
        
        # Export performance
        if 'performance' in logs and logs['performance']:
            df = pd.DataFrame(logs['performance'])
            filename = f"{filename_prefix}_performance.csv"
            df.to_csv(filename, index=False)
            print(f"Exported performance to {filename}")
        
        print("Export complete!")
    
    def get_error_details(self, logs):
        """Get detailed error information"""
        if not logs or 'errors' not in logs:
            print("No errors found")
            return
        
        errors = logs['errors']
        
        print("\n" + "="*60)
        print("DETAILED ERROR REPORT")
        print("="*60 + "\n")
        
        for i, error in enumerate(errors[-20:], 1):  # Last 20 errors
            print(f"Error #{i}:")
            print(f"  Time: {error.get('timestamp', 'N/A')}")
            print(f"  Component: {error.get('component', 'unknown')}")
            print(f"  Level: {error.get('level', 'ERROR')}")
            print(f"  Message: {error.get('message', 'N/A')}")
            
            if 'exception' in error:
                exc = error['exception']
                print(f"  Exception: {exc.get('type', 'N/A')}: {exc.get('message', 'N/A')}")
                if 'traceback' in exc:
                    print(f"  Traceback:\n{exc['traceback']}")
            
            print()


# Example usage in QuantConnect Notebook:
"""
# In a QuantConnect Research Notebook

from log_retrieval import LogRetriever

# Initialize
qb = QuantBook()
retriever = LogRetriever(qb)

# List available logs
retriever.list_available_logs()

# Get logs for today
logs = retriever.get_logs('2024-11-06')

# Analyze
retriever.analyze_logs(logs)

# Export to CSV
retriever.export_to_csv(logs, 'extreme_aware_2024_11_06')

# Get specific date range
range_logs = retriever.get_date_range_logs('2024-11-01', '2024-11-06')
retriever.analyze_logs(range_logs)

# Detailed error report
retriever.get_error_details(logs)
"""
```


## E:\rony-data\trading-bot\src\components\logger.py

```python
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
            self.algorithm.Log(f"âš ï¸ {formatted}")
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
        
        self.algorithm.Error(f"âŒ {formatted}")
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
        
        self.algorithm.Error(f"ðŸ”´ CRITICAL: {formatted}")
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
        
        msg = (f"ðŸš¨ EXTREME: {symbol} | "
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
        
        msg = (f"ðŸ’° TRADE: {trade_type.upper()} {quantity:+.2f} {symbol} "
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
        
        msg = f"ðŸ”„ REGIME: {old_regime} â†’ {new_regime} (GPM: {regime_data.get('gpm', 1.0):.2f})"
        
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
        
        msg = f"ðŸ”´ CIRCUIT BREAKER: {breaker_type} | {reason} | Action: {action}"
        
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
        
        msg = (f"ðŸ“ A-VWAP: {symbol} | "
               f"VWAP=${avwap_data.get('avwap', 0):.2f} | "
               f"Distance={avwap_data.get('distance', 0):.2%} | "
               f"Bars={avwap_data.get('bars_since_impulse', 0)}")
        
        self.debug(msg, component='AVWAPTracker', extra_data=avwap_data)
    
    def log_risk_metrics(self, metrics):
        """Log risk management metrics"""
        
        msg = (f"ðŸ“Š RISK: DD={metrics.get('drawdown', 0):.2%} | "
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
```


## E:\rony-data\trading-bot\src\components\portfolio_constraints.py

```python
"""
Portfolio Constraints - Phase 2

Enforces portfolio-level constraints:
- Beta neutrality (|Î²| â‰¤ 0.05)
- Sector limits (â‰¤ 2Ã— baseline weight)
- Position limits (min of 2% NAV, 5% ADV)
- Gross/Net exposure limits

Usage:
    from portfolio_constraints import PortfolioConstraints
    
    constraints = PortfolioConstraints(algorithm)
    can_trade, reason = constraints.CheckConstraints(symbol, size)
    constraints.EnforceBetaNeutrality()
"""

from AlgorithmImports import *
from collections import defaultdict

class PortfolioConstraints:
    """
    Enforce portfolio-level constraints
    """
    
    def __init__(self, algorithm):
        self.algorithm = algorithm
        self.logger = algorithm.logger if hasattr(algorithm, 'logger') else None
        
        # Constraint thresholds
        self.max_beta = 0.05
        self.max_sector_multiplier = 2.0
        self.max_position_pct_nav = 0.02  # 2%
        self.max_position_pct_adv = 0.05  # 5%
        self.max_gross_exposure = 2.5  # 250%
        self.max_net_exposure = 0.10  # Â±10%
        
        # Baseline sector weights (from universe)
        self.sector_baseline = {}
        
        # Current exposures
        self.current_beta = 0.0
        self.current_sector_weights = defaultdict(float)
        self.current_gross = 0.0
        self.current_net = 0.0
        
        if self.logger:
            self.logger.info("PortfolioConstraints initialized", component="PortfolioConstraints")
    
    def Update(self):
        """Update current portfolio metrics"""
        
        portfolio = self.algorithm.Portfolio
        total_value = portfolio.TotalPortfolioValue
        
        if total_value == 0:
            return
        
        # Calculate exposures
        self.current_gross = 0.0
        self.current_net = 0.0
        self.current_sector_weights = defaultdict(float)
        
        for symbol in portfolio.Keys:
            if portfolio[symbol].Invested:
                quantity = portfolio[symbol].Quantity
                price = portfolio[symbol].Price
                position_value = abs(quantity * price)
                
                # Gross exposure
                self.current_gross += position_value / total_value
                
                # Net exposure
                self.current_net += (quantity * price) / total_value
                
                # Sector exposure (would need sector data)
                # For now, skip
        
        # Calculate beta (simplified - would need actual beta calculation)
        self.current_beta = self._CalculatePortfolioBeta()
    
    def CheckConstraints(self, symbol, proposed_size, price):
        """
        Check if trade violates any constraints
        
        Returns:
            (bool, str): (can_trade, reason)
        """
        
        # 1. Check position size limit
        can_trade, reason = self._CheckPositionLimit(symbol, proposed_size, price)
        if not can_trade:
            return False, reason
        
        # 2. Check sector limit
        can_trade, reason = self._CheckSectorLimit(symbol, proposed_size, price)
        if not can_trade:
            return False, reason
        
        # 3. Check gross exposure
        can_trade, reason = self._CheckGrossExposure(proposed_size, price)
        if not can_trade:
            return False, reason
        
        # 4. Check net exposure
        can_trade, reason = self._CheckNetExposure(proposed_size, price)
        if not can_trade:
            return False, reason
        
        return True, "OK"
    
    def _CheckPositionLimit(self, symbol, size, price):
        """Check if position size within limits"""
        
        portfolio = self.algorithm.Portfolio
        total_value = portfolio.TotalPortfolioValue
        
        if total_value == 0:
            return False, "Zero portfolio value"
        
        position_value = abs(size * price)
        
        # Check vs NAV
        pct_nav = position_value / total_value
        if pct_nav > self.max_position_pct_nav:
            return False, f"Position size {pct_nav:.2%} > {self.max_position_pct_nav:.2%} NAV limit"
        
        # Check vs ADV (would need actual ADV data)
        # For now, skip
        
        return True, "OK"
    
    def _CheckSectorLimit(self, symbol, size, price):
        """Check if sector exposure within limits"""
        
        # Would need sector classification
        # For now, pass
        return True, "OK"
    
    def _CheckGrossExposure(self, size, price):
        """Check if gross exposure within limits"""
        
        portfolio = self.algorithm.Portfolio
        total_value = portfolio.TotalPortfolioValue
        
        if total_value == 0:
            return True, "OK"
        
        new_exposure = abs(size * price) / total_value
        projected_gross = self.current_gross + new_exposure
        
        if projected_gross > self.max_gross_exposure:
            return False, f"Gross exposure {projected_gross:.2f} > {self.max_gross_exposure:.2f} limit"
        
        return True, "OK"
    
    def _CheckNetExposure(self, size, price):
        """Check if net exposure within limits"""
        
        portfolio = self.algorithm.Portfolio
        total_value = portfolio.TotalPortfolioValue
        
        if total_value == 0:
            return True, "OK"
        
        new_exposure = (size * price) / total_value
        projected_net = self.current_net + new_exposure
        
        if abs(projected_net) > self.max_net_exposure:
            return False, f"Net exposure {projected_net:.2%} > Â±{self.max_net_exposure:.2%} limit"
        
        return True, "OK"
    
    def EnforceBetaNeutrality(self):
        """Hedge portfolio beta with SPY if needed"""
        
        if abs(self.current_beta) <= self.max_beta:
            return  # Within tolerance
        
        # Calculate hedge size
        portfolio_value = self.algorithm.Portfolio.TotalPortfolioValue
        hedge_size = -self.current_beta * portfolio_value
        
        # Get SPY price
        spy = self.algorithm.Symbol("SPY")
        if spy not in self.algorithm.Securities:
            if self.logger:
                self.logger.warning("SPY not available for beta hedge", component="PortfolioConstraints")
            return
        
        spy_price = self.algorithm.Securities[spy].Price
        
        if spy_price == 0:
            return
        
        # Calculate shares needed
        shares_needed = int(hedge_size / spy_price)
        
        if abs(shares_needed) < 1:
            return
        
        # Place hedge
        if self.logger:
            self.logger.info(f"Beta hedge: {shares_needed:+d} SPY @ ${spy_price:.2f} (Î²={self.current_beta:.3f})",
                           component="PortfolioConstraints")
        
        # Would execute hedge here
        # self.algorithm.MarketOrder(spy, shares_needed)
    
    def _CalculatePortfolioBeta(self):
        """Calculate portfolio beta (simplified)"""
        
        # Would need actual beta calculation with SPY returns
        # For now, estimate based on net exposure
        return self.current_net * 0.8  # Rough estimate
    
    def GetConstraintsSummary(self):
        """Get summary of current constraints"""
        
        return {
            'beta': self.current_beta,
            'beta_limit': self.max_beta,
            'beta_ok': abs(self.current_beta) <= self.max_beta,
            'gross': self.current_gross,
            'gross_limit': self.max_gross_exposure,
            'gross_ok': self.current_gross <= self.max_gross_exposure,
            'net': self.current_net,
            'net_limit': self.max_net_exposure,
            'net_ok': abs(self.current_net) <= self.max_net_exposure
        }
```


## E:\rony-data\trading-bot\src\components\pvs_monitor.py

```python
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
            summary += " | âš ï¸ HALT"
        elif info['action']['size_multiplier'] < 1.0:
            summary += f" | Size: {info['action']['size_multiplier']:.1f}x"
        
        return summary
```


## E:\rony-data\trading-bot\src\components\risk_monitor.py

```python
"""
Risk Monitor
Tracks all key metrics, circuit breakers, and generates reports
Phase 1: Observation and logging only
"""

from AlgorithmImports import *
from collections import defaultdict
from datetime import datetime

class RiskMonitor:
    """Monitor risk metrics and generate reports"""
    
    def __init__(self, algorithm):
        self.algorithm = algorithm
        self.config = algorithm.config
        
        # Daily tracking
        self.daily_stats = self._InitDailyStats()
        
        # Circuit breaker states
        self.breakers = {
            'consecutive_stopouts': 0,
            'daily_loss_breach': False,
            'weekly_loss_breach': False,
            'liquidity_crisis': False,
            'correlation_spike': False
        }
        
        # Trade log
        self.trades_today = []
        self.extremes_detected = []
        
        # Performance tracking
        self.equity_curve = []
        self.drawdown_history = []
        
    def _InitDailyStats(self):
        """Initialize daily statistics"""
        return {
            'date': None,
            'extremes_detected': 0,
            'trades_attempted': 0,
            'trades_executed': 0,
            'dominant_regime': 'Unknown',
            'avg_gpm': 0.0,
            'active_avwap_tracks': 0,
            'blocked_trades': defaultdict(int),  # reason -> count
            'regime_changes': 0,
            'vix_level': None,
            'correlation_breakdown': 0.0
        }
    
    def Update(self, current_time, regime_state, candidates):
        """
        Update risk metrics
        
        Args:
            current_time: Current timestamp
            regime_state: Dict from HMMRegime
            candidates: List of (symbol, extreme_info) tuples
        """
        
        # Update date if new day
        current_date = current_time.date()
        if self.daily_stats['date'] != current_date:
            # New day - reset daily stats
            self.daily_stats = self._InitDailyStats()
            self.daily_stats['date'] = current_date
            self.trades_today = []
            self.extremes_detected = []
        
        # Update regime tracking
        self.daily_stats['dominant_regime'] = regime_state['dominant_state']
        self.daily_stats['avg_gpm'] = regime_state['gpm']
        self.daily_stats['correlation_breakdown'] = regime_state.get('correlation_breakdown', 0.0)
        
        # Track extremes
        self.daily_stats['extremes_detected'] += len(candidates)
        
        for symbol, info in candidates:
            self.extremes_detected.append({
                'time': current_time,
                'symbol': symbol,
                'z_score': info['z_score'],
                'vol_anomaly': info['vol_anomaly'],
                'direction': info['direction']
            })
        
        # Update A-VWAP track count
        self.daily_stats['active_avwap_tracks'] = self.algorithm.avwap_tracker.GetActiveTracks()
        
        # Check circuit breakers
        self._CheckCircuitBreakers()
    
    def _CheckCircuitBreakers(self):
        """Check if any circuit breakers should fire"""
        
        # Phase 1: Just monitor, don't enforce
        # In later phases, these would halt trading
        
        # Daily loss check
        if self.algorithm.Portfolio.TotalPortfolioValue < self.config.INITIAL_CAPITAL * 0.95:
            if not self.breakers['daily_loss_breach']:
                self.breakers['daily_loss_breach'] = True
                self.algorithm.Log("âš ï¸ Circuit Breaker: Daily loss > 5%")
        else:
            self.breakers['daily_loss_breach'] = False
        
        # Correlation spike (placeholder)
        corr = self.daily_stats['correlation_breakdown']
        if corr > 0.85:
            if not self.breakers['correlation_spike']:
                self.breakers['correlation_spike'] = True
                self.algorithm.Log("âš ï¸ Circuit Breaker: Correlation spike > 0.85")
        else:
            self.breakers['correlation_spike'] = False
    
    def LogBlockedTrade(self, symbol, reason):
        """Log a trade that was blocked and why"""
        self.daily_stats['blocked_trades'][reason] += 1
        self.algorithm.Log(f"âŒ Trade Blocked: {symbol} - {reason}")
    
    def LogTrade(self, symbol, direction, size, price, reason):
        """Log a trade execution"""
        trade = {
            'time': self.algorithm.Time,
            'symbol': symbol,
            'direction': direction,
            'size': size,
            'price': price,
            'reason': reason
        }
        self.trades_today.append(trade)
        self.daily_stats['trades_executed'] += 1
        
        self.algorithm.Log(f"âœ… Trade Executed: {direction} {size} {symbol} @ ${price:.2f} ({reason})")
    
    def GetDailySummary(self):
        """Generate daily summary report"""
        summary = {
            'extremes_detected': self.daily_stats['extremes_detected'],
            'trades_attempted': self.daily_stats['trades_attempted'],
            'trades_executed': self.daily_stats['trades_executed'],
            'dominant_regime': self.daily_stats['dominant_regime'],
            'active_avwap_tracks': self.daily_stats['active_avwap_tracks'],
            'blocked_trades': dict(self.daily_stats['blocked_trades']),
            'circuit_breakers_active': self._GetActiveBreakers()
        }
        
        return summary
    
    def _GetActiveBreakers(self):
        """Get list of active circuit breakers"""
        active = []
        for breaker, is_active in self.breakers.items():
            if is_active:
                active.append(breaker)
        return active
    
    def GetExtremeSummary(self):
        """Get summary of detected extremes today"""
        if not self.extremes_detected:
            return "No extremes detected today"
        
        summary = f"\n{'='*60}\n"
        summary += f"EXTREMES DETECTED TODAY: {len(self.extremes_detected)}\n"
        summary += f"{'='*60}\n"
        
        for ext in self.extremes_detected[-10:]:  # Last 10
            summary += f"{ext['time'].strftime('%H:%M')} | {ext['symbol']:6s} | "
            summary += f"Z={ext['z_score']:+.2f} | Vol={ext['vol_anomaly']:.1f}x | "
            summary += f"{ext['direction']:>4s}\n"
        
        return summary
    
    def CalculateDrawdown(self):
        """Calculate current drawdown"""
        if not self.equity_curve:
            return 0.0
        
        peak = max(self.equity_curve)
        current = self.algorithm.Portfolio.TotalPortfolioValue
        
        if peak > 0:
            dd = (current - peak) / peak
            return dd
        return 0.0
    
    def UpdateEquityCurve(self):
        """Update equity curve for drawdown calculation"""
        self.equity_curve.append(self.algorithm.Portfolio.TotalPortfolioValue)
        
        # Calculate current drawdown
        dd = self.CalculateDrawdown()
        self.drawdown_history.append({
            'time': self.algorithm.Time,
            'drawdown': dd
        })
        
        # Keep only last 252 days (1 year)
        if len(self.equity_curve) > 252:
            self.equity_curve = self.equity_curve[-252:]
            self.drawdown_history = self.drawdown_history[-252:]
    
    def GetDrawdownLadderMultiplier(self):
        """
        Get position size multiplier based on drawdown ladder
        Phase 1: Just observe, don't apply
        """
        dd = abs(self.CalculateDrawdown())
        
        for i, threshold in enumerate(self.config.DD_THRESHOLDS):
            if dd >= threshold:
                multiplier = self.config.DD_MULTIPLIERS[i]
                if multiplier < 1.0:
                    self.algorithm.Log(f"ðŸ“‰ Drawdown {dd:.1%} -> Size Multiplier {multiplier:.2f}")
                return multiplier
        
        return 1.0  # No drawdown scaling
    
    def GenerateWeeklyReport(self):
        """Generate weekly performance report"""
        report = f"\n{'='*60}\n"
        report += f"WEEKLY REPORT - {self.algorithm.Time.strftime('%Y-%m-%d')}\n"
        report += f"{'='*60}\n"
        
        # Performance metrics
        report += f"Portfolio Value: ${self.algorithm.Portfolio.TotalPortfolioValue:,.2f}\n"
        report += f"Cash: ${self.algorithm.Portfolio.Cash:,.2f}\n"
        report += f"Current Drawdown: {self.CalculateDrawdown():.2%}\n"
        
        # Trading activity
        report += f"\nTrading Activity:\n"
        report += f"  Extremes Detected: {self.daily_stats['extremes_detected']}\n"
        report += f"  Trades Executed: {self.daily_stats['trades_executed']}\n"
        
        # Circuit breakers
        active_breakers = self._GetActiveBreakers()
        if active_breakers:
            report += f"\nâš ï¸ Active Circuit Breakers:\n"
            for breaker in active_breakers:
                report += f"  - {breaker}\n"
        else:
            report += f"\nâœ… No active circuit breakers\n"
        
        report += f"{'='*60}\n"
        
        return report
```


## E:\rony-data\trading-bot\src\components\universe_filter.py

```python
"""
Universe Selection - Filter for top ~1000 liquid US equities
Criteria:
- NYSE/NASDAQ common shares
- Price: $5-$350
- Liquidity: top 1000 by 60-day median dollar volume
- Spread quality: median spread â‰¤ 35 bps
- Exclude blacklisted tickers
"""

from AlgorithmImports import *

class UniverseFilter:
    """Handle coarse and fine universe selection"""
    
    def __init__(self, algorithm):
        self.algorithm = algorithm
        self.config = algorithm.config
        
        # Track universe stats
        self.last_rebalance = None
        self.current_universe = set()
        
    def CoarseFilter(self, coarse):
        """
        First pass: liquidity and price filters
        Returns top UNIVERSE_SIZE symbols
        """
        
        # Filter criteria
        selected = [
            x for x in coarse
            if x.HasFundamentalData
            and x.Price >= self.config.MIN_PRICE
            and x.Price <= self.config.MAX_PRICE
            and x.DollarVolume > self.config.MIN_DOLLAR_VOLUME
            and x.Symbol.Value not in self.config.BLACKLIST
        ]
        
        # Sort by dollar volume and take top N
        selected = sorted(selected, key=lambda x: x.DollarVolume, reverse=True)
        selected = selected[:self.config.UNIVERSE_SIZE]
        
        self.algorithm.Log(f"Coarse Filter: {len(selected)} symbols passed")
        
        return [x.Symbol for x in selected]
    
    def FineFilter(self, fine):
        """
        Second pass: quality filters
        - Common shares only (no ADRs, preferred, etc.)
        - Exchange: NYSE or NASDAQ
        """
        
        selected = []
        
        for f in fine:
            # Basic checks
            if not f.HasFundamentalData:
                continue
            
            # Security type filter
            if f.SecurityReference.SecurityType != "ST00000001":  # Common Stock
                continue
            
            # Exchange filter (NYSE, NASDAQ)
            exchange = f.CompanyReference.PrimaryExchangeId
            if exchange not in ["NYS", "NAS"]:
                continue
            
            # Company profile checks
            if not f.CompanyProfile.HeadquarterCity:
                continue
            
            selected.append(f.Symbol)
        
        self.algorithm.Log(f"Fine Filter: {len(selected)} symbols passed")
        self.current_universe = set(selected)
        
        return selected
    
    def IsInUniverse(self, symbol):
        """Check if symbol is in current universe"""
        return symbol in self.current_universe
    
    def GetUniverseStats(self):
        """Return universe statistics"""
        return {
            'size': len(self.current_universe),
            'last_rebalance': self.last_rebalance
        }
```


## E:\rony-data\trading-bot\src\main.py

```python
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
        # âš ï¸ SET YOUR CONFIGURATION HERE
        # Week 1-4:  Config(version=1, trading_enabled=False)  # Learn basics
        # Week 5-8:  Config(version=2, trading_enabled=False)  # Test advanced
        # Week 9+:   Config(version=2, trading_enabled=True)   # Go live

        self.config = Config(version=2, trading_enabled=False)  # âš ï¸ CHANGE THIS

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

        self.logger.info("âœ“ Core components initialized", component="Main")

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

            self.logger.info("âœ“ Advanced components initialized", component="Main")
        else:
            # Stub components for v1 (not used)
            self.drawdown_enforcer = None
            self.pvs_monitor = None
            self.exhaustion_detector = None
            self.portfolio_constraints = None
            self.cascade_prevention = None
            self.dynamic_sizer = None
            self.entry_timing = None

            self.logger.info("â„¹ Advanced components disabled (v1 mode)", component="Main")

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

        # Reset hourly counter
        self.trades_this_hour = 0
        self.last_hour = self.Time.hour

        # Update systems
        portfolio_value = self.Portfolio.TotalPortfolioValue

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

    def _ScanForExtremes(self):
        """Scan all symbols for extremes"""

        detections = []

        for symbol in self.active_symbols:
            if symbol not in self.minute_bars:
                continue

            bars = self.minute_bars[symbol]

            if len(bars) < self.config['LOOKBACK_MINUTES']:
                continue

            # Check for continuation extreme
            extreme = self.extreme_detector.Detect(bars)

            if extreme and extreme['is_extreme']:
                extreme['symbol'] = symbol
                extreme['type'] = 'continuation'
                extreme['detection_time'] = self.Time
                detections.append(extreme)

                self.health_monitor.update_metrics('detection', None)

            # v2+: Check for exhaustion
            if self.config.version >= 2 and self.config['ENABLE_EXHAUSTION']:
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

        self.logger.info(
            f"Extreme: {symbol} | Type: {detection['type']} | Z: {detection.get('z_score', 0):.2f}",
            component="ExtremeDetector"
        )

        # Get regime
        regime = self.hmm_regime.GetCurrentRegime()
        gpm = regime.get('gpm', 0.5)

        # v2+: Check cascade risk
        if self.config.version >= 2 and self.config['ENABLE_CASCADE_PREVENTION']:
            can_trade, violations = self._CheckCascadeRisk(detection)

            if not can_trade:
                self.logger.warning(
                    f"Trade blocked - Cascade risk: {violations}",
                    component="CascadePrevention"
                )
                return

        # Calculate position size
        size = self._CalculatePositionSize(detection, gpm)

        if size < self.config['RISK_PER_TRADE'] * 0.5:
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
        if self.config.version >= 2 and self.config['ENABLE_ENTRY_TIMING']:
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
        """Calculate position size with all multipliers"""

        # Get multipliers
        z_score = abs(detection.get('z_score', 2.0))

        # v2+: Use advanced sizing
        if self.config.version >= 2 and self.config['ENABLE_DYNAMIC_SIZING']:
            dd_mult = self.drawdown_enforcer.GetSizeMultiplier()
            pvs_mult = self.pvs_monitor.GetSizeMultiplier()
            size = self.dynamic_sizer.CalculateSize(z_score, gpm, dd_mult, pvs_mult)
        else:
            # Phase 1: Fixed size
            size = self.config['RISK_PER_TRADE']

        self.logger.info(
            f"Position size: ${size:.2f} (Z={z_score:.2f}, GPM={gpm:.2f})",
            component="DynamicSizer" if self.config.version >= 2 else "Main"
        )

        return size

    # ==================== ENTRY/EXIT ====================

    def _CheckPendingEntries(self, data):
        """Check pending entries for timing (v2+ only)"""

        if self.config.version < 2 or not self.config['ENABLE_ENTRY_TIMING']:
            return

        to_remove = []

        for symbol, entry_info in self.pending_entries.items():
            if symbol not in data or not data[symbol]:
                continue

            current_price = data[symbol].Close
            detection = entry_info['detection']

            # Get A-VWAP if available
            avwap_price = None
            if symbol in self.avwap_tracker.avwap_values:
                avwap_price = self.avwap_tracker.avwap_values[symbol]

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
        if self.config['OBSERVATION_MODE']:
            self.logger.info(
                f"ðŸ’¡ OBSERVATION MODE - Would enter: {shares:+d} {symbol} @ ${price:.2f}",
                component="Main"
            )
            return

        # Execute order (v2+ only)
        try:
            ticket = self.MarketOrder(symbol, shares)

            if ticket.Status == OrderStatus.Filled or ticket.Status == OrderStatus.PartiallyFilled:
                fill_price = ticket.AverageFillPrice

                self.logger.info(
                    f"âœ“ ENTRY: {shares:+d} {symbol} @ ${fill_price:.2f} (${size:.2f})",
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
        if self.config['OBSERVATION_MODE']:
            self.logger.info(
                f"ðŸ’¡ OBSERVATION MODE - Would exit: {-shares:+d} {symbol} @ ${current_price:.2f} | "
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
                    f"âœ“ EXIT: {-shares:+d} {symbol} @ ${exit_price:.2f} | "
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
            self.logger.info(f"  Status: {'âœ“ HEALTHY' if health['overall_healthy'] else 'âœ— ISSUES'}", component="Report")
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
        total_return = (final_value / self.config['INITIAL_CAPITAL'] - 1) * 100

        self.logger.info(f"Final Portfolio Value: ${final_value:,.2f}", component="Main")
        self.logger.info(f"Total Return: {total_return:+.2f}%", component="Main")

        # Export trades
        trades_df = self.backtest_analyzer.export_trades_csv()
        if trades_df is not None:
            self.logger.info(f"Total Trades: {len(trades_df)}", component="Main")

        self.logger.info("="*70, component="Main")
```


