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
