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

Validation:
    All configuration parameters are validated on initialization.
    Invalid values raise ValueError with descriptive error messages.

    Key validated ranges:
    - MIN_PRICE: >= $1.00
    - MAX_PRICE: <= $100,000
    - MIN_DOLLAR_VOLUME: >= $1M daily
    - MAX_SPREAD_BPS: 1-1000 basis points
    - Z_THRESHOLD: 0.5-5.0
    - VOLUME_ANOMALY: 1.0-10.0x
    - LOOKBACK_MINUTES: 10-1440
    - PVS levels: 1-10
    - Position sizes: MIN <= BASE <= MAX
    - Correlation thresholds: SOFT < SECTOR < MARKET
    - Circuit breakers: Reasonable % ranges
    - Blacklist: Auto-normalized to uppercase

    See _validate() method for complete validation logic.
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

        # Blacklist problematic symbols (will be normalized to uppercase)
        self.BLACKLIST = ['BRK.A', 'BRK.B']
        # Normalize blacklist to uppercase once upfront
        self.BLACKLIST = [s.upper() for s in self.BLACKLIST]

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

        # Validate all configuration parameters
        self._validate()

    def _validate(self):
        """
        Validate all configuration values

        Raises:
            ValueError: If any configuration parameter is out of valid range
        """
        # Basic settings validation
        if self.INITIAL_CAPITAL <= 0:
            raise ValueError(f"INITIAL_CAPITAL must be > 0, got {self.INITIAL_CAPITAL}")
        if not (0 < self.RISK_PER_TRADE <= 1000):
            raise ValueError(f"RISK_PER_TRADE must be 0-1000, got {self.RISK_PER_TRADE}")
        if not (0 < self.MAX_POSITIONS <= 100):
            raise ValueError(f"MAX_POSITIONS must be 1-100, got {self.MAX_POSITIONS}")
        if not (0 < self.MAX_TRADES_PER_DAY <= 1000):
            raise ValueError(f"MAX_TRADES_PER_DAY must be 1-1000, got {self.MAX_TRADES_PER_DAY}")

        # Universe validation
        if not (0 < self.UNIVERSE_SIZE <= 10000):
            raise ValueError(f"UNIVERSE_SIZE must be 1-10000, got {self.UNIVERSE_SIZE}")
        if not (0 < self.MIN_PRICE < self.MAX_PRICE):
            raise ValueError(f"MIN_PRICE ({self.MIN_PRICE}) must be < MAX_PRICE ({self.MAX_PRICE})")
        if self.MIN_PRICE < 1.0:
            raise ValueError(f"MIN_PRICE should be >= $1.00, got ${self.MIN_PRICE}")
        if self.MAX_PRICE > 100000:
            raise ValueError(f"MAX_PRICE too high (>${self.MAX_PRICE}), likely a mistake")
        if self.MIN_DOLLAR_VOLUME < 1_000_000:
            raise ValueError(f"MIN_DOLLAR_VOLUME should be >= $1M, got ${self.MIN_DOLLAR_VOLUME:,.0f}")
        if not (1 <= self.MAX_SPREAD_BPS <= 1000):
            raise ValueError(f"MAX_SPREAD_BPS must be 1-1000, got {self.MAX_SPREAD_BPS}")

        # Spread guards validation
        if not (1 <= self.HARD_SKIP_SPREAD_BPS <= 1000):
            raise ValueError(f"HARD_SKIP_SPREAD_BPS must be 1-1000, got {self.HARD_SKIP_SPREAD_BPS}")
        if not (1 <= self.NORMAL_SPREAD_BPS <= self.HARD_SKIP_SPREAD_BPS):
            raise ValueError(f"NORMAL_SPREAD_BPS must be <= HARD_SKIP_SPREAD_BPS")
        if not (1 <= self.HIGH_VOL_SPREAD_BPS <= self.NORMAL_SPREAD_BPS):
            raise ValueError(f"HIGH_VOL_SPREAD_BPS must be <= NORMAL_SPREAD_BPS")

        # Extreme detection validation
        if not (0.5 <= self.Z_THRESHOLD <= 5.0):
            raise ValueError(f"Z_THRESHOLD must be 0.5-5.0, got {self.Z_THRESHOLD}")
        if not (1.0 <= self.VOLUME_ANOMALY_NORMAL <= 10.0):
            raise ValueError(f"VOLUME_ANOMALY_NORMAL must be 1.0-10.0, got {self.VOLUME_ANOMALY_NORMAL}")
        if not (1.0 <= self.VOLUME_ANOMALY_AUCTION <= 10.0):
            raise ValueError(f"VOLUME_ANOMALY_AUCTION must be 1.0-10.0, got {self.VOLUME_ANOMALY_AUCTION}")
        if not (10 <= self.LOOKBACK_MINUTES <= 1440):
            raise ValueError(f"LOOKBACK_MINUTES must be 10-1440, got {self.LOOKBACK_MINUTES}")
        if not (10 <= self.MIN_BARS_FOR_DETECTION <= 1440):
            raise ValueError(f"MIN_BARS_FOR_DETECTION must be 10-1440, got {self.MIN_BARS_FOR_DETECTION}")

        # HMM validation
        if self.HMM_STATES not in [2, 3, 4]:
            raise ValueError(f"HMM_STATES must be 2, 3, or 4, got {self.HMM_STATES}")
        if not (100 <= self.HMM_FIT_WINDOW_DAYS <= 2000):
            raise ValueError(f"HMM_FIT_WINDOW_DAYS must be 100-2000, got {self.HMM_FIT_WINDOW_DAYS}")
        if not (1 <= self.HMM_REFIT_DAYS <= 100):
            raise ValueError(f"HMM_REFIT_DAYS must be 1-100, got {self.HMM_REFIT_DAYS}")
        if not (60 <= self.MIN_BARS_FOR_HMM <= 1440):
            raise ValueError(f"MIN_BARS_FOR_HMM must be 60-1440, got {self.MIN_BARS_FOR_HMM}")

        # A-VWAP validation
        if not (0.1 <= self.AVWAP_ATR_MULTIPLIER <= 5.0):
            raise ValueError(f"AVWAP_ATR_MULTIPLIER must be 0.1-5.0, got {self.AVWAP_ATR_MULTIPLIER}")
        if not (1 <= self.AVWAP_MAX_BARS <= 24):
            raise ValueError(f"AVWAP_MAX_BARS must be 1-24 hours, got {self.AVWAP_MAX_BARS}")

        # Timing filters validation
        if not (15 <= self.AUCTION_MINUTES <= 60):
            raise ValueError(f"AUCTION_MINUTES must be 15-60, got {self.AUCTION_MINUTES}")
        if not (13.0 <= self.AVOID_FADE_AFTER <= 16.0):
            raise ValueError(f"AVOID_FADE_AFTER must be 13.0-16.0, got {self.AVOID_FADE_AFTER}")

        # Drawdown ladder validation
        if len(self.DD_THRESHOLDS) != len(self.DD_MULTIPLIERS):
            raise ValueError("DD_THRESHOLDS and DD_MULTIPLIERS must have same length")
        if not all(0 <= t <= 1 for t in self.DD_THRESHOLDS):
            raise ValueError(f"DD_THRESHOLDS must be 0-1 (percentages), got {self.DD_THRESHOLDS}")
        if not all(0 <= m <= 1 for m in self.DD_MULTIPLIERS):
            raise ValueError(f"DD_MULTIPLIERS must be 0-1, got {self.DD_MULTIPLIERS}")
        if self.DD_THRESHOLDS != sorted(self.DD_THRESHOLDS):
            raise ValueError("DD_THRESHOLDS must be in ascending order")

        # PVS validation (v2+)
        if self.version >= 2 and self.ENABLE_PVS:
            if not (1 <= self.PVS_WARNING_LEVEL <= 10):
                raise ValueError(f"PVS_WARNING_LEVEL must be 1-10, got {self.PVS_WARNING_LEVEL}")
            if not (1 <= self.PVS_HALT_LEVEL <= 10):
                raise ValueError(f"PVS_HALT_LEVEL must be 1-10, got {self.PVS_HALT_LEVEL}")
            if self.PVS_WARNING_LEVEL >= self.PVS_HALT_LEVEL:
                raise ValueError("PVS_WARNING_LEVEL must be < PVS_HALT_LEVEL")
            if not (1.0 <= self.PVS_SMALL_CAPITAL_MULT <= 3.0):
                raise ValueError(f"PVS_SMALL_CAPITAL_MULT must be 1.0-3.0, got {self.PVS_SMALL_CAPITAL_MULT}")
            if self.SMALL_CAPITAL_THRESHOLD <= 0:
                raise ValueError(f"SMALL_CAPITAL_THRESHOLD must be > 0, got {self.SMALL_CAPITAL_THRESHOLD}")

        # Cascade prevention validation (v2+)
        if self.version >= 2 and self.ENABLE_CASCADE_PREVENTION:
            cp = self.CASCADE_PREVENTION
            if not (0.5 <= cp['MIN_EDGE_THRESHOLD'] <= 5.0):
                raise ValueError(f"MIN_EDGE_THRESHOLD must be 0.5-5.0, got {cp['MIN_EDGE_THRESHOLD']}")
            if not (1 <= cp['CASCADE_THRESHOLD'] <= 10):
                raise ValueError(f"CASCADE_THRESHOLD must be 1-10, got {cp['CASCADE_THRESHOLD']}")
            if not (1 <= cp['MAX_CONSECUTIVE_LOSSES'] <= 10):
                raise ValueError(f"MAX_CONSECUTIVE_LOSSES must be 1-10, got {cp['MAX_CONSECUTIVE_LOSSES']}")
            if not (1 <= cp['PVS_THRESHOLD'] <= 10):
                raise ValueError(f"PVS_THRESHOLD must be 1-10, got {cp['PVS_THRESHOLD']}")
            if not (1 <= cp['MAX_TRADES_PER_HOUR'] <= 100):
                raise ValueError(f"MAX_TRADES_PER_HOUR must be 1-100, got {cp['MAX_TRADES_PER_HOUR']}")
            if not (0.0 <= cp['MIN_REGIME_CONFIDENCE'] <= 1.0):
                raise ValueError(f"MIN_REGIME_CONFIDENCE must be 0.0-1.0, got {cp['MIN_REGIME_CONFIDENCE']}")

        # Exhaustion detection validation (v2+)
        if self.version >= 2 and self.ENABLE_EXHAUSTION:
            if not (5 <= self.BOLL_PERIOD <= 100):
                raise ValueError(f"BOLL_PERIOD must be 5-100, got {self.BOLL_PERIOD}")
            if not (0.5 <= self.BOLL_STD <= 5.0):
                raise ValueError(f"BOLL_STD must be 0.5-5.0, got {self.BOLL_STD}")
            if not (1 <= self.MIN_COMPRESSION_HOURS <= 24):
                raise ValueError(f"MIN_COMPRESSION_HOURS must be 1-24, got {self.MIN_COMPRESSION_HOURS}")

        # Position sizing validation (v2+)
        if self.version >= 2 and self.ENABLE_DYNAMIC_SIZING:
            if not (0.1 <= self.MIN_POSITION_SIZE <= self.MAX_POSITION_SIZE):
                raise ValueError(f"MIN_POSITION_SIZE ({self.MIN_POSITION_SIZE}) must be <= MAX_POSITION_SIZE ({self.MAX_POSITION_SIZE})")
            if self.MAX_POSITION_SIZE > 10000:
                raise ValueError(f"MAX_POSITION_SIZE seems too high: ${self.MAX_POSITION_SIZE}")
            if not (self.MIN_POSITION_SIZE <= self.BASE_POSITION_SIZE <= self.MAX_POSITION_SIZE):
                raise ValueError(f"BASE_POSITION_SIZE ({self.BASE_POSITION_SIZE}) must be between MIN ({self.MIN_POSITION_SIZE}) and MAX ({self.MAX_POSITION_SIZE})")

        # Entry timing validation (v2+)
        if self.version >= 2 and self.ENABLE_ENTRY_TIMING:
            if not (0 <= self.ENTRY_WAIT_MIN <= self.ENTRY_WAIT_MAX):
                raise ValueError(f"ENTRY_WAIT_MIN ({self.ENTRY_WAIT_MIN}) must be <= ENTRY_WAIT_MAX ({self.ENTRY_WAIT_MAX})")
            if self.ENTRY_WAIT_MAX > 120:
                raise ValueError(f"ENTRY_WAIT_MAX too high: {self.ENTRY_WAIT_MAX} minutes")
            if not (0.0 <= self.MAX_RETRACEMENT <= 1.0):
                raise ValueError(f"MAX_RETRACEMENT must be 0.0-1.0, got {self.MAX_RETRACEMENT}")

        # Portfolio constraints validation (v2+)
        if self.version >= 2 and self.ENFORCE_SECTOR_NEUTRALITY:
            if not (0.0 <= self.MAX_BETA <= 1.0):
                raise ValueError(f"MAX_BETA must be 0.0-1.0, got {self.MAX_BETA}")
            if not (1.0 <= self.MAX_SECTOR_MULTIPLIER <= 10.0):
                raise ValueError(f"MAX_SECTOR_MULTIPLIER must be 1.0-10.0, got {self.MAX_SECTOR_MULTIPLIER}")
            if not (0.0 < self.MAX_POSITION_PCT_NAV <= 1.0):
                raise ValueError(f"MAX_POSITION_PCT_NAV must be 0.0-1.0, got {self.MAX_POSITION_PCT_NAV}")
            if not (0.0 < self.MAX_POSITION_PCT_ADV <= 1.0):
                raise ValueError(f"MAX_POSITION_PCT_ADV must be 0.0-1.0, got {self.MAX_POSITION_PCT_ADV}")
            if not (0.1 <= self.MAX_GROSS_EXPOSURE <= 10.0):
                raise ValueError(f"MAX_GROSS_EXPOSURE must be 0.1-10.0, got {self.MAX_GROSS_EXPOSURE}")
            if not (0.0 <= self.MAX_NET_EXPOSURE <= 1.0):
                raise ValueError(f"MAX_NET_EXPOSURE must be 0.0-1.0, got {self.MAX_NET_EXPOSURE}")

        # Correlation thresholds validation
        if not (0.0 <= self.CORR_SOFT_DEEMPHASIS <= 1.0):
            raise ValueError(f"CORR_SOFT_DEEMPHASIS must be 0.0-1.0, got {self.CORR_SOFT_DEEMPHASIS}")
        if not (0.0 <= self.CORR_SECTOR_NEUTRAL <= 1.0):
            raise ValueError(f"CORR_SECTOR_NEUTRAL must be 0.0-1.0, got {self.CORR_SECTOR_NEUTRAL}")
        if not (0.0 <= self.CORR_MARKET_NEUTRAL <= 1.0):
            raise ValueError(f"CORR_MARKET_NEUTRAL must be 0.0-1.0, got {self.CORR_MARKET_NEUTRAL}")
        if not (self.CORR_SOFT_DEEMPHASIS <= self.CORR_SECTOR_NEUTRAL <= self.CORR_MARKET_NEUTRAL):
            raise ValueError("Correlation thresholds must be in ascending order: SOFT < SECTOR < MARKET")

        # Circuit breaker validation
        if not (1 <= self.CB_CONSECUTIVE_STOPS <= 10):
            raise ValueError(f"CB_CONSECUTIVE_STOPS must be 1-10, got {self.CB_CONSECUTIVE_STOPS}")
        if not (0.01 <= self.CB_DAILY_LOSS <= 0.50):
            raise ValueError(f"CB_DAILY_LOSS must be 0.01-0.50, got {self.CB_DAILY_LOSS}")
        if not (0.01 <= self.CB_WEEKLY_LOSS <= 0.75):
            raise ValueError(f"CB_WEEKLY_LOSS must be 0.01-0.75, got {self.CB_WEEKLY_LOSS}")
        if not (1.0 <= self.CB_LIQUIDITY_SPREAD_MULT <= 10.0):
            raise ValueError(f"CB_LIQUIDITY_SPREAD_MULT must be 1.0-10.0, got {self.CB_LIQUIDITY_SPREAD_MULT}")
        if not (0.01 <= self.CB_LIQUIDITY_VOLUME_MULT <= 1.0):
            raise ValueError(f"CB_LIQUIDITY_VOLUME_MULT must be 0.01-1.0, got {self.CB_LIQUIDITY_VOLUME_MULT}")

        # Feature engineering validation
        if not (5 <= self.ATR_PERIOD <= 100):
            raise ValueError(f"ATR_PERIOD must be 5-100, got {self.ATR_PERIOD}")
        if not (5 <= self.BOLLINGER_PERIOD <= 100):
            raise ValueError(f"BOLLINGER_PERIOD must be 5-100, got {self.BOLLINGER_PERIOD}")
        if not (0.5 <= self.BOLLINGER_STD <= 5.0):
            raise ValueError(f"BOLLINGER_STD must be 0.5-5.0, got {self.BOLLINGER_STD}")

        # Blacklist validation
        if not isinstance(self.BLACKLIST, list):
            raise ValueError(f"BLACKLIST must be a list, got {type(self.BLACKLIST)}")
        if not all(isinstance(s, str) for s in self.BLACKLIST):
            raise ValueError("All BLACKLIST items must be strings")

    def GetTimeOfDayMultiplier(self, hour, minute):
