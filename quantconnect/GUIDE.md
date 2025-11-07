# Extreme-Aware Trading Strategy - Phase 1 Implementation

## 📋 Overview

This is the **Phase 1 observation-mode implementation** of the Extreme-Aware US Equities strategy for QuantConnect + Interactive Brokers.

**Phase 1 Goals (Weeks 1-2):**
- ✅ Detect extremes (|Z₆₀| ≥ 2 + volume anomaly)
- ✅ Track HMM regime states (observe only)
- ✅ Calculate Anchored VWAP from impulse bars
- ✅ Monitor all signals without executing trades
- ✅ Build confidence in stack integration
- ✅ Log everything for analysis

**Current Mode:** 🔍 **OBSERVATION ONLY** - No real money at risk

---

## 🚀 Quick Start

### 1. Upload to QuantConnect

1. Create a new algorithm in QuantConnect
2. Upload all Python files to your project:
   - `main.py` (main algorithm)
   - `config.py` (parameters)
   - `universe_filter.py`
   - `extreme_detector.py`
   - `hmm_regime.py`
   - `avwap_tracker.py`
   - `risk_monitor.py`

### 2. Configure IBKR Connection

In QuantConnect settings:
- Set brokerage to **Interactive Brokers**
- Connect your IBKR account
- Verify paper trading account is active

### 3. Run Backtest

```python
# In main.py, set your backtest period:
self.SetStartDate(2024, 1, 1)
self.SetEndDate(2024, 11, 6)
self.SetCash(1000)
```

Click **Backtest** to run in historical mode.

### 4. Deploy to Paper Trading

Once satisfied with backtests:
1. Click **Deploy Live**
2. Select **Paper Trading** (not live account yet!)
3. Monitor the logs in real-time

---

## 📊 What Phase 1 Does

### Universe Selection
- Filters ~1,000 most liquid US stocks
- Price range: $5-$350
- Min daily volume: $20M
- Excludes blacklisted tickers

### Extreme Detection
Every hour, scans for:
- **Z-score ≥ 2:** 60-minute return is ≥2 standard deviations
- **Volume anomaly ≥ 1.5x:** Current hour's volume vs 20-day median
- **Logs all detections** but doesn't trade

### HMM Regime (Simplified)
- Classifies market as: **Low-Vol / High-Vol / Trending**
- Uses VIX levels as primary input
- Calculates Global Position Multiplier (GPM)
- **Phase 1:** Observe only, no gating applied

### A-VWAP Tracking
- Anchors VWAP from impulse bars
- Tracks price distance to A-VWAP
- Auto-expires after time/distance stops
- **Phase 1:** Monitor only

### Risk Monitoring
- Tracks all metrics
- Monitors circuit breaker conditions
- Generates daily/weekly reports
- **Phase 1:** No enforcement, just logging

---

## 📈 Reading the Logs

### Key Log Patterns

**Extreme Detected:**
```
🚨 EXTREME DETECTED: AAPL
   Z-score: 2.45
   Volume Anomaly: 2.1x
   Direction: up
   60m Return: +1.23%
```

**A-VWAP Update:**
```
AAPL A-VWAP Distance: +0.85%
```

**HMM Regime:**
```
HMM Regime: {'dominant_state': 'Low-Vol', 'gpm': 1.0, ...}
```

**Daily Summary:**
```
📈 Daily Summary:
   Extremes Detected: 15
   HMM Regime: Low-Vol
   Active A-VWAP Tracks: 3
   💡 OBSERVATION MODE - No trades executed
```

---

## ⚙️ Configuration

Edit `config.py` to adjust parameters:

```python
# Detection thresholds
self.Z_THRESHOLD = 2.0  # Increase to be more selective
self.VOLUME_ANOMALY_NORMAL = 1.5  # Increase for higher bar

# Risk limits (Phase 1)
self.INITIAL_CAPITAL = 1000
self.RISK_PER_TRADE = 5  # $5 per trade
self.MAX_POSITIONS = 1  # One at a time
```

---

## 🔄 Transitioning to Live Trading

When ready to go live (after 3-4 weeks of observation):

1. **Review logs:** Ensure extremes are detected correctly
2. **Check metrics:** Verify no excessive false positives
3. **Set live flag:** In `main.py`, change:
   ```python
   self.OBSERVATION_MODE = False  # Enable trading
   ```
4. **Start small:** Keep `RISK_PER_TRADE = 5` ($5 risk)
5. **Monitor closely:** Watch first few trades carefully

---

## 📁 File Structure

```
.
├── main.py                 # Main algorithm & orchestration
├── config.py              # All parameters
├── universe_filter.py     # Stock screening
├── extreme_detector.py    # Z-score + volume anomaly
├── hmm_regime.py          # Market regime classification
├── avwap_tracker.py       # Anchored VWAP calculations
├── risk_monitor.py        # Risk tracking & reporting
└── README.md              # This file
```

---

## 🎯 Phase 1 Success Criteria

Before moving to Phase 2, validate:

- ✅ **5-10 extremes detected per day** (reasonable rate)
- ✅ **HMM regime switches** align with VIX/market conditions
- ✅ **A-VWAP tracks** correctly anchor and expire
- ✅ **No data errors** or crashes
- ✅ **Logs are readable** and informative
- ✅ **QC + IBKR stack** working smoothly

**Target:** Run for **2-4 weeks** in paper mode before considering live trades.

---

## 📞 Support

Questions? Review your strategy document for detailed explanations of:
- Detection logic (Section 3-5)
- HMM regime model (Section 6)
- Risk management layers (Section 10)
- Implementation sequence (Section 11)

---

## ⚠️ Important Notes

1. **OBSERVATION MODE is ON by default** - No money at risk
2. **Paper trading first** - Don't skip this step
3. **Review daily logs** - Make sure signals make sense
4. **Start with $1k** - As per strategy doc
5. **Be patient** - Phase 1 is about learning the system

---

## 📝 Next Steps (Phase 2+)

After Phase 1 validation:
- Add drawdown ladder enforcement
- Add PVS (psychological governor)
- Add spread guards with live data
- Add exhaustion signals
- Enable HMM gating
- Integrate options data (GEX/IV/skew)

**Current Status:** 🏗️ Phase 1 - Observation & Validation
