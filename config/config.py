"""
Configuration parameters for Phase 1 implementation
All parameters from strategy doc with conservative Phase 1 defaults
"""

class Config:
    """Central configuration for the trading strategy"""
    
    def __init__(self):
        # Universe Selection
        self.UNIVERSE_SIZE = 1000
        self.MIN_PRICE = 5.0
        self.MAX_PRICE = 350.0
        self.MIN_DOLLAR_VOLUME = 20_000_000  # $20M daily
        self.MAX_SPREAD_BPS = 35  # 35 basis points
        
        # Extreme Detection
        self.Z_THRESHOLD = 2.0  # |Z₆₀| ≥ 2
        self.VOLUME_ANOMALY_NORMAL = 1.5  # 1.5x median
        self.VOLUME_ANOMALY_AUCTION = 2.0  # 2x for first/last 30min
        self.LOOKBACK_MINUTES = 60
        
        # Risk Management - Phase 1
        self.INITIAL_CAPITAL = 1000
        self.RISK_PER_TRADE = 5  # $5 per trade
        self.MAX_POSITIONS = 1  # One at a time
        self.MAX_TRADES_PER_DAY = 2  # Conservative
        
        # Spread Guards
        self.HARD_SKIP_SPREAD_BPS = 40
        self.NORMAL_SPREAD_BPS = 30
        self.HIGH_VOL_SPREAD_BPS = 20
        
        # HMM Regime
        self.HMM_STATES = 3  # Low-Vol, High-Vol, Trending
        self.HMM_FIT_WINDOW_DAYS = 500  # ~24 months trading days
        self.HMM_REFIT_DAYS = 20  # Monthly refit
        
        # A-VWAP
        self.AVWAP_ATR_MULTIPLIER = 0.5  # Stop distance
        self.AVWAP_MAX_BARS = 5  # Time stop
        
        # Timing Filters
        self.AUCTION_MINUTES = 30  # First/last 30 min
        self.AVOID_FADE_AFTER = 15.5  # 3:30 PM
        
        # Drawdown Ladder (Phase 1 - observe only)
        self.DD_THRESHOLDS = [0.10, 0.20, 0.30, 0.40]
        self.DD_MULTIPLIERS = [0.75, 0.50, 0.25, 0.00]
        
        # Data Quality
        self.MIN_BARS_FOR_DETECTION = 60  # Need 60 minutes
        self.MIN_BARS_FOR_HMM = 240  # Need 4 hours
        
        # Blacklist symbols (Phase 1)
        self.BLACKLIST = [
            # Add known problematic tickers
            # Examples: 'GME', 'AMC', etc. if desired
        ]
        
        # Feature Engineering
        self.ATR_PERIOD = 20
        self.BOLLINGER_PERIOD = 20
        self.BOLLINGER_STD = 2.0
        
        # Logging
        self.VERBOSE_LOGGING = True
        
    def GetTimeOfDayMultiplier(self, hour, minute):
        """Get intraday risk scaling multiplier"""
        time_decimal = hour + minute / 60.0
        
        if 9.5 <= time_decimal < 10.0:
            return 0.7  # First 30 min
        elif 10.0 <= time_decimal < 11.5:
            return 1.0
        elif 11.5 <= time_decimal < 13.0:
            return 0.8
        elif 13.0 <= time_decimal < 15.5:
            return 1.0
        elif 15.5 <= time_decimal <= 16.0:
            return 0.6  # Last 30 min
        else:
            return 0.5  # Outside normal hours
    
    def IsAuctionPeriod(self, time):
        """Check if in auction period (first/last 30 min)"""
        hour = time.hour
        minute = time.minute
        
        # First 30 minutes (9:30-10:00)
        if hour == 9 and minute >= 30:
            return True
        if hour == 10 and minute == 0:
            return True
        
        # Last 30 minutes (15:30-16:00)
        if hour == 15 and minute >= 30:
            return True
        if hour == 16 and minute == 0:
            return True
        
        return False
