# Version & Trading Mode System Guide

## The Problem with "Phase"

**OLD CONFUSING SYSTEM:**
- Phase 1 = Observation mode
- Phase 2 = Live trading

**Issues:**
- ❌ Confuses **features** (what capabilities exist) with **mode** (whether to trade)
- ❌ Can't test advanced features without trading
- ❌ Must jump from basic observation to live trading with advanced features
- ❌ No gradual progression path

---

## The NEW Clear System

### Two Independent Dimensions

```
┌─────────────────────────────────────────────────────┐
│  VERSION (Features)    ×    MODE (Trading)          │
├─────────────────────────────────────────────────────┤
│  v1 = Basic            ×    Observation = No trades │
│  v2 = Advanced         ×    Live = Real trades      │
└─────────────────────────────────────────────────────┘
```

### Version (Features Available)

| Version | Features |
|---------|----------|
| **v1** | Extreme detection, HMM regime, A-VWAP tracking |
| **v2** | **v1 PLUS** drawdown ladder, PVS, cascade prevention, dynamic sizing, entry timing, exhaustion detection, portfolio constraints |

### Mode (Whether to Execute Trades)

| Mode | Behavior |
|------|----------|
| **Observation** | Detect signals, log everything, **no real trades** |
| **Live Trading** | Detect signals, **execute real trades** |

---

## Configuration Examples

### Week 1-4: Learn the Basics

```python
config = Config(version=1, trading_enabled=False)
```

- ✅ Basic features only
- ✅ Observation mode (no trading)
- ✅ Learn how extremes are detected
- ✅ Understand regime switching
- ✅ See A-VWAP tracking in action

**Result:** Build confidence in core signal generation

---

### Week 5-8: Test Advanced Features

```python
config = Config(version=2, trading_enabled=False)
```

- ✅ ALL features enabled
- ✅ Still observation mode (no trading)
- ✅ Test drawdown ladder behavior
- ✅ Monitor PVS scores
- ✅ See cascade prevention in action
- ✅ Verify entry timing protocol
- ✅ Check exhaustion signals

**Result:** Understand advanced risk management WITHOUT risking capital

---

### Week 9+: Go Live

```python
config = Config(version=2, trading_enabled=True)
```

- ✅ ALL features enabled
- ✅ **LIVE TRADING** - executes real orders
- ✅ All safety systems active
- ✅ Full risk management

**Result:** Fully protected live trading

---

## Quick Reference

### How to Set Configuration

