"""
Extreme Detection - Core Signal Generator
Detects when a stock has an extreme 60-minute move with participation

Criteria:
1. |Z₆₀| ≥ 2 (60-min return z-score)
2. Volume anomaly ≥ 1.5x (2x during auction periods)
3. Spread checks pass
"""

from AlgorithmImports import *
import numpy as np
from collections import deque


class ExtremeDetector:
    """Detect price extremes with participation"""

    def __init__(self, algorithm, config=None):
        self.algorithm = algorithm
        # Prefer explicit config if given, else fall back to algorithm.config
        self.config = config or getattr(algorithm, "config", None)
        if self.config is None:
            raise ValueError("ExtremeDetector requires a Config instance")
        self.logger = getattr(algorithm, "logger", None)
        # Historical data for volume baseline
        self.volume_history = {}  # symbol -> {hour: deque of volumes}
        self.return_history = {}  # symbol -> deque of minute returns

        # Detection cache
        self.last_detection = {}  # symbol -> timestamp
        self.detection_cooldown = 15  # Minutes before re-detecting same symbol

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
        # QC TradeBar: EndTime is usually what you want
        if hasattr(bar, "EndTime"):
            return bar.EndTime
        if hasattr(bar, "Time"):
            return bar.Time
        return None

        # --------- time / auction helpers ----------

    def _is_auction_period(self, dt) -> bool:
        """
        Determine if we're in an 'auction' period.

        If Config has IsAuctionPeriod(dt), use that.
        Otherwise, fall back to:
          - first AUCTION_MINUTES after 9:30
          - last  AUCTION_MINUTES before 16:00
        """
        if dt is None:
            return False

        # If Config exposes a helper, use it
        if hasattr(self.config, "IsAuctionPeriod"):
            try:
                return bool(self.config.IsAuctionPeriod(dt))
            except Exception:
                # fall through to manual logic on error
                pass

        # Fallback manual logic using AUCTION_MINUTES from Config
        minutes = getattr(self.config, "AUCTION_MINUTES", 30)
        t = dt.hour + dt.minute / 60.0

        open_start = 9.5  # 9:30
        open_end = open_start + minutes / 60.0

        close_end = 16.0  # 4:00pm
        close_start = close_end - minutes / 60.0

        return (open_start <= t <= open_end) or (close_start <= t <= close_end)


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
            "is_extreme": False,
            "z_score": 0.0,
            "vol_anomaly": 0.0,
            "direction": "neutral",
            "return_60m": 0.0,
            "impulse_bar": None,
            "detection_time": None,
        }

        # Need at least 60 minutes of data
        if len(minute_bars) < self.config.MIN_BARS_FOR_DETECTION:
            return result

        # Get last 60 minutes
        recent_bars = minute_bars[-60:]

        # Calculate 60-minute return
        start_price = self._bar_close(recent_bars[0])
        end_price = self._bar_close(recent_bars[-1])
        if start_price > 0:
            return_60m = end_price / start_price - 1.0
        else:
            return_60m = 0.0

        # Calculate minute returns for volatility
        minute_returns = []
        for i in range(1, len(recent_bars)):
            prev_close = self._bar_close(recent_bars[i - 1])
            curr_close = self._bar_close(recent_bars[i])
            if prev_close > 0:
                ret = curr_close / prev_close - 1.0
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
        result["z_score"] = z_score
        result["return_60m"] = return_60m
        result["direction"] = "up" if return_60m > 0 else "down"

        # Check Z-score threshold
        if abs(z_score) < self.config.Z_THRESHOLD:
            return result

        # Calculate volume anomaly
        total_volume_60m = sum(self._bar_volume(bar) for bar in recent_bars)

        # Get hour of day for comparison
        current_time = self._bar_time(recent_bars[-1])
        if current_time is None:
            return result  # cannot proceed without a timestamp
        hour_of_day = current_time.hour

        # Update volume history
        if symbol not in self.volume_history:
            self.volume_history[symbol] = {}
        if hour_of_day not in self.volume_history[symbol]:
            self.volume_history[symbol][hour_of_day] = deque(
                maxlen=20
            )  # 20-day history

        # Get historical median for this hour
        hist_volumes = list(self.volume_history[symbol][hour_of_day])
        if len(hist_volumes) >= 5:  # Need at least 5 days
            median_volume = np.median(hist_volumes)
            vol_anomaly = total_volume_60m / median_volume if median_volume > 0 else 0.0
        else:
            vol_anomaly = 0.0  # Not enough history

        # Update history
        self.volume_history[symbol][hour_of_day].append(total_volume_60m)

        result["vol_anomaly"] = vol_anomaly

         # Check volume anomaly threshold (auction periods need 2x)
        is_auction = self._is_auction_period(current_time)
        vol_threshold = (
            self.config.VOLUME_ANOMALY_AUCTION
            if is_auction
            else self.config.VOLUME_ANOMALY_NORMAL
        )

        if vol_anomaly < vol_threshold:
            return result

        # Check cooldown (avoid re-detecting too quickly)
        if symbol in self.last_detection:
            minutes_since = (
                current_time - self.last_detection[symbol]
            ).total_seconds() / 60
            if minutes_since < self.detection_cooldown:
                return result

        # Check spread (if available - in Phase 1 we might not have this)
        # For now, we'll skip this check and add it when we have live data

        # All checks passed - this is an extreme!
        result["is_extreme"] = True
        result["detection_time"] = current_time
        last_bar = recent_bars[-1]
        result["impulse_bar"] = {
            "time": self._bar_time(last_bar),
            "open": self._bar_open(last_bar),
            "high": self._bar_high(last_bar),
            "low": self._bar_low(last_bar),
            "close": self._bar_close(last_bar),
            "volume": self._bar_volume(last_bar),
        }

        # Update detection time
        self.last_detection[symbol] = current_time

        return result

    def GetDetectionStats(self, symbol):
        """Get detection statistics for a symbol"""
        stats = {
            "has_volume_history": symbol in self.volume_history,
            "volume_history_length": 0,
            "last_detection": None,
        }

        if symbol in self.volume_history:
            total_entries = sum(len(v) for v in self.volume_history[symbol].values())
            stats["volume_history_length"] = total_entries

        if symbol in self.last_detection:
            stats["last_detection"] = self.last_detection[symbol]

        return stats

    def Scan(self, minute_bars):
        """
        Scan all symbols' minute bars and return a list of extreme detections.

        Parameters
        ----------
        minute_bars : dict[str | Symbol, list[dict]]
            Per-symbol minute bar history. Each bar dict should have:
              - 'time'
              - 'open'
              - 'high'
              - 'low'
              - 'close'
              - 'volume'

        Returns
        -------
        list[dict]
            List of detection dicts with at least:
            - 'symbol'
            - 'type'          (always 'extreme' here)
            - 'direction'     ('up' or 'down')
            - 'z_score'
            - 'vol_anomaly'
            - 'return_60m'
            - 'impulse_bar'
            - 'detection_time'
        """
        detections = []

        for symbol, bars in minute_bars.items():
            if not bars:
                continue

            result = self.Detect(symbol, bars)
            if not result.get("is_extreme", False):
                continue

            detections.append(
                {
                    "symbol": symbol,
                    "type": "extreme",
                    "direction": result["direction"],
                    "z_score": result["z_score"],
                    "vol_anomaly": result["vol_anomaly"],
                    "return_60m": result["return_60m"],
                    "impulse_bar": result["impulse_bar"],
                    "detection_time": result["detection_time"],
                    # Optionally keep full raw result if other components want it
                    "raw": result,
                }
            )

        return detections

    def ResetHistory(self, symbol):
        """Clear history for a symbol (e.g., after delisting)"""
        if symbol in self.volume_history:
            del self.volume_history[symbol]
        if symbol in self.return_history:
            del self.return_history[symbol]
        if symbol in self.last_detection:
            del self.last_detection[symbol]
