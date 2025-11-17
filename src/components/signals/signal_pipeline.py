# src/components/signals/signal_pipeline.py
from AlgorithmImports import *


class SignalPipeline:
    """
    Orchestrates:
      - building/maintaining minute bars
      - running extreme + exhaustion detectors
      - returning a unified list of detections

    This is where you move:
      - minute-bar update logic from main.OnData
      - _ScanForExtremes (and exhaustion scan) from main.py
    """

    def __init__(self, algorithm):
        self.algo = algorithm
        self.config = algorithm.config
        self.logger = algorithm.logger

        # Direct references to components the pipeline depends on
        self.extreme_detector = algorithm.extreme_detector
        self.exhaustion_detector = algorithm.exhaustion_detector
        self.health_monitor = algorithm.health_monitor
        self.risk_monitor = algorithm.risk_monitor
        self.hmm_regime = algorithm.hmm_regime
        self.avwap_tracker = algorithm.avwap_tracker

    # ---------------- MINUTE BAR PIPELINE ----------------

    def UpdateMinuteBars(self, data) -> None:
        """
        Update or build 1-minute bars from raw QC data (Slice).

        >>> THIS IS WHERE YOU PASTE THE MINUTE-BAR LOGIC FROM main.OnData <<<
        Currently you do something like:
          - for each symbol in data:
              - append TradeBar to self.minute_bars[symbol]
              - keep last N
              - notify HealthMonitor if missing
        Keep self.algo.minute_bars as the storage to avoid touching other code.
        """

        minute_bars = self.algo.minute_bars

        for symbol, bar in data.Bars.items():
            # Example structure – replace with your existing logic:
            if symbol not in minute_bars:
                minute_bars[symbol] = []
            minute_bars[symbol].append(bar)

            # If you currently cap history length, do that here:
            # if len(minute_bars[symbol]) > self.config.LOOKBACK_MINUTES:
            #     minute_bars[symbol] = minute_bars[symbol][-self.config.LOOKBACK_MINUTES :]

        # If HealthMonitor currently checks for missing bars in OnData,
        # move that logic here too.

    # ---------------- SCANNING PIPELINE ----------------

    def ScanForDetections(self) -> list[dict]:
        """
        Run extreme & exhaustion detectors and return a list of detection dicts.

        >>> THIS IS WHERE YOU MOVE _ScanForExtremes FROM main.py <<<

        Contract:
            return [
                {
                    "symbol": Symbol,
                    "type": "EXTREME_LONG" / "EXTREME_SHORT" / "EXHAUSTION_LONG" / ...,
                    "z_score": float,
                    "direction": "LONG"/"SHORT",
                    # plus any extra fields your detectors already add
                },
                ...
            ]
        """

        detections: list[dict] = []

        # 1) Build candidates for extreme detector from minute bars
        # Right now you probably do something like:
        #   candidates = self.extreme_detector.Scan(self.algo.minute_bars)
        # Move that here.
        minute_bars = self.algo.minute_bars

        # ---- Extreme detection (paste your existing logic here) ----
        extreme_candidates = self.extreme_detector.Scan(minute_bars)
        for symbol, info in extreme_candidates:
            detections.append(
                {
                    "symbol": symbol,
                    "type": info["type"],  # or whatever you currently use
                    "z_score": info.get("z_score", 0.0),
                    "direction": info.get("direction", "UNKNOWN"),
                    **info,
                }
            )

        # ---- Exhaustion detection (if you have it) ----
        # If you already scan for exhaustion separately in _ScanForExtremes,
        # move that code here as well:
        # exhaustion_signals = self.exhaustion_detector.Scan(minute_bars, ...)
        # for symbol, info in exhaustion_signals:
        #     detections.append({ ... })

        # 2) Update risk monitor / health here if you currently do it in _ScanForExtremes
        # Example: update regime state & candidates
        regime_state = self.hmm_regime.GetCurrentRegime()
        self.risk_monitor.Update(self.algo.Time, regime_state, extreme_candidates)

        return detections
