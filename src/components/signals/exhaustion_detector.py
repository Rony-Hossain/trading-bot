# src/components/signals/exhaustion_detector.py
"""
Exhaustion Detector - Phase 2

Detects exhaustion/mean-reversion opportunities (fade signals).

Detection Criteria (initial simple version):
1. Bollinger-band based exhaustion:
   - Price outside Boll(20, 2)
   - Then closing back inside => fade signal
"""

from AlgorithmImports import *
import numpy as np
from collections import deque


class ExhaustionDetector:
    """
    Detect exhaustion/mean-reversion opportunities.
    """

    def __init__(self, algorithm, config=None):
        self.algorithm = algorithm
        self.config = config or getattr(algorithm, "config", None)
        if self.config is None:
            raise ValueError("ExhaustionDetector requires a Config instance")

        self.logger = getattr(algorithm, "logger", None)

        # Use Config values where possible
        self.boll_period = getattr(self.config, "BOLL_PERIOD", 20)
        self.boll_std = getattr(self.config, "BOLL_STD", 2.0)
        self.min_compression_hours = getattr(
            self.config, "MIN_COMPRESSION_HOURS", 3
        )
        self.compression_threshold = 0.8  # Each range ≤ 0.8× prior

        # Tracking
        self.last_detection = {}      # symbol -> timestamp
        self.detection_cooldown = 30  # Minutes

        if self.logger:
            self.logger.info(
                "ExhaustionDetector initialized",
                component="ExhaustionDetector",
            )

    # --------- bar access helpers (dict or TradeBar) ----------

    def _bar_close(self, bar) -> float:
        if isinstance(bar, dict):
            return float(bar.get("close", 0) or 0)
        if hasattr(bar, "Close"):
            return float(bar.Close or 0)
        if hasattr(bar, "close"):
            return float(bar.close or 0)
        return 0.0

    def _bar_open(self, bar) -> float:
        if isinstance(bar, dict):
            return float(bar.get("open", 0) or 0)
        if hasattr(bar, "Open"):
            return float(bar.Open or 0)
        if hasattr(bar, "open"):
            return float(bar.open or 0)
        return 0.0

    def _bar_high(self, bar) -> float:
        if isinstance(bar, dict):
            return float(bar.get("high", 0) or 0)
        if hasattr(bar, "High"):
            return float(bar.High or 0)
        if hasattr(bar, "high"):
            return float(bar.high or 0)
        return 0.0

    def _bar_low(self, bar) -> float:
        if isinstance(bar, dict):
            return float(bar.get("low", 0) or 0)
        if hasattr(bar, "Low"):
            return float(bar.Low or 0)
        if hasattr(bar, "low"):
            return float(bar.low or 0)
        return 0.0

    def _bar_volume(self, bar) -> float:
        if isinstance(bar, dict):
            return float(bar.get("volume", 0) or 0)
        if hasattr(bar, "Volume"):
            return float(bar.Volume or 0)
        if hasattr(bar, "volume"):
            return float(bar.volume or 0)
        return 0.0

    def _bar_time(self, bar):
        if isinstance(bar, dict):
            return bar.get("time")
        if hasattr(bar, "EndTime"):
            return bar.EndTime
        if hasattr(bar, "Time"):
            return bar.Time
        return None

    # ---------------- CORE LOGIC ----------------

    def Detect(self, symbol, minute_bars):
        """
        Example exhaustion detector (simple Bollinger-band fade).

        Returns a dict with:
          - is_exhaustion: bool
          - direction: 'up' (fade long) or 'down' (fade short)
          - band_upper, band_lower, close, time, etc.
        """
        result = {
            "is_exhaustion": False,
            "direction": "neutral",
        }

        if len(minute_bars) < self.boll_period:
            return result

        recent = minute_bars[-self.boll_period:]

        closes = [self._bar_close(b) for b in recent]
        if not closes:
            return result

        mean = float(np.mean(closes))
        std = float(np.std(closes))

        if std <= 0:
            return result

        upper = mean + self.boll_std * std
        lower = mean - self.boll_std * std

        last_bar = recent[-1]
        last_close = self._bar_close(last_bar)
        ts = self._bar_time(last_bar)

        # Simple exhaustion: last close is outside band
        if last_close > upper:
            result["is_exhaustion"] = True
            result["direction"] = "down"  # fade short
        elif last_close < lower:
            result["is_exhaustion"] = True
            result["direction"] = "up"    # fade long
        else:
            return result

        result.update(
            {
                "band_upper": upper,
                "band_lower": lower,
                "close": last_close,
                "time": ts,
            }
        )
        return result

    def Scan(self, minute_bars):
        """
        Scan all symbols' minute bars and return a list of exhaustion detections.

        Parameters
        ----------
        minute_bars : dict[symbol, list[TradeBar|dict]]

        Returns
        -------
        list[dict] with at least:
            - 'symbol'
            - 'type'      (always 'exhaustion' here)
            - 'direction' ('up'/'down')
        """
        detections = []

        for symbol, bars in minute_bars.items():
            if not bars:
                continue

            res = self.Detect(symbol, bars)
            if not res.get("is_exhaustion", False):
                continue

            detections.append(
                {
                    "symbol": symbol,
                    "type": "exhaustion",
                    "direction": res.get("direction", "neutral"),
                    "time": res.get("time"),
                    "band_upper": res.get("band_upper"),
                    "band_lower": res.get("band_lower"),
                    "close": res.get("close"),
                    "raw": res,
                }
            )

        return detections

    # ---------------- ADVANCED HELPERS (optional, not yet wired) ----------------

    def _ConvertToHourly(self, minute_bars):
        """Convert minute bars to hourly bars (using dict-like structure)."""
        hourly = []
        current_hour = None
        hour_data = {
            "open": None,
            "high": None,
            "low": None,
            "close": None,
            "volume": 0,
            "time": None,
        }

        for bar in minute_bars:
            t = self._bar_time(bar)
            if t is None:
                continue

            bar_hour = t.replace(minute=0, second=0, microsecond=0)

            if current_hour is None:
                current_hour = bar_hour
                hour_data["open"] = self._bar_open(bar)
                hour_data["high"] = self._bar_high(bar)
                hour_data["low"] = self._bar_low(bar)
                hour_data["time"] = bar_hour

            if bar_hour != current_hour:
                # Close current hour
                hour_data["close"] = self._bar_close(bar)
                hourly.append(hour_data.copy())

                # Start new hour
                current_hour = bar_hour
                hour_data = {
                    "open": self._bar_open(bar),
                    "high": self._bar_high(bar),
                    "low": self._bar_low(bar),
                    "close": self._bar_close(bar),
                    "volume": self._bar_volume(bar),
                    "time": bar_hour,
                }
            else:
                # Update current hour
                hour_data["high"] = max(hour_data["high"], self._bar_high(bar))
                hour_data["low"] = min(hour_data["low"], self._bar_low(bar))
                hour_data["close"] = self._bar_close(bar)
                hour_data["volume"] += self._bar_volume(bar)

        if hour_data["open"] is not None:
            hourly.append(hour_data)

        return hourly

    def _CalculateATR(self, bars):
        """Calculate Average True Range on dict-like hourly bars."""
        if len(bars) < 2:
            return 0.0

        true_ranges = []
        for i in range(1, len(bars)):
            high = bars[i]["high"]
            low = bars[i]["low"]
            prev_close = bars[i - 1]["close"]

            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close),
            )
            true_ranges.append(tr)

        return float(np.mean(true_ranges)) if true_ranges else 0.0

    def GetExhaustionStats(self, symbol):
        """Get exhaustion detection statistics."""
        stats = {
            "has_history": symbol in self.last_detection,
            "last_detection": self.last_detection.get(symbol),
            "cooldown_active": False,
        }

        if symbol in self.last_detection:
            minutes_since = (
                self.algorithm.Time - self.last_detection[symbol]
            ).total_seconds() / 60
            stats["cooldown_active"] = minutes_since < self.detection_cooldown
            stats["minutes_since_last"] = minutes_since

        return stats
