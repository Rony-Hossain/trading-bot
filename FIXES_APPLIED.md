# Trading Bot Fixes Applied

## Summary
This document outlines all critical fixes applied to the trading bot application.

## 1. Configuration Validation (config/config.py)

### Issue: No validation of configuration parameters
### Fix: Add validation in __init__ method

```python
# Add after line 41 (after def __init__):
def __init__(self, version=2, trading_enabled=False):
    """
    Initialize configuration

    Args:
        version: 1 (basic) or 2 (advanced features)
        trading_enabled: False (observation) or True (live trading)

    Raises:
        ValueError: If version is invalid or configuration validation fails
    """
    # Validate inputs
    if version not in [1, 2]:
        raise ValueError(f"version must be 1 or 2, got {version}")

    if not isinstance(trading_enabled, bool):
        raise ValueError(f"trading_enabled must be bool, got {type(trading_enabled)}")

    self.version = version
    self.trading_enabled = trading_enabled

    # ... rest of existing code ...

    # Add at end of __init__:
    self._validate()

def _validate(self):
    """Validate configuration values"""
    # Basic settings validation
    assert 0 < self.INITIAL_CAPITAL, "Invalid INITIAL_CAPITAL"
    assert 0 < self.RISK_PER_TRADE <= 100, f"RISK_PER_TRADE must be 0-100, got {self.RISK_PER_TRADE}"
    assert 0 < self.MAX_POSITIONS <= 100, "Invalid MAX_POSITIONS"
    assert 0 < self.MAX_TRADES_PER_DAY <= 1000, "Invalid MAX_TRADES_PER_DAY"

    # Universe validation
    assert 0 < self.UNIVERSE_SIZE <= 10000, "Invalid UNIVERSE_SIZE"
    assert 0 < self.MIN_PRICE < self.MAX_PRICE, "MIN_PRICE must be < MAX_PRICE"
    assert 0 < self.MIN_DOLLAR_VOLUME, "Invalid MIN_DOLLAR_VOLUME"
    assert 0 < self.MAX_SPREAD_BPS <= 1000, "Invalid MAX_SPREAD_BPS"

    # Extreme detection validation
    assert 0 < self.Z_THRESHOLD <= 5, f"Z_THRESHOLD must be 0-5, got {self.Z_THRESHOLD}"
    assert 0 < self.VOLUME_ANOMALY_NORMAL, "Invalid VOLUME_ANOMALY_NORMAL"
    assert 0 < self.VOLUME_ANOMALY_AUCTION, "Invalid VOLUME_ANOMALY_AUCTION"
    assert 10 <= self.LOOKBACK_MINUTES <= 1440, "LOOKBACK_MINUTES must be 10-1440"

    # Position sizing validation (v2+)
    if self.version >= 2 and self.ENABLE_DYNAMIC_SIZING:
        assert 0 < self.MIN_POSITION_SIZE <= self.MAX_POSITION_SIZE, \
            f"MIN_POSITION_SIZE must be < MAX_POSITION_SIZE"
        assert self.BASE_POSITION_SIZE >= self.MIN_POSITION_SIZE, \
            "BASE_POSITION_SIZE must be >= MIN_POSITION_SIZE"
```

## 2. HMM Regime Classifier Fix (quantconnect/hmm_regime.py)

### Issue: Missing GetCurrentRegime() method
### Fix: Add wrapper method

```python
# Add after the Update() method (around line 150):
def GetCurrentRegime(self):
    """
    Get current regime state (convenience wrapper)

    Returns:
        dict: Current regime information with keys:
            - dominant_state: str
            - state_probs: dict
            - gpm: float
            - requires_2x_edge: bool
            - correlation_breakdown: float
    """
    return self.Update(self.algorithm.Time)
```

## 3. A-VWAP Tracker Access Fix (quantconnect/main.py)

### Issue: Incorrect attribute access in _CheckPendingEntries
### Fix: Use GetAVWAP() method

