# src/components/signals/signal_pipeline.py
from AlgorithmImports import *


class SignalPipeline:
    """
    Orchestrates:
      - building/maintaining minute bars
      - running extreme + exhaustion detectors
      - returning a unified list of detections
    """

    def __init__(self, algorithm):
        self.algo = algorithm
        self.config = algorithm.config
        self.logger = algorithm.logger

        # Use getattr so we don't explode if something is disabled / missing
        self.extreme_detector = getattr(algorithm, "extreme_detector", None)
        self.exhaustion_detector = getattr(algorithm, "exhaustion_detector", None)
        self.health_monitor = getattr(algorithm, "health_monitor", None)
        self.risk_monitor = getattr(algorithm, "risk_monitor", None)
        self.hmm_regime = getattr(algorithm, "hmm_regime", None)
        self.avwap_tracker = getattr(algorithm, "avwap_tracker", None)

    # ---------------- MINUTE BAR PIPELINE ----------------

    def UpdateMinuteBars(self, data) -> None:
        """
        Update or build 1-minute bars from raw QC data (Slice).

        Stores history on self.algo.minute_bars:
          minute_bars[symbol] = [TradeBar, TradeBar, ...]
        """

        minute_bars = self.algo.minute_bars

        for symbol, bar in data.Bars.items():
            if symbol not in minute_bars:
                minute_bars[symbol] = []
            minute_bars[symbol].append(bar)

            # Optional: cap history length to LOOKBACK_MINUTES
            if len(minute_bars[symbol]) > self.config.LOOKBACK_MINUTES:
                minute_bars[symbol] = minute_bars[symbol][-self.config.LOOKBACK_MINUTES :]

        # If HealthMonitor used to check missing symbols in OnData,
        # you can move that logic here and call self.health_monitor.run_health_check()
        # or a lighter data-quality check.

    def Run(self, data):
        """
        Primary entrypoint used by core_strategy.on_data.

        1) Update intraday minute-bar history.
        2) Scan for detections (extreme/exhaustion/etc.).
        3) Return list of detection dicts.
        """
        # Maintain rolling minute bars
        self.UpdateMinuteBars(data)

        # Scan for new signals
        return self.ScanForDetections()

    # ---------------- SCANNING PIPELINE ----------------

    def ScanForDetections(self) -> list[dict]:
        """
        Run extreme & exhaustion detectors and return a list of detection dicts.

        Contract:
            return [
                {
                    "symbol": Symbol,
                    "type": "extreme" / "exhaustion" / ...,
                    "direction": "up"/"down"/...,
                    # plus any extra fields your detectors already add
                },
                ...
            ]
        """

        detections: list[dict] = []

        # Defensive: if algo doesn't have minute_bars yet, nothing to do
        minute_bars = getattr(self.algo, "minute_bars", {}) or {}
        if not minute_bars:
            return detections

        # ---------- 1) EXTREME DETECTIONS ----------
        if self.extreme_detector is not None:
            # ExtremeDetector.Scan now returns list[dict]:
            #   [{"symbol": ..., "type": "extreme", "direction": "up"/"down", ...}, ...]
            extreme_candidates = self.extreme_detector.Scan(minute_bars) or []
            detections.extend(extreme_candidates)

        # ---------- 2) EXHAUSTION DETECTIONS (if present) ----------
        if self.exhaustion_detector is not None:
            exhaustion_raw = self.exhaustion_detector.Scan(minute_bars) or []

            normalized_exhaustion: list[dict] = []

            for item in exhaustion_raw:
                if isinstance(item, dict):
                    # Already a detection dict – make sure minimal keys exist
                    d = dict(item)
                    d.setdefault("type", "exhaustion")
                    normalized_exhaustion.append(d)
                else:
                    # Legacy: (symbol, info_dict)
                    try:
                        symbol, info = item
                    except Exception:
                        continue

                    info = dict(info)
                    info.setdefault("symbol", symbol)
                    info.setdefault("type", "exhaustion")
                    normalized_exhaustion.append(info)

            detections.extend(normalized_exhaustion)

        # ---------- 3) UPDATE RISK MONITOR / REGIME STATS ----------
        if self.hmm_regime is not None and self.risk_monitor is not None:
            regime_state = self.hmm_regime.GetCurrentRegime()
            # Pass all detections to RiskMonitor; it can filter by type if needed
            self.risk_monitor.Update(self.algo.Time, regime_state, detections)

        return detections
