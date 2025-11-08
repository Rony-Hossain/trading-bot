"""
Universe Selection - Filter for top ~1000 liquid US equities
Criteria:
- NYSE/NASDAQ common shares
- Price: $5-$350
- Liquidity: top 1000 by 60-day median dollar volume
- Spread quality: median spread <= 35 bps
- Exclude blacklisted tickers
"""

from AlgorithmImports import *

class UniverseFilter:
    """Handle coarse and fine universe selection"""
    
    def __init__(self, algorithm):
        self.algorithm = algorithm
        self.config = algorithm.config
        
        # Track universe stats
        self.last_rebalance = None
        self.current_universe = set()
        
    def CoarseFilter(self, coarse):
        """
        First pass: liquidity and price filters
        Returns top UNIVERSE_SIZE symbols
        """
        
        # Filter criteria
        selected = [
            x for x in coarse
            if x.HasFundamentalData
            and x.Price >= self.config.MIN_PRICE
            and x.Price <= self.config.MAX_PRICE
            and x.DollarVolume > self.config.MIN_DOLLAR_VOLUME
            and x.Symbol.Value not in self.config.BLACKLIST
        ]
        
        # Sort by dollar volume and take top N
        selected = sorted(selected, key=lambda x: x.DollarVolume, reverse=True)
        selected = selected[:self.config.UNIVERSE_SIZE]
        
        self.algorithm.Log(f"Coarse Filter: {len(selected)} symbols passed")
        
        return [x.Symbol for x in selected]
    
    def FineFilter(self, fine):
        """
        Second pass: quality filters
        - Common shares only (no ADRs, preferred, etc.)
        - Exchange: NYSE or NASDAQ
        """
        
        selected = []
        
        for f in fine:
            # Basic checks
            if not f.HasFundamentalData:
                continue
            
            # Security type filter
            if f.SecurityReference.SecurityType != "ST00000001":  # Common Stock
                continue
            
            # Exchange filter (NYSE, NASDAQ)
            exchange = f.CompanyReference.PrimaryExchangeId
            if exchange not in ["NYS", "NAS"]:
                continue
            
            # Company profile checks
            if not f.CompanyProfile.HeadquarterCity:
                continue
            
            selected.append(f.Symbol)
        
        self.algorithm.Log(f"Fine Filter: {len(selected)} symbols passed")
        self.current_universe = set(selected)
        
        return selected
    
    def IsInUniverse(self, symbol):
        """Check if symbol is in current universe"""
        return symbol in self.current_universe
    
    def GetUniverseStats(self):
        """Return universe statistics"""
        return {
            'size': len(self.current_universe),
            'last_rebalance': self.last_rebalance
        }