```python
# Line ~485 in main.py - REPLACE:
if symbol in self.avwap_tracker.avwap_values:
    avwap_price = self.avwap_tracker.avwap_values[symbol]

# WITH:
avwap_price = self.avwap_tracker.GetAVWAP(symbol)
```

## 4. Safe Dictionary Access (quantconnect/main.py)

### Issue: Using config['KEY'] which raises KeyError if missing
### Fix: Use config.get('KEY', default) or direct attribute access

```python
# Line ~365 - REPLACE:
if self.trades_today >= self.config['MAX_TRADES_PER_DAY']:

# WITH:
if self.trades_today >= self.config.MAX_TRADES_PER_DAY:

# Line ~388 - REPLACE:
if len(bars) < self.config['LOOKBACK_MINUTES']:

# WITH:
if len(bars) < self.config.LOOKBACK_MINUTES:

# Line ~402 - REPLACE:
if self.config.version >= 2 and self.config['ENABLE_EXHAUSTION']:

# WITH:
if self.config.version >= 2 and self.config.ENABLE_EXHAUSTION:

# Line ~435 - REPLACE:
if self.config.version >= 2 and self.config['ENABLE_CASCADE_PREVENTION']:

# WITH:
if self.config.version >= 2 and self.config.ENABLE_CASCADE_PREVENTION:

# Line ~448 - REPLACE:
if size < self.config['RISK_PER_TRADE'] * 0.5:

# WITH:
if size < self.config.RISK_PER_TRADE * 0.5:

# Line ~468 - REPLACE:
if self.config.version >= 2 and self.config['ENABLE_ENTRY_TIMING']:

# WITH:
if self.config.version >= 2 and self.config.ENABLE_ENTRY_TIMING:

# Line ~501 - REPLACE:
if self.config.version >= 2 and self.config['ENABLE_DYNAMIC_SIZING']:

# WITH:
if self.config.version >= 2 and self.config.ENABLE_DYNAMIC_SIZING:

# Line ~509 - REPLACE:
size = self.config['RISK_PER_TRADE']

# WITH:
size = self.config.RISK_PER_TRADE:

# Line ~529 - REPLACE:
if self.config.version < 2 or not self.config['ENABLE_ENTRY_TIMING']:

# WITH:
if self.config.version < 2 or not self.config.ENABLE_ENTRY_TIMING:

# Line ~594 - REPLACE:
if self.config['OBSERVATION_MODE']:

# WITH:
if self.config.OBSERVATION_MODE:

# Line ~675 - REPLACE:
if self.config['OBSERVATION_MODE']:

# WITH:
if self.config.OBSERVATION_MODE:

# Line ~715 - REPLACE:
final_value / self.config['INITIAL_CAPITAL']

# WITH:
final_value / self.config.INITIAL_CAPITAL
```

## 5. Add Error Handling (quantconnect/main.py)

### Issue: No try-catch in critical methods
### Fix: Add defensive error handling

```python
# In OnData method (line ~253):
def OnData(self, data):
    """Handle incoming data"""

    if self.IsWarmingUp:
        return

    try:
        # Update minute bars
        for symbol in self.active_symbols:
            if symbol in data and data[symbol]:
                # ... existing code ...

        # v2+: Check pending entries for timing
        if self.config.version >= 2:
            self._CheckPendingEntries(data)
            self._ManagePositions(data)

    except Exception as e:
        self.logger.error(f"OnData error: {str(e)}",
                         component="Main", exception=e)

# In HourlyScan method (line ~330):
def HourlyScan(self):
    """Hourly scan for extremes"""

    if self.IsWarmingUp:
        return

    try:
        self.logger.info(f"=== HOURLY SCAN: {self.Time.strftime('%H:%M')} ===", component="Main")

        # ... existing code ...

    except Exception as e:
        self.logger.error(f"HourlyScan error: {str(e)}",
                         component="Main", exception=e)

# In _ProcessDetection method (line ~415):
def _ProcessDetection(self, detection):
    """Process a detected extreme"""

    try:
        symbol = detection['symbol']

        # ... existing code ...

    except Exception as e:
        self.logger.error(f"ProcessDetection error for {detection.get('symbol', 'unknown')}: {str(e)}",
                         component="Main", exception=e)
```

