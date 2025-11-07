# System Architecture - Phase 1

## 📐 Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                       main.py (QCAlgorithm)                  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              QuantConnect Framework                   │  │
│  │  • Data feeds (minute bars)                          │  │
│  │  • Order execution                                   │  │
│  │  • Portfolio management                              │  │
│  │  • IBKR integration                                  │  │
│  └──────────────────────────────────────────────────────┘  │
│                            │                                 │
│                            ↓                                 │
│  ┌────────────────────────────────────────────────────┐    │
│  │                config.py                           │    │
│  │  • All parameters                                  │    │
│  │  • Thresholds and limits                           │    │
│  │  • Risk constraints                                │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┴───────────────────┐
        │                                       │
        ↓                                       ↓
┌──────────────────┐                  ┌──────────────────┐
│ universe_filter  │                  │ extreme_detector │
│                  │                  │                  │
│ • Coarse filter  │                  │ • Z-score calc   │
│ • Fine filter    │                  │ • Vol anomaly    │
│ • ~1000 stocks   │                  │ • Cooldown       │
└──────────────────┘                  └──────────────────┘
        │                                       │
        │                                       │
        ↓                                       ↓
┌──────────────────┐                  ┌──────────────────┐
│   hmm_regime     │                  │  avwap_tracker   │
│                  │                  │                  │
│ • VIX-based      │                  │ • Anchor VWAP    │
│ • 3 states       │                  │ • Track distance │
│ • GPM calc       │                  │ • Time stops     │
└──────────────────┘                  └──────────────────┘
        │                                       │
        └───────────────────┬───────────────────┘
                            ↓
                  ┌──────────────────┐
                  │  risk_monitor    │
                  │                  │
                  │ • Circuit break  │
                  │ • Daily summary  │
                  │ • Trade logging  │
                  └──────────────────┘
```

---

## 🔄 Data Flow (Hourly Cycle)

```
1. Market Data → minute bars collected
                 ↓
2. Universe Filter → select active stocks
                 ↓
3. Extreme Detector → scan for |Z₆₀| ≥ 2 + volume anomaly
                 ↓
4. HMM Regime → classify market state (Low/High/Trending)
                 ↓
5. A-VWAP Tracker → anchor from impulse, track distance
                 ↓
6. Risk Monitor → log everything, check circuit breakers
                 ↓
7. Decision → (Phase 1: observe only, no trades)
```

---

## 📊 Module Dependencies

```
main.py
├── config.py (no dependencies)
├── universe_filter.py → config
├── extreme_detector.py → config
├── hmm_regime.py → config
├── avwap_tracker.py → config
└── risk_monitor.py → config
```

**Upload Order:**
1. config.py first (base)
2. All others next (they import config)
3. main.py last (imports everything)

---

## 🎯 Signal Generation Pipeline

```
Raw Data (OHLCV)
    ↓
[60-min Rolling Window]
    ↓
[Calculate Returns & Volatility]
    ↓
[Z-score = return_60m / sigma_60m]
    ↓
[Volume Baseline by Hour-of-Day]
    ↓
[Volume Anomaly = current / median]
    ↓
[Check: |Z| ≥ 2 AND VolAnom ≥ 1.5x]
    ↓
    Yes → EXTREME DETECTED
    │     ↓
    │  [Anchor A-VWAP]
    │     ↓
    │  [HMM Regime Check]
    │     ↓
    │  [Risk Checks]
    │     ↓
    │  [Phase 1: Log Only]
    │
    No → Continue Scanning
