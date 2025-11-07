# Pre-Live Trading Checklist

## Critical Safety Features to Add Before Live Trading

### Priority 1: MUST HAVE (Safety Critical) 🔴

- [ ] **1.1 Per-Trade Spread Guard Enforcement**
  - Location: `quantconnect/main.py` - in order execution logic
  - Check current spread before every order
  - Reject if `spread_bps > config.MAX_SPREAD_BPS`
  - Status: ⚠️ NOT IMPLEMENTED

- [ ] **1.2 Double-Check Execution Guards at Order Time**
  - Location: `quantconnect/main.py` - `_ExecuteTrade()` or equivalent
  - Re-verify before order send:
    - Daily trade limit not exceeded
    - Drawdown ladder allows trading
    - PVS not at halt level
    - Position limits not exceeded
  - Status: ⚠️ PARTIALLY IMPLEMENTED (needs consolidation)

- [ ] **1.3 Per-Symbol Cooldowns After Exits**
  - Location: `quantconnect/main.py` - track exit times
  - Prevent re-entry into same symbol for N minutes after exit
  - Ties into cascade prevention
  - Suggested: 60 minute cooldown
  - Status: ⚠️ NOT IMPLEMENTED

- [ ] **1.4 Recovery Circuit Breaker**
  - Location: `src/utils/recovery.py`
  - Add jitter + exponential backoff
  - Circuit "open" after N failed recovery attempts
  - Log recovery_attempts count
  - Status: ⚠️ NEEDS ENHANCEMENT

### Priority 2: HIGH PRIORITY (Stability) 🟡

- [ ] **2.1 Event-Driven Detection (Minute-Level)**
  - Location: `quantconnect/main.py` - `OnData()` method
  - Move from hourly to per-minute detection
  - Add internal rate limits (max detections per hour)
  - Keep hourly block for health/reporting only
  - Status: ⚠️ CURRENTLY HOURLY ONLY

- [ ] **2.2 ATR-Based Position Sizing**
  - Location: `quantconnect/dynamic_sizer.py` or equivalent
  - Replace fixed dollar sizing with ATR-based
  - Risk invariant across different volatility stocks
  - Formula: `size = risk_amount / (ATR * multiplier)`
  - Status: ⚠️ CURRENTLY FIXED DOLLAR

