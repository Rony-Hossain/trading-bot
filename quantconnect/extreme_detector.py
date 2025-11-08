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
