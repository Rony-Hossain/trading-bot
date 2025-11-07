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
        self.logger = algorithm.logger if hasattr(algorithm, 'logger') else None
        self.min_edge_threshold = 2.0  # Minimum |Z|
        self.cascade_threshold = 2  # Block if ≥2 violations
        
    def CheckCascadeRisk(self, trade_signal, pvs_score, consecutive_losses, 
                         regime_confidence, trades_last_hour, rule_violations):
        """
        Check if trade should be blocked due to cascade risk
        
        Returns:
            (bool, list): (can_trade, violations)
        """
        violations = []
        
        # Check each factor
        if trade_signal.get('z_score', 0) < self.min_edge_threshold:
            violations.append('weak_signal')
        
        if consecutive_losses >= 2:
            violations.append('loss_streak')
        
        if pvs_score > 7:
            violations.append('high_pvs')
        
        if rule_violations > 0:
            violations.append('rule_violation')
        
        if trades_last_hour > 3:
            violations.append('fatigue')
        
        if regime_confidence < 0.5:
            violations.append('regime_uncertainty')
        
        # Block if ≥2 violations
        can_trade = len(violations) < self.cascade_threshold
        
        if not can_trade and self.logger:
            self.logger.warning(f"Cascade prevention: {violations}", component="CascadePrevention")
        
        return can_trade, violations