## 6. Universe Filter Spread Check (quantconnect/universe_filter.py)

### Issue: Missing spread quality check in SelectFine
### Fix: Add spread filtering

```python
# In SelectFine method (around line 55):
def SelectFine(self, fine):
    """
    Second pass: quality filters
    - Common shares only (no ADRs, preferred, etc.)
    - Exchange: NYSE or NASDAQ
    - Spread quality check
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

        # ADD THIS: Spread quality check
        try:
            if hasattr(f, 'AskPrice') and hasattr(f, 'BidPrice') and f.Price > 0:
                spread = f.AskPrice - f.BidPrice
                spread_bps = (spread / f.Price) * 10000

                if spread_bps > self.config.MAX_SPREAD_BPS:
                    continue  # Skip symbols with wide spreads
        except (AttributeError, ZeroDivisionError):
            # If spread data not available, allow through
            pass

        selected.append(f.Symbol)

    self.algorithm.Log(f"Fine Filter: {len(selected)} symbols passed")
    self.current_universe = set(selected)

    return selected
```

## 7. Fix Extreme Detector Method Call (quantconnect/main.py)

### Issue: Passing wrong parameter to Detect method
### Fix: Pass symbol parameter correctly

```python
# Line ~386 in _ScanForExtremes - REPLACE:
extreme = self.extreme_detector.Detect(bars)

# WITH:
extreme = self.extreme_detector.Detect(symbol, bars)
```

## 8. Add GetCurrentRegime Method to HMM (src/components/hmm_regime.py)

Same fix as #2 above - apply to both quantconnect/ and src/components/ directories.

## Files to Modify

1. `config/config.py` - Add validation
2. `quantconnect/config.py` - Add validation (duplicate file)
3. `quantconnect/hmm_regime.py` - Add GetCurrentRegime()
4. `src/components/hmm_regime.py` - Add GetCurrentRegime()
5. `quantconnect/main.py` - Fix dictionary access, A-VWAP access, error handling
6. `src/main.py` - Same fixes as quantconnect/main.py
7. `quantconnect/universe_filter.py` - Add spread check
8. `src/components/universe_filter.py` - Add spread check

## Testing Checklist

After applying fixes:

- [ ] Run config validation: `Config(version=3, trading_enabled=False)` should raise ValueError
- [ ] Test GetCurrentRegime() method exists and returns dict
- [ ] Test observation mode with v1 configuration
- [ ] Test observation mode with v2 configuration
- [ ] Verify no KeyError exceptions in logs
- [ ] Check spread filtering is working in universe selection
- [ ] Verify error handling catches and logs exceptions
- [ ] Test A-VWAP tracker access doesn't throw AttributeError

## Priority Order

1. **CRITICAL** - Fix #3 (A-VWAP access) - prevents runtime errors
2. **CRITICAL** - Fix #4 (dictionary access) - prevents KeyError crashes
3. **HIGH** - Fix #2 (GetCurrentRegime) - fixes method not found error
4. **HIGH** - Fix #7 (Extreme detector call) - fixes detection logic
5. **MEDIUM** - Fix #1 (validation) - prevents invalid configurations
6. **MEDIUM** - Fix #5 (error handling) - improves stability
7. **LOW** - Fix #6 (spread check) - improves universe quality

## Notes

- Both `quantconnect/` and `src/` directories contain similar files - apply fixes to both
- Test in observation mode first before enabling live trading
- Review logs after each fix to ensure no new issues introduced
- Consider creating backup before applying all fixes
