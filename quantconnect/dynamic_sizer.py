"""
Dynamic Position Sizer - Phase 2

Kelly-inspired position sizing based on edge quality.

Formula:
base_size * edge_mult * regime_mult * dd_mult * pvs_mult

Multipliers:
- Edge: 1x to 2x (based on |Z|)
- Regime: 0.3 to 1.0 (from HMM GPM)
- Drawdown: 0.0 to 1.0 (from DD ladder)
- PVS: 0.0 to 1.0 (from psychological state)

Usage:
    from dynamic_sizer import DynamicSizer
    
    sizer = DynamicSizer(algorithm)
    size = sizer.CalculateSize(signal, regime, dd, pvs)
"""

from AlgorithmImports import *

class DynamicSizer:
    """Dynamic position sizing based on multiple factors"""
    
    def __init__(self, algorithm):
        self.algorithm = algorithm
        self.base_size = 5.0  # $5 base
        self.min_size = 2.50
        self.max_size = 20.0
        
    def CalculateSize(self, z_score, gpm, dd_mult, pvs_mult):
        """
        Calculate position size
        
        Args:
            z_score: Signal Z-score
            gpm: Global Position Multiplier (regime)
            dd_mult: Drawdown multiplier
            pvs_mult: PVS multiplier
        
        Returns:
            float: Position size in dollars
        """
        
        # Edge multiplier (1x to 2x)
        edge_mult = min(abs(z_score) / 2.0, 2.0)
        
        # Combine all multipliers
        total_mult = edge_mult * gpm * dd_mult * pvs_mult
        
        # Calculate size
        size = self.base_size * total_mult
        
        # Apply caps
        size = max(self.min_size, min(size, self.max_size))
        
        return size
