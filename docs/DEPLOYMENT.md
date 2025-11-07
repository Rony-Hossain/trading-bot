# QuantConnect Deployment Guide

## 🚀 Step-by-Step Deployment

### 1. Create QuantConnect Account
1. Go to https://www.quantconnect.com
2. Sign up for free account
3. Navigate to "Algorithm Lab"

### 2. Create New Project
1. Click "Create New Algorithm"
2. Name it: `Extreme-Aware-Phase1`
3. Select Python as language

### 3. Upload Files

Upload these files **in order** (dependencies first):

```
1. config.py              # Parameters - no dependencies
2. universe_filter.py     # Uses config
3. extreme_detector.py    # Uses config
4. hmm_regime.py         # Uses config
5. avwap_tracker.py      # Uses config
6. risk_monitor.py       # Uses config
7. main.py              # Main algorithm - uses everything
```

**How to upload:**
- Click "+" button in file explorer
- Select "Upload File"
- Choose each .py file
- Click "Upload"

### 4. Configure IBKR Connection

#### In QuantConnect:
1. Go to "Live Trading" → "Brokerage"
2. Select "Interactive Brokers"
3. Enter your IBKR credentials
4. Verify connection is green

#### In IBKR:
1. Enable API connections in TWS/Gateway
2. Set socket port: 4001 (paper) or 7496 (live)
3. Trust QuantConnect IP addresses
4. Enable "Download open orders on connection"

### 5. Set Initial Parameters

In `main.py`, verify these settings:

```python
# Backtest period
self.SetStartDate(2024, 1, 1)
self.SetEndDate(2024, 11, 6)
self.SetCash(1000)

# Safety flags
self.OBSERVATION_MODE = True  # Keep this True initially!
self.MAX_CONCURRENT_POSITIONS = 1
self.RISK_PER_TRADE = 5
```

### 6. Run Backtest

1. Click "Backtest" button (looks like a play button)
2. Wait for backtest to complete (2-5 minutes)
3. Review the logs in the "Logs" tab
4. Check for errors

**Expected log output:**
```
Phase 1 Observation Mode - Initialized
Capital: $1000.00
Observation Mode: True
Coarse Filter: 1000 symbols passed
Fine Filter: 850 symbols passed
HMM: Using simplified regime detection (Phase 1)
```

### 7. Deploy to Paper Trading

**⚠️ Critical: Only deploy to PAPER TRADING first!**

1. Click "Deploy Live"
2. Select **"Paper Trading"** (NOT live account)
3. Choose IBKR as brokerage
4. Confirm deployment
5. Monitor in "Live Trading" dashboard

### 8. Monitor Live Logs

Once deployed:
1. Go to "Live Trading" tab
2. Click on your algorithm
3. View real-time logs
4. Look for extreme detections

**What to watch for:**
- ✅ Algorithm starts without errors
- ✅ Universe loads (~1000 stocks)
- ✅ Hourly checks run on schedule
- ✅ Extremes are detected (5-10 per day is normal)
- ✅ A-VWAP tracks are created
- ✅ Daily summaries appear at market close

---

## 🔍 Reading QuantConnect Logs

### Log Levels
- **INFO:** Normal operation (blue)
- **WARNING:** Worth noting but not critical (yellow)
- **ERROR:** Something went wrong (red)

### Key Events to Monitor

**Startup:**
```
INFO: Phase 1 Observation Mode - Initialized
INFO: Active Universe Size: 987
```

**Hourly Scan:**
```
INFO: ============================================================
INFO: Hourly Check: 2024-11-06 10:00:00
INFO: HMM Regime: {'dominant_state': 'Low-Vol', 'gpm': 1.0}
```

**Extreme Detection:**
```
INFO: 🚨 EXTREME DETECTED: AAPL
INFO:    Z-score: 2.45
INFO:    Volume Anomaly: 2.1x
INFO:    Direction: up
INFO:    60m Return: +1.23%
INFO: A-VWAP: Started tracking AAPL from $175.23
```

**Daily Close:**
```
INFO: 🔔 Market Close: 2024-11-06
INFO: 📈 Daily Summary:
INFO:    Extremes Detected: 12
INFO:    HMM Regime: Low-Vol
INFO:    Active A-VWAP Tracks: 3
INFO:    💡 OBSERVATION MODE - No trades executed
```

---

## 🛠️ Troubleshooting

### "Module Not Found" Error
**Problem:** Files uploaded in wrong order
**Solution:** 
1. Delete all files
2. Re-upload in the order listed above
3. Ensure `config.py` is uploaded first

### No Extremes Detected
**Problem:** Thresholds too strict or quiet market
**Solution:**
1. Reduce `Z_THRESHOLD` to 1.5 in `config.py`
2. Reduce `VOLUME_ANOMALY_NORMAL` to 1.2
3. Wait for more volatile market conditions

### Universe is Empty
**Problem:** Filters too restrictive
**Solution:**
1. Lower `MIN_DOLLAR_VOLUME` to 10M in `config.py`
2. Check that market data subscription is active

### IBKR Connection Failed
**Problem:** IBKR not configured properly
**Solution:**
1. Verify TWS/Gateway is running
2. Check API settings in IBKR
3. Confirm QuantConnect has correct credentials
4. Try paper trading account instead of live

### Algorithm Stops Running
**Problem:** Runtime error or resource limit
**Solution:**
1. Check "Logs" tab for error messages
2. Reduce `UNIVERSE_SIZE` to 500 in `config.py`
3. Contact QuantConnect support if persistent

---

## 📊 Verifying Phase 1 is Working

After 1 week of paper trading, you should see:

✅ **Detection Stats:**
- 25-50 extremes detected for the week
- Mix of up and down extremes
- Various sectors represented

✅ **A-VWAP Tracking:**
- 5-15 active tracks at any time
- Tracks expire after 3-5 hours
- Distance calculations look reasonable

✅ **HMM Regime:**
- Switches between states when market changes
- High-Vol during news/earnings
- Low-Vol during calm periods

✅ **No Errors:**
- No red ERROR messages in logs
- Algorithm runs continuously
- No disconnections from IBKR

---

## 🎯 Weekly Review Checklist

Every Friday, review:

- [ ] Total extremes detected this week
- [ ] Any obvious false positives?
- [ ] Regime classifications make sense?
- [ ] Any errors or crashes?
- [ ] IBKR connection stable?
- [ ] Ready to continue Phase 1?

**After 4 weeks:** Decide if ready to enable trading

---

## 📞 Getting Help

**QuantConnect Documentation:**
- https://www.quantconnect.com/docs

**IBKR API Setup:**
- https://www.interactivebrokers.com/en/software/api/api.htm

**Community Forums:**
- https://www.quantconnect.com/forum

**Your Strategy Document:**
- Re-read Sections 3-5 for detection logic
- Re-read Section 11 for implementation sequence

---

## ⚠️ Safety Reminders

1. **OBSERVATION_MODE = True** means no trades execute
2. **Paper trading** means no real money at risk
3. **Start small** - $5 risk per trade when you go live
4. **Monitor closely** - Check logs daily in Phase 1
5. **Be patient** - 4 weeks of validation is recommended

---

## 🔜 Next Steps

After Phase 1 (4+ weeks):
1. Review all logs and metrics
2. Adjust thresholds if needed
3. Set `OBSERVATION_MODE = False`
4. Continue paper trading with simulated trades
5. After another 2 weeks, consider live deployment
6. Start with minimum capital ($1,000)
7. Scale slowly as confidence builds

**Good luck! 🚀**
