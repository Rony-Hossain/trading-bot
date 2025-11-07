"""
Configuration for Phase 2 - Trading Enabled

All Phase 2 parameters with enhanced risk management
"""

class ConfigPhase2:
    """Phase 2 configuration with all new systems"""
    
    def __init__(self):
        # ==================== PHASE 2 FLAGS ====================
        OBSERVATION_MODE = False  # ⚠️ ENABLE TRADING!
        ENABLE_EXHAUSTION = True
        ENFORCE_DRAWDOWN_LADDER = True
        ENFORCE_SECTOR_NEUTRALITY = True
        ENABLE_PVS = True
        ENABLE_CASCADE_PREVENTION = True
        ENABLE_DYNAMIC_SIZING = True
        ENABLE_ENTRY_TIMING = True
        
        # ==================== BASIC SETTINGS ====================
        INITIAL_CAPITAL = 1000
        RISK_PER_TRADE = 5  # Base size
        MAX_POSITIONS = 1   # Phase 2: Still 1
        MAX_TRADES_PER_DAY = 2
        
        # ==================== UNIVERSE ====================
        UNIVERSE_SIZE = 1000
        MIN_PRICE = 5.0
        MAX_PRICE = 350.0
        MIN_DOLLAR_VOLUME = 20_000_000
        MAX_SPREAD_BPS = 35
        
        # ==================== DETECTION ====================
        Z_THRESHOLD = 2.0
        VOLUME_ANOMALY_NORMAL = 1.5
        VOLUME_ANOMALY_AUCTION = 2.0
        LOOKBACK_MINUTES = 60
        
        # ==================== SPREADS ====================
        HARD_SKIP_SPREAD_BPS = 40
        NORMAL_SPREAD_BPS = 30
        HIGH_VOL_SPREAD_BPS = 20
        
        # ==================== HMM REGIME ====================
        HMM_STATES = 3
        HMM_FIT_WINDOW_DAYS = 500
        HMM_REFIT_DAYS = 20
        
        # ==================== DRAWDOWN LADDER ====================
        DD_THRESHOLDS = [0.10, 0.20, 0.30, 0.40]
        DD_MULTIPLIERS = [0.75, 0.50, 0.25, 0.00]
        
        # ==================== PVS (PSYCHOLOGICAL) ====================
        PVS_WARNING_LEVEL = 7
        PVS_HALT_LEVEL = 9
        PVS_SMALL_CAPITAL_MULT = 1.5  # For <$5k
        SMALL_CAPITAL_THRESHOLD = 5000
        
        # ==================== CORRELATION ====================
        CORR_SOFT_DEEMPHASIS = 0.50
        CORR_SECTOR_NEUTRAL = 0.70
        CORR_MARKET_NEUTRAL = 0.85
        
        # ==================== CIRCUIT BREAKERS ====================
        CB_CONSECUTIVE_STOPS = 3
        CB_DAILY_LOSS = 0.05
        CB_WEEKLY_LOSS = 0.10
        CB_LIQUIDITY_SPREAD_MULT = 3.0
        CB_LIQUIDITY_VOLUME_MULT = 0.3
        
        # ==================== DYNAMIC SIZING ====================
        MIN_POSITION_SIZE = 2.50
        MAX_POSITION_SIZE = 20.00
        BASE_POSITION_SIZE = 5.00
        
        # ==================== ENTRY TIMING ====================
        ENTRY_WAIT_MIN = 15
        ENTRY_WAIT_MAX = 30
        MAX_RETRACEMENT = 0.50
        
        # ==================== EXHAUSTION ====================
        BOLL_PERIOD = 20
        BOLL_STD = 2.0
        MIN_COMPRESSION_HOURS = 3
        
        # ==================== PORTFOLIO CONSTRAINTS ====================
        MAX_BETA = 0.05
        MAX_SECTOR_MULTIPLIER = 2.0
        MAX_POSITION_PCT_NAV = 0.02
        MAX_POSITION_PCT_ADV = 0.05
        MAX_GROSS_EXPOSURE = 2.5
        MAX_NET_EXPOSURE = 0.10
        
        # ==================== CASCADE PREVENTION ====================
        MIN_EDGE_THRESHOLD = 2.0
        CASCADE_THRESHOLD = 2  # Block if ≥2 violations
        
        # Store all as instance variables
        for key, value in locals().items():
            if key != 'self' and not key.startswith('_'):
                setattr(self, key, value)
    
    def GetTimeOfDayMultiplier(self, hour, minute):
        """Get intraday risk scaling multiplier"""
        time_decimal = hour + minute / 60.0
        
        if 9.5 <= time_decimal < 10.0:
            return 0.7
        elif 10.0 <= time_decimal < 11.5:
            return 1.0
        elif 11.5 <= time_decimal < 13.0:
            return 0.8
        elif 13.0 <= time_decimal < 15.5:
            return 1.0
        elif 15.5 <= time_decimal <= 16.0:
            return 0.6
        else:
            return 0.5
    
    def IsAuctionPeriod(self, time):
        """Check if in auction period"""
        hour = time.hour
        minute = time.minute
        
        if hour == 9 and minute >= 30:
            return True
        if hour == 10 and minute == 0:
            return True
        if hour == 15 and minute >= 30:
            return True
        if hour == 16 and minute == 0:
            return True
        
        return False
