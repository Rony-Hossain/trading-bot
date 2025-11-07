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
        """
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
        self.Z_THRESHOLD = 2.0  # |Z₆₀| ≥ 2.0 for detection
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
        self.PVS_WARNING_LEVEL = 7  # Reduce size at PVS ≥ 7
        self.PVS_HALT_LEVEL = 9     # Halt trading at PVS ≥ 9
        self.PVS_SMALL_CAPITAL_MULT = 1.5  # Extra sensitivity for small accounts
        self.SMALL_CAPITAL_THRESHOLD = 5000  # What counts as "small"

        # ==================== CASCADE PREVENTION ====================
        self.ENABLE_CASCADE_PREVENTION = (version >= 2)
        self.CASCADE_PREVENTION = {
            'MIN_EDGE_THRESHOLD': 2.0,      # Minimum |Z-score| for strong signal
            'CASCADE_THRESHOLD': 2,         # Block if ≥2 violations
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
        self.CORR_SOFT_DEEMPHASIS = 0.50  # Soft deemphasis if |ρ| > 0.5
        self.CORR_SECTOR_NEUTRAL = 0.70   # Sector neutral pairing if |ρ| > 0.7
        self.CORR_MARKET_NEUTRAL = 0.85   # Market neutral if |ρ| > 0.85

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

    def GetTimeOfDayMultiplier(self, hour, minute):
        """
        Get intraday risk scaling multiplier based on time of day

        Args:
            hour: Hour (0-23)
            minute: Minute (0-59)

        Returns:
            float: Multiplier (0.5 - 1.0)
        """
        time_decimal = hour + minute / 60.0

        if 9.5 <= time_decimal < 10.0:
            return 0.7  # First 30 min - reduced
        elif 10.0 <= time_decimal < 11.5:
            return 1.0  # Morning - full size
        elif 11.5 <= time_decimal < 13.0:
            return 0.8  # Lunch - reduced
        elif 13.0 <= time_decimal < 15.5:
            return 1.0  # Afternoon - full size
        elif 15.5 <= time_decimal <= 16.0:
            return 0.6  # Last 30 min - reduced
        else:
            return 0.5  # Outside normal hours

    def IsAuctionPeriod(self, time):
        """
        Check if current time is in auction period (first/last 30 min)

        Args:
            time: datetime object

        Returns:
            bool: True if in auction period
        """
        hour = time.hour
        minute = time.minute

        # First 30 minutes (9:30-10:00 AM)
        if hour == 9 and minute >= 30:
            return True
        if hour == 10 and minute == 0:
            return True

        # Last 30 minutes (3:30-4:00 PM)
        if hour == 15 and minute >= 30:
            return True
        if hour == 16 and minute == 0:
            return True

        return False

    def GetDescription(self):
        """Get human-readable configuration description"""
        version_desc = f"v{self.version} ({'Basic' if self.version == 1 else 'Advanced'})"
        mode_desc = "OBSERVATION" if self.OBSERVATION_MODE else "LIVE TRADING"
        return f"{version_desc} - {mode_desc}"

    def __repr__(self):
        """String representation"""
        return f"Config(version={self.version}, trading_enabled={self.trading_enabled})"

    def __getitem__(self, key):
        """Support dictionary-style access: config['KEY']"""
        return getattr(self, key)

    def __setitem__(self, key, value):
        """Support dictionary-style assignment: config['KEY'] = value"""
        setattr(self, key, value)

    def __contains__(self, key):
        """Support 'in' operator: 'KEY' in config"""
        return hasattr(self, key)

    def get(self, key, default=None):
        """Support .get() method like a dictionary"""
        return getattr(self, key, default)


# Convenience functions for quick config creation
def create_config(version=2, trading_enabled=False):
    """
    Create configuration object

    Args:
        version: 1 (basic) or 2 (advanced features)
        trading_enabled: False (observation) or True (live trading)

    Returns:
        Config: Configuration object
    """
    return Config(version=version, trading_enabled=trading_enabled)


# Pre-configured common scenarios
def config_v1_observe():
    """Version 1 (basic features), observation mode"""
    return Config(version=1, trading_enabled=False)


def config_v2_observe():
    """Version 2 (all features), observation mode"""
    return Config(version=2, trading_enabled=False)


def config_v2_live():
    """Version 2 (all features), live trading"""
    return Config(version=2, trading_enabled=True)
