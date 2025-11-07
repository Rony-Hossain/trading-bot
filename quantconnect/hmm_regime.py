"""
HMM Regime Classifier
3-state model: Low-Vol, High-Vol, Trending
Phase 1: Observation only - calculate posteriors but don't gate trades yet
"""

from AlgorithmImports import *
import numpy as np
from collections import deque

class HMMRegime:
    """Hidden Markov Model for regime detection"""
    
    def __init__(self, algorithm):
        self.algorithm = algorithm
        self.config = algorithm.config
        
        # States
        self.states = ['Low-Vol', 'High-Vol', 'Trending']
        self.n_states = len(self.states)
        
        # Current regime probabilities
        self.state_probs = {
            'Low-Vol': 0.33,
            'High-Vol': 0.33,
            'Trending': 0.34
        }
        
        # Feature history for fitting
        self.feature_history = deque(maxlen=self.config.HMM_FIT_WINDOW_DAYS)
        
        # Track market-wide features daily
        self.daily_features = {
            'realized_vol': [],
            'correlation': [],
            'vix_level': [],
            'spread_percentile': []
        }
        
        # Model state
        self.is_fitted = False
        self.last_fit_date = None
        self.days_since_fit = 0
        self.next_scheduled_fit = None  # Next scheduled fit date

        # For Phase 1 - simplified regime detection
        self.use_simplified = True  # Use heuristics instead of full HMM

        # Fit scheduling
        self.fit_on_warmup_end = True  # Fit when warmup completes
        self.refit_interval_days = self.config.HMM_REFIT_DAYS  # 20 days default
        
        # Subscribe to VIX for regime detection
        try:
            self.vix = algorithm.AddIndex("VIX", Resolution.Daily).Symbol
        except:
            self.vix = None
            algorithm.Log("Warning: VIX not available, using simplified regime detection")
    
    def Update(self, current_time):
        """
        Update regime probabilities
        Phase 1: Use simplified heuristic-based regime detection
        
        Returns dict with:
        - dominant_state: str
        - state_probs: dict
        - gpm: float (Global Position Multiplier)
        - requires_2x_edge: bool
        """
        
        if self.use_simplified:
            return self._SimplifiedRegime(current_time)
        else:
            return self._FullHMMRegime(current_time)
    
    def _SimplifiedRegime(self, current_time):
        """
        Simplified regime detection using market observables
        Good enough for Phase 1 observation
        """
        
        # Default to neutral
        regime = {
            'dominant_state': 'Low-Vol',
            'state_probs': {
                'Low-Vol': 0.50,
                'High-Vol': 0.25,
                'Trending': 0.25
            },
            'gpm': 1.0,  # Global Position Multiplier
            'requires_2x_edge': False,
            'correlation_breakdown': 0.0
        }
        
        # Try to get VIX level
        vix_level = self._GetVIXLevel()
        
        if vix_level is not None:
            # VIX-based regime classification
            if vix_level < 15:
                # Low volatility environment
                regime['dominant_state'] = 'Low-Vol'
                regime['state_probs'] = {
                    'Low-Vol': 0.70,
                    'High-Vol': 0.15,
                    'Trending': 0.15
                }
                regime['gpm'] = 1.0
                
            elif vix_level > 25:
                # High volatility environment
                regime['dominant_state'] = 'High-Vol'
                regime['state_probs'] = {
                    'Low-Vol': 0.10,
                    'High-Vol': 0.70,
                    'Trending': 0.20
                }
                regime['gpm'] = 0.3  # Reduce size in high vol
                regime['requires_2x_edge'] = True
                
            else:
                # Moderate/trending environment
                regime['dominant_state'] = 'Trending'
                regime['state_probs'] = {
                    'Low-Vol': 0.20,
                    'High-Vol': 0.30,
                    'Trending': 0.50
                }
                regime['gpm'] = 0.8
        
        # Calculate correlation breakdown (placeholder for now)
        # In production, this would analyze cross-correlation of returns
        regime['correlation_breakdown'] = 0.0
        
        return regime
    
    def _GetVIXLevel(self):
        """Get current VIX level if available"""
        if self.vix is None:
            return None
        
        try:
            history = self.algorithm.History(self.vix, 1, Resolution.Daily)
            if history.empty:
                return None
            return float(history['close'].iloc[-1])
        except:
            return None
    
    def _FullHMMRegime(self, current_time):
        """
        Full HMM implementation (for future Phase 2+)
        Currently returns simplified version
        """
        # TODO: Implement full Gaussian HMM with sklearn
        # For now, fall back to simplified
        return self._SimplifiedRegime(current_time)
    
    def _CollectFeatures(self):
        """
        Collect features for HMM fitting
        - Realized volatility
        - Correlation
        - Spread levels
        - VIX
        """
        features = {}
        
        # Get VIX
        vix = self._GetVIXLevel()
        if vix is not None:
            features['vix'] = vix
        
        # Get SPY returns for volatility
        try:
            spy = self.algorithm.Symbol("SPY")
            history = self.algorithm.History(spy, 20, Resolution.Daily)
            if not history.empty:
                returns = history['close'].pct_change().dropna()
                features['realized_vol'] = returns.std() * np.sqrt(252)
        except:
            pass
        
        return features
    
    def ShouldRefit(self, current_date):
        """
        Check if we should refit the HMM based on schedule

        Args:
            current_date: Current date

        Returns:
            bool: True if refit is due
        """
        # First fit (on warmup end)
        if not self.is_fitted and self.fit_on_warmup_end:
            return True

        # No scheduled refit date set yet
        if self.next_scheduled_fit is None:
            return False

        # Check if we've reached scheduled refit date
        if current_date >= self.next_scheduled_fit:
            return True

        return False

    def Fit(self, force=False):
        """
        Fit the HMM model with scheduling

        Args:
            force: Force fit regardless of schedule

        Returns:
            bool: True if fit was performed
        """
        current_date = self.algorithm.Time.date()

        # Check if fit should be performed
        if not force and not self.ShouldRefit(current_date):
            return False

        # For Phase 1: Use simplified heuristics (no actual fitting)
        self.is_fitted = True
        self.last_fit_date = current_date

        # Schedule next refit
        from datetime import timedelta
        self.next_scheduled_fit = current_date + timedelta(days=self.refit_interval_days)

        self.algorithm.Log(
            f"HMM: Fitted on {current_date.strftime('%Y-%m-%d')}, "
            f"next refit scheduled for {self.next_scheduled_fit.strftime('%Y-%m-%d')}"
        )

        return True

    def OnWarmupEnd(self):
        """
        Called when algorithm warmup ends - perform initial fit

        This should be called from main algorithm's OnWarmupEnd
        """
        if self.fit_on_warmup_end and not self.is_fitted:
            self.Fit(force=True)
            self.algorithm.Log("HMM: Initial fit completed after warmup")

    def GetCurrentRegime(self):
        """
        Get current regime state (convenience wrapper)

        Returns:
            dict: Current regime information with keys:
                - dominant_state: str ('Low-Vol', 'High-Vol', or 'Trending')
                - state_probs: dict of state probabilities
                - gpm: float (Global Position Multiplier, 0.3-1.0)
                - requires_2x_edge: bool (if high-vol regime)
                - correlation_breakdown: float (0.0-1.0)
        """
        return self.Update(self.algorithm.Time)

    def GetGlobalPositionMultiplier(self):
        """
        Get the current Global Position Multiplier (GPM)
        Used to scale position sizes based on regime
        """
        regime = self.Update(self.algorithm.Time)
        return regime['gpm']
    
    def GetRegimeSummary(self):
        """Get current regime summary for logging"""
        regime = self.Update(self.algorithm.Time)
        
        summary = f"Regime: {regime['dominant_state']}"
        summary += f" (GPM: {regime['gpm']:.2f})"
        
        if regime['requires_2x_edge']:
            summary += " [2x Edge Required]"
        
        return summary