Edit **line 92** in [src/main.py](src/main.py#L92):

```python
# Week 1-4: Learn basics
self.config = Config(version=1, trading_enabled=False)

# Week 5-8: Test advanced features
self.config = Config(version=2, trading_enabled=False)

# Week 9+: Go live
self.config = Config(version=2, trading_enabled=True)
```

### Helper Functions (Shortcuts)

```python
# Instead of typing it out, use shortcuts:
from config.config import config_v1_observe, config_v2_observe, config_v2_live

# Week 1-4
self.config = config_v1_observe()

# Week 5-8
self.config = config_v2_observe()

# Week 9+
self.config = config_v2_live()
```

---

## Feature Comparison

| Feature | v1 | v2 |
|---------|----|----|
| **Core Detection** | | |
| Extreme detection (Z-score + volume) | ✅ | ✅ |
| HMM regime classification | ✅ | ✅ |
| A-VWAP tracking | ✅ | ✅ |
| Risk monitoring | ✅ | ✅ |
| **Advanced Risk Management** | | |
| Drawdown ladder (progressive size reduction) | ❌ | ✅ |
| PVS (psychological fatigue monitoring) | ❌ | ✅ |
| Cascade prevention (multi-violation blocking) | ❌ | ✅ |
| Dynamic position sizing (Kelly-inspired) | ❌ | ✅ |
| Entry timing protocol (15-30 min wait) | ❌ | ✅ |
| Exhaustion/fade signals | ❌ | ✅ |
| Portfolio constraints (beta, sector limits) | ❌ | ✅ |

---

## What Happens When You Set Each Configuration

### `Config(version=1, trading_enabled=False)`

**Components Initialized:**
- ✅ Universe filter
- ✅ Extreme detector
- ✅ HMM regime classifier
- ✅ A-VWAP tracker
- ✅ Risk monitor
- ✅ Logger
- ✅ Alert manager
- ✅ Backtest analyzer
- ✅ Health monitor

**Components NOT Initialized:**
- ❌ Drawdown enforcer
- ❌ PVS monitor
- ❌ Exhaustion detector
- ❌ Portfolio constraints
- ❌ Cascade prevention
- ❌ Dynamic sizer
- ❌ Entry timing

**Behavior:**
- Detects extremes hourly
- Logs signals (observation mode)
- **No trades executed**

---

### `Config(version=2, trading_enabled=False)`

**Components Initialized:**
- ✅ All v1 components
- ✅ **Drawdown enforcer**
- ✅ **PVS monitor**
- ✅ **Exhaustion detector**
- ✅ **Portfolio constraints**
- ✅ **Cascade prevention**
- ✅ **Dynamic sizer**
- ✅ **Entry timing**

**Behavior:**
- Detects extremes hourly
- Applies ALL risk checks
- Calculates dynamic position sizes
- Monitors drawdown ladder
- Tracks PVS scores
- Logs everything (observation mode)
- **Still no trades executed** (safe testing)

---

### `Config(version=2, trading_enabled=True)`

**Components Initialized:**
- ✅ All v2 components (everything)

**Behavior:**
- Detects extremes hourly
- Applies ALL risk checks
- **EXECUTES REAL TRADES** when signals pass all checks
- Manages active positions
- Exits based on targets/stops/time

---

## Configuration Properties

### Always Available

```python
config.OBSERVATION_MODE          # True if trading_enabled=False
config.version                   # 1 or 2
config.trading_enabled           # True or False

# Basic settings (always present)
config.RISK_PER_TRADE           # 5.0
config.MAX_POSITIONS            # 1
config.MAX_TRADES_PER_DAY       # 2
config.UNIVERSE_SIZE            # 1000
config.Z_THRESHOLD              # 2.0
config.VOLUME_ANOMALY_NORMAL    # 1.5

# ... all other config values
```

### Version-Dependent Flags

```python
# These are automatically set based on version:
config.ENABLE_EXHAUSTION              # True if version >= 2
config.ENABLE_PVS                     # True if version >= 2
config.ENABLE_CASCADE_PREVENTION      # True if version >= 2
config.ENABLE_DYNAMIC_SIZING          # True if version >= 2
config.ENABLE_ENTRY_TIMING            # True if version >= 2
config.ENFORCE_DRAWDOWN_LADDER        # True if version >= 2
config.ENFORCE_SECTOR_NEUTRALITY      # True if version >= 2
```

---

## Migration from Old "Phase" System

### OLD System (Confusing)

```python
# Phase 1 = observation
config = Config(phase=1)

# Phase 2 = live trading
config = Config(phase=2)
```

### NEW System (Clear)

```python
# v1, observation (equivalent to old Phase 1)
config = Config(version=1, trading_enabled=False)

# v2, observation (NEW - test advanced features safely!)
config = Config(version=2, trading_enabled=False)

# v2, live trading (equivalent to old Phase 2)
config = Config(version=2, trading_enabled=True)
```

---

## Recommended Learning Path

### ✅ Week 1-4: Foundation Building

**Config:**
```python
Config(version=1, trading_enabled=False)
```

**Focus:**
- Understand extreme detection criteria
- Learn regime classification patterns
- Study A-VWAP anchor behavior
- Review daily logs
- Identify false positives

**Success Criteria:**
- Can predict extremes before they trigger
- Understand regime switches
- Trust the signal generation

---

### ✅ Week 5-8: Advanced Testing

**Config:**
```python
Config(version=2, trading_enabled=False)
```

**Focus:**
- Monitor drawdown ladder activations
- Study PVS score patterns
- Review cascade prevention blocks
- Verify dynamic sizing calculations
- Check entry timing delays
- Analyze exhaustion signals

**Success Criteria:**
- Understand when/why trades get blocked
- See how position sizes adjust
- Trust the risk management systems
- Ready to trade live

---

### ✅ Week 9+: Live Trading

**Config:**
```python
Config(version=2, trading_enabled=True)
```

**Focus:**
- Monitor real trades
- Track P&L
- Verify systems work as expected
- Scale gradually if successful

**Success Criteria:**
- Consistent with backtest results
- All safety systems working
- Comfortable with live trading

---

## Testing Scenarios

### Test Drawdown Ladder (v2, observation)

```python
config = Config(version=2, trading_enabled=False)

# Manually adjust starting capital to simulate drawdown
self.SetCash(900)  # Simulate 10% drawdown
# Check logs: should show 0.75x size multiplier
```

### Test PVS Monitoring (v2, observation)

```python
config = Config(version=2, trading_enabled=False)

# After multiple simulated losses
# Check logs: PVS should increase
# Verify size reduction at PVS >= 7
# Verify halt at PVS >= 9
```

### Test Cascade Prevention (v2, observation)

```python
config = Config(version=2, trading_enabled=False)

# When weak signals appear (Z < 2.0)
# After loss streaks
# During high PVS
# Check logs: trades should be blocked
```

---

## FAQ

### Q: Why separate version and trading mode?

**A:** So you can **test advanced features safely** before risking capital. With old system, you had to jump from basic observation directly to live trading with advanced features. Now you can test advanced features in observation mode first.

### Q: Should I ever use v1 with trading enabled?

**A:** **Not recommended.** v1 lacks critical safety systems. Only trade live with v2.

### Q: Can I switch configurations mid-backtest?

**A:** No. Set config at initialization (line 92 in main.py). To test different configs, run separate backtests.

### Q: What's the difference between OBSERVATION_MODE and trading_enabled?

**A:** They're inverses:
- `trading_enabled=False` → `OBSERVATION_MODE=True`
- `trading_enabled=True` → `OBSERVATION_MODE=False`

We keep both for backward compatibility and clarity.

### Q: How do I know which version I'm running?

**A:** Check the initialization logs:

```
EXTREME-AWARE STRATEGY - V2 (ADVANCED) - OBSERVATION
Version: 2 | Mode: OBSERVATION (no trades)
```

---

## Summary

| Configuration | Use Case | Trades? | Features |
|---------------|----------|---------|----------|
| `Config(version=1, trading_enabled=False)` | Learn basics | ❌ No | Basic only |
| `Config(version=2, trading_enabled=False)` | Test advanced | ❌ No | All features |
| `Config(version=2, trading_enabled=True)` | Live trading | ✅ YES | All features |

**Golden Rule:** Always test in observation mode (`trading_enabled=False`) before going live!

---

## Code Examples

### Checking Version in Components

```python
# In any component that has access to algorithm.config:

if self.algorithm.config.version >= 2:
    # Use advanced features
    self.exhaustion_detector.Detect(symbol, bars)
else:
    # Skip advanced features
    pass
```

### Checking Trading Mode

```python
if self.algorithm.config.OBSERVATION_MODE:
    # Log what would happen
    self.logger.info(f"Would enter {shares} shares")
else:
    # Execute real trade
    self.MarketOrder(symbol, shares)
```

### Both Checks Together

```python
# Only use cascade prevention if v2+ AND any mode
if self.config.version >= 2:
    can_trade, violations = self.cascade_prevention.CheckCascadeRisk(...)
    if not can_trade:
        return  # Block trade
```

---

**Need Help?** See:
- [config/README.md](config/README.md) - Configuration reference
- [CONSOLIDATION_SUMMARY.md](CONSOLIDATION_SUMMARY.md) - Migration guide
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - System design
