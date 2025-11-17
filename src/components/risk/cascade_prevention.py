"""
Cascade Prevention - Phase 2

Prevents cascade of bad decisions by blocking trades when ≥2 violations occur.

Violations:
- Weak signal (low edge)
- Loss streak (≥2 consecutive)
- High PVS (>7)
- Rule violation today
- Fatigue (>3 trades/hour)
- Regime uncertainty

Usage:
    from cascade_prevention import CascadePrevention

    cascade = CascadePrevention(algorithm)
    can_trade, violations = cascade.CheckCascadeRisk(trade_signal)
"""

from AlgorithmImports import *

class CascadePrevention:
    """Block trades when multiple violations occur"""

    def __init__(self, algorithm):
        self.algorithm = algorithm
        self.logger = getattr(algorithm, 'logger', None)

        # Get thresholds from config, with sane defaults. Be defensive: some
        # unit tests or lightweight runs may not attach a full `config` object
        # to the algorithm stub, so check for presence first.
        cascade_config = {}
        if getattr(algorithm, 'config', None) is not None:
            cascade_config = getattr(algorithm.config, 'CASCADE_PREVENTION', {})
        self.min_edge_threshold = cascade_config.get('MIN_EDGE_THRESHOLD', 2.0)
        self.cascade_threshold = cascade_config.get('CASCADE_THRESHOLD', 2)
        self.max_consecutive_losses = cascade_config.get('MAX_CONSECUTIVE_LOSSES', 2)
        self.pvs_threshold = cascade_config.get('PVS_THRESHOLD', 7)
        self.max_trades_per_hour = cascade_config.get('MAX_TRADES_PER_HOUR', 3)
        self.min_regime_confidence = cascade_config.get('MIN_REGIME_CONFIDENCE', 0.5)

    def CheckCascadeRisk(self,
                         trade_signal: dict,
                         pvs_score: float,
                         consecutive_losses: int,
                         regime_confidence: float,
                         trades_last_hour: int,
                         rule_violations: int
                         ) -> tuple[bool, list]:
        """
        Check if trade should be blocked due to cascade risk

        Returns:
            (bool, list): (can_trade, violations)
        """
        violations = []

        # Check each factor
        if abs(trade_signal.get('z_score', 0)) < self.min_edge_threshold:
            violations.append('weak_signal')

        if consecutive_losses >= self.max_consecutive_losses:
            violations.append('loss_streak')

        if pvs_score > self.pvs_threshold:
            violations.append('high_pvs')

        if rule_violations > 0:
            violations.append('rule_violation')

        if trades_last_hour > self.max_trades_per_hour:
            violations.append('fatigue')

        if regime_confidence < self.min_regime_confidence:
            violations.append('regime_uncertainty')

        # Block if ≥2 violations
        can_trade = len(violations) < self.cascade_threshold

        if not can_trade and self.logger:
            self.logger.warning(f"Cascade prevention: {violations}", component="CascadePrevention")

        return can_trade, violations