```

---

## 🧩 Component Responsibilities

### main.py
- Orchestrates everything
- Manages QuantConnect lifecycle
- Handles data events (OnData, OnHourly, etc.)
- Coordinates between modules
- **Size:** ~250 lines

### config.py
- Central parameter store
- All thresholds and limits
- Time-of-day multipliers
- Blacklists
- **Size:** ~110 lines

### universe_filter.py
- Coarse filtering (price, volume)
- Fine filtering (security type, exchange)
- Universe rebalancing
- **Size:** ~90 lines

### extreme_detector.py
- Z-score calculation
- Volume anomaly detection
- Cooldown management
- Historical tracking
- **Size:** ~200 lines

### hmm_regime.py
- Simplified VIX-based regime
- 3-state classification
- GPM calculation
- Ready for full Gaussian HMM
- **Size:** ~220 lines

### avwap_tracker.py
- Anchor VWAP from impulse
- Distance calculations
- Time/distance stops
- Multi-symbol tracking
- **Size:** ~250 lines

### risk_monitor.py
- Circuit breaker monitoring
- Daily/weekly summaries
- Trade logging
- Drawdown tracking
- **Size:** ~280 lines

**Total:** ~1,400 lines of production code

---

## ⚙️ Key Parameters (config.py)

### Detection Thresholds
```python
Z_THRESHOLD = 2.0                    # |Z₆₀| ≥ 2
VOLUME_ANOMALY_NORMAL = 1.5          # 1.5x median
VOLUME_ANOMALY_AUCTION = 2.0         # 2x during open/close
```

### Universe
```python
UNIVERSE_SIZE = 1000
MIN_PRICE = 5.0
MAX_PRICE = 350.0
MIN_DOLLAR_VOLUME = 20_000_000
```

### Risk (Phase 1)
```python
INITIAL_CAPITAL = 1000
RISK_PER_TRADE = 5
MAX_POSITIONS = 1
MAX_TRADES_PER_DAY = 2
```

### A-VWAP
```python
AVWAP_ATR_MULTIPLIER = 0.5
AVWAP_MAX_BARS = 5  # hours
```

---

## 📈 Performance Considerations

### Computational Cost (per minute bar):
- Universe screening: O(1) (daily rebalance)
- Minute bar collection: O(N) where N = active symbols
- Hourly extreme scan: O(N) 
- A-VWAP updates: O(M) where M = tracked symbols
- HMM update: O(1) (simplified)

**Expected Load:**
- ~1,000 symbols monitored
- ~20-60 "in-play" at any time
- ~5-15 A-VWAP tracks active
- Hourly scans: <1 second
- Memory: <500MB

### Optimization Notes:
- Volume history uses deques (fixed size)
- Minute bars truncated to 24 hours
- Only active symbols processed
- Efficient numpy operations

---

## 🔐 Safety Layers

### Layer 1: Observation Mode
```python
OBSERVATION_MODE = True  # No trades execute
```

### Layer 2: Detection Filters
- Z-score threshold
- Volume anomaly threshold
- Spread checks
- Cooldown period

### Layer 3: Regime Gate
- HMM state assessment
- GPM position multiplier
- 2x edge requirement in High-Vol

### Layer 4: Risk Constraints
- Max positions (1 in Phase 1)
- Max trades per day (2)
- Risk per trade ($5)

### Layer 5: Circuit Breakers
- Daily loss limit
- Consecutive stopouts
- Correlation spike
- Liquidity crisis

### Layer 6: Time Guards
- Market hours only
- Time-of-day multipliers
- Auction period filters
- EOD position flattening

---

## 📊 Data Requirements

### From QuantConnect:
- Minute bars (OHLCV)
- Daily fundamentals
- Exchange/security type info
- VIX index data

### From IBKR:
- Account value
- Portfolio positions
- Order status
- (Future: live spreads, options chains)

### Historical Tracking:
- 20 days volume by hour
- 60 days for feature normalization
- 500 days for HMM fitting
- 252 days for drawdown

---

## 🎓 Design Principles

1. **Separation of Concerns:** Each module has single responsibility
2. **Configuration Driven:** All parameters in config.py
3. **Defensive Programming:** Extensive error checking and logging
4. **Phase-Aware:** Simple in Phase 1, ready for complexity
5. **Observation First:** Validate before trading
6. **Paper Before Live:** Build confidence gradually
7. **Safety by Default:** Conservative parameters, multiple guards

---

## 🔜 Phase 2+ Extensions

Ready to add (without major refactoring):

- Full Gaussian HMM (replace simplified)
- Options data (IV, skew, GEX)
- Exhaustion signals
- Spread guards with live data
- Sector neutrality
- Drawdown ladder enforcement
- PVS psychological governor
- Cascade prevention
- Meta-fitness tracking

All extension points are marked with "TODO" or "Phase 2+" comments in code.

---

## 📝 Code Quality

### Testing Strategy:
- Backtest on 6+ months
- Paper trade 4+ weeks
- Compare to strategy document
- Validate all parameters

### Logging Levels:
- **Normal:** Daily summaries, extremes detected
- **Verbose:** All filter decisions, A-VWAP updates
- **Debug:** Raw data, intermediate calculations

### Error Handling:
- Try/except around external data
- Graceful degradation (fallbacks)
- Clear error messages
- Continue on non-critical failures

---

*Architecture Document - Phase 1*
*Last Updated: November 6, 2024*
