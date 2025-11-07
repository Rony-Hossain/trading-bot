"""
Exhaustion Detector - Phase 2

Detects exhaustion/mean-reversion opportunities (fade signals).

Detection Criteria:
1. Bollinger re-entry: Price back inside Boll(20,2) after outside close
2. Range compression: ≥3 hours of shrinking ranges
3. Options tells (Phase 3): ΔIV declining, skew relaxing

Entry: Retest of outer band
Target: Revert to A-VWAP
Stop: Beyond extreme ± 0.3 ATR
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
        self.compression_threshold = 0.8  # Each range ≤ 0.8× prior
        
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
        Check for range compression (≥3 hours of shrinking ranges)
        
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
