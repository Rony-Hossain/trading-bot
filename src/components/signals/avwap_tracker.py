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