- [ ] **2.3 HMM Fit Scheduling & Persistence**
  - Location: `quantconnect/hmm_regime.py`
  - Explicit refit schedule (don't thrash on warm-up)
  - Save/load fitted model state
  - Log "2x edge required" to decision logs
  - Status: ⚠️ SIMPLIFIED VERSION ONLY

- [ ] **2.4 Wire scanner.yaml → AlertManager**
  - Location: `src/alerts/alert_manager.py`
  - Load scanner.yaml config
  - Map `mode`, `rate_limit_per_hour`, `min_signal_score`
  - Implement prompt throttling
  - Status: ⚠️ CONFIG EXISTS BUT NOT WIRED

### Priority 3: MEDIUM PRIORITY (Quality) 🟢

- [ ] **3.1 Options + Sector Breadth Adapters**
  - Location: New files or extend existing components
  - Options: IV rank, put/call skew, gamma exposure
  - Sector: A/D lines, sector rotation
  - Feed into weighted scores from scanner.yaml
  - Status: ⚠️ NOT IMPLEMENTED

- [ ] **3.2 Unify Config Sources**
  - Option A: Load scanner.yaml into Config on startup
  - Option B: Collapse into single source of truth
  - Prevent drift between code config and YAML
  - Status: ⚠️ DUAL SOURCES EXIST

- [ ] **3.3 Clean Encoding Artifacts**
  - Search for: "Zâ‚†â‚€", unicode arrows, checkmarks
  - Replace with ASCII or proper UTF-8
  - Prevents log parsing issues
  - Status: ⚠️ SOME ARTIFACTS PRESENT

- [ ] **3.4 Daily Health Digest**
  - Location: `src/monitoring/health_monitor.py`
  - Auto-generate daily summary PDF/CSV
  - Include: pass/fail, top symbols, avg metrics
  - Store in ObjectStore
  - Status: ⚠️ BASIC LOGGING EXISTS

---

## Implementation Plan

### Phase 1: Critical Safety (Do First) - 2-3 days

#### 1. Add Execution Guard Layer
```python
# quantconnect/main.py - Add before order execution

def _CheckExecutionGuards(self, symbol, direction, size):
    """
    Final safety check before order execution

    Returns:
        (bool, str): (allowed, reason)
    """
    # Daily trade limit
    if self.trades_today >= self.config.MAX_TRADES_PER_DAY:
        return False, "Daily trade limit reached"

    # Drawdown ladder
    dd_mult = self._GetDrawdownMultiplier()
    if dd_mult == 0:
        return False, "Drawdown ladder halted trading"

    # PVS check (v2+)
    if self.config.version >= 2 and self.config.ENABLE_PVS:
        pvs = self.pvs_tracker.GetCurrentPVS()
        if pvs >= self.config.PVS_HALT_LEVEL:
            return False, f"PVS at halt level: {pvs}"

    # Spread check
    spread_bps = self._GetCurrentSpread(symbol)
    if spread_bps > self.config.MAX_SPREAD_BPS:
        return False, f"Spread too wide: {spread_bps:.1f} bps"

    # Position limits
    if len(self.Portfolio) >= self.config.MAX_POSITIONS:
        return False, "Max positions reached"

    # Symbol cooldown
    if self._IsInCooldown(symbol):
        return False, f"Symbol in cooldown period"

    return True, "OK"
```

#### 2. Add Spread Guard at Trade Time
```python
def _GetCurrentSpread(self, symbol):
    """Get current bid-ask spread in basis points"""
    try:
        if symbol not in self.Securities:
            return float('inf')

        bid = self.Securities[symbol].BidPrice
        ask = self.Securities[symbol].AskPrice
        mid = (bid + ask) / 2

        if mid <= 0:
            return float('inf')

        spread_bps = ((ask - bid) / mid) * 10000
        return spread_bps
    except:
        return float('inf')  # Conservative: assume infinite spread on error
```

#### 3. Add Symbol Cooldown Tracking
```python
# In __init__:
self.symbol_cooldowns = {}  # symbol -> exit_time
self.COOLDOWN_MINUTES = 60

def _IsInCooldown(self, symbol):
    """Check if symbol is in cooldown after recent exit"""
    if symbol not in self.symbol_cooldowns:
        return False

    exit_time = self.symbol_cooldowns[symbol]
    elapsed = (self.Time - exit_time).total_seconds() / 60

    return elapsed < self.COOLDOWN_MINUTES

def _OnPositionExit(self, symbol):
    """Track exit time for cooldown"""
    self.symbol_cooldowns[symbol] = self.Time
```

### Phase 2: Stability Improvements - 3-5 days

#### 4. Event-Driven Detection
```python
def OnData(self, data):
    """Handle incoming data - check for extremes on every minute"""

    if self.IsWarmingUp:
        return

    try:
        # Update minute bars
        for symbol in self.active_symbols:
            if symbol in data and data[symbol]:
                self._UpdateMinuteBars(symbol, data[symbol])

        # Rate-limited detection (instead of hourly)
        if self._ShouldCheckForExtremes():
            self._ScanForExtremes()

        # v2+: Check pending entries for timing
        if self.config.version >= 2:
            self._CheckPendingEntries(data)
            self._ManagePositions(data)

    except Exception as e:
        self.logger.error(f"OnData error: {str(e)}", exception=e)

def _ShouldCheckForExtremes(self):
    """Rate limit extreme detection to avoid spam"""
    if not hasattr(self, '_last_scan_time'):
        self._last_scan_time = self.Time
        return True

    # Check at most once per 5 minutes
    elapsed = (self.Time - self._last_scan_time).total_seconds() / 60
    if elapsed >= 5:
        self._last_scan_time = self.Time
        return True

    return False
```

#### 5. ATR-Based Position Sizing
```python
def _CalculatePositionSize(self, symbol, direction, edge_score):
    """
    Calculate position size based on ATR

    Returns size in dollars (QC convention)
    """
    # Get base risk amount
    base_risk = self.config.BASE_POSITION_SIZE

    # Get ATR
    atr = self._GetATR(symbol, period=20)
    if atr <= 0:
        return 0

    # Get current price
    price = self.Securities[symbol].Price
    if price <= 0:
        return 0

    # ATR-based sizing: risk_amount / (ATR_dollars)
    # ATR in percentage terms
    atr_pct = atr / price

    # Size = base_risk / atr_pct
    # This makes risk consistent across different volatility stocks
    size = base_risk / atr_pct

    # Apply multipliers (regime, edge, etc.)
    if self.config.version >= 2 and self.config.ENABLE_DYNAMIC_SIZING:
        multipliers = self._GetSizeMultipliers(symbol, direction, edge_score)
        size *= multipliers

    # Clamp to limits
    size = max(self.config.MIN_POSITION_SIZE,
               min(size, self.config.MAX_POSITION_SIZE))

    return size
```

### Phase 3: Quality Improvements - 1 week

- Options adapters (IV rank, skew)
- Sector breadth (A/D lines)
- Config unification
- Health digest automation
- Encoding cleanup

---

## Testing Protocol

### Before Each Phase Goes Live:

1. **Paper Trading Test (1 week minimum)**
   - Run in observation mode
   - Verify all guards trigger correctly
   - Check logs for errors/exceptions

2. **Backtesting Verification**
   - Run 6-month backtest
   - Ensure new features don't break existing logic
   - Compare results to baseline

3. **Guard Trigger Tests**
   - Manually trigger each guard condition
   - Verify proper rejection and logging
   - Example: Set MAX_TRADES_PER_DAY=1, trigger 2 signals

4. **Stress Test**
   - Simulate high-volatility day
   - Verify PVS/drawdown guards work
   - Check recovery mechanisms

---

## Risk Summary

### Current State (After Basic Fixes):
- ✅ Config validation working
- ✅ Dictionary access safe
- ✅ HMM methods available
- ⚠️ **Spread guards NOT enforced at trade time**
- ⚠️ **No symbol cooldowns**
- ⚠️ **Detection is hourly (may miss ephemeral extremes)**
- ⚠️ **Fixed dollar sizing (not vol-adjusted)**

### Recommended Minimum Before Live:
Must complete **ALL Priority 1 items** (🔴):
1. Per-trade spread guard
2. Execution guard double-check
3. Symbol cooldowns
4. Recovery circuit breaker

### Ideal State Before Live:
Complete Priority 1 + Priority 2 (🔴 + 🟡):
- All safety guards
- Event-driven detection
- ATR-based sizing
- HMM persistence
- AlertManager integration

---

## Timeline Estimate

- **Minimum viable (P1 only)**: 2-3 days implementation + 1 week testing
- **Recommended (P1 + P2)**: 5-7 days implementation + 2 weeks testing
- **Full polish (P1 + P2 + P3)**: 2-3 weeks implementation + 2-3 weeks testing

---

## Decision Point

**Question for you:** Which path?

**A) Fast Track (P1 only)**
- Implement critical safety guards only
- Start paper trading in ~1 week
- Risk: May miss some signals due to hourly detection

**B) Balanced (P1 + P2)** ⭐ **RECOMMENDED**
- Add safety + stability features
- Start paper trading in ~2 weeks
- Better detection, more robust

**C) Full Polish (All priorities)**
- Complete production-ready system
- Start paper trading in ~1 month
- Maximum confidence

---

**Current Recommendation: Path B (Balanced)**
- Gives you solid safety AND performance
- 2-week implementation is manageable
- Significant improvement over current state

Would you like me to start implementing Path B, or do you prefer a different approach?
