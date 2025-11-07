# 🚀 QUICK START GUIDE

**Get running in 10 minutes!**

---

## ⚡ Super Fast Start (3 Steps)

### 1️⃣ Configure Your Strategy

**Choose your configuration** in `src/main.py` line 85:

```python
# Week 1-4: Learn basics
self.config = Config(version=1, trading_enabled=False)

# Week 5-8: Test advanced features (recommended)
self.config = Config(version=2, trading_enabled=False)  # ← START HERE

# Week 9+: Go live
self.config = Config(version=2, trading_enabled=True)
```

**Recommended:** Start with `version=2, trading_enabled=False` to test all features safely!

### 2️⃣ Upload to QuantConnect

1. Go to https://www.quantconnect.com
2. Create new algorithm: "Extreme-Aware-v2"
3. Upload files in this order:
   - **config.py** (from `config/` folder)
   - All component files (from `src/components/`)
   - **main.py** (from `src/` folder) - **UPLOAD LAST!**

### 3️⃣ Run Backtest

1. Click "Backtest" button
2. Wait 2-5 minutes
3. Check initialization logs:
   ```
   EXTREME-AWARE STRATEGY - V2 (ADVANCED) - OBSERVATION
   Version: 2 | Mode: OBSERVATION (no trades)
   ```
4. Review detection logs
5. Deploy to Paper Trading when ready

**Done! 🎉**

---

## 📖 Read These (In Order)

1. **[README.md](README.md)** - Project overview (5 min)
2. **[docs/START_HERE.md](docs/START_HERE.md)** - What Phase 1 does (5 min)
3. **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)** - Detailed setup (15 min)
4. **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** - File organization (5 min)

---

## 🎯 What You're Deploying

A trading system that:
- ✅ Monitors ~1,000 liquid US stocks
- ✅ Detects price extremes hourly
- ✅ Tracks market regime (VIX-based)
- ✅ Calculates anchored VWAP
- ✅ Logs everything (NO TRADES in Phase 1)

---

## ⚙️ Default Settings (Phase 1)

```python
OBSERVATION_MODE = True    # No trades execute
INITIAL_CAPITAL = $1,000
RISK_PER_TRADE = $5
MAX_POSITIONS = 1
```

**These are safe defaults!** Start here.

---

## 📊 What to Expect

### First Hour:
```
Phase 1 Observation Mode - Initialized
Capital: $1000.00
Coarse Filter: 1000 symbols passed
Fine Filter: 850 symbols passed
HMM: Using simplified regime detection
```

### First Detection:
```
🚨 EXTREME DETECTED: AAPL
   Z-score: 2.45
   Volume Anomaly: 2.1x
   Direction: up
   60m Return: +1.23%
```

### Daily Close:
```
📈 Daily Summary:
   Extremes Detected: 12
   HMM Regime: Low-Vol
   Active A-VWAP Tracks: 3
   💡 OBSERVATION MODE - No trades executed
```

---

## ✅ Success Checklist (Week 1)

After 1 week, you should have:
- [ ] Algorithm running without errors
- [ ] 25-50 extremes detected
- [ ] A-VWAP tracks active (3-8 at a time)
- [ ] Regime switches observed
- [ ] Daily summaries generated
- [ ] No data quality issues

**If all checks pass → Continue Phase 1 for 3 more weeks**

---

## 🔄 Weekly Routine

### Monday AM:
- Check weekend summary
- Review regime state
- Verify system health

### Daily:
- Scan logs for extremes
- Note any unusual behavior
- Track in [docs/CHECKLIST.md](docs/CHECKLIST.md)

### Friday PM:
- Generate weekly summary
- Review all detections
- Update checklist
- Decide: continue or adjust?

---

## ⚠️ Common Issues

### "No extremes detected"
**Solution:** Market might be quiet. Wait 2-3 days. If still none, reduce thresholds in `config.py`:
```python
Z_THRESHOLD = 1.5          # Was 2.0
VOLUME_ANOMALY_NORMAL = 1.2  # Was 1.5
```

### "Universe is empty"
**Solution:** Lower filters in `config.py`:
```python
MIN_DOLLAR_VOLUME = 10_000_000  # Was 20M
```

### "IBKR connection failed"
**Solution:** 
1. Check TWS/Gateway is running
2. Verify API settings enabled
3. Use paper trading account
4. Check QuantConnect has correct credentials

---

## 📝 Adjusting Parameters

Edit `config/config.py` to tune:

```python
# More/fewer detections
Z_THRESHOLD = 2.0           # Lower = more detections
VOLUME_ANOMALY_NORMAL = 1.5  # Lower = more detections

# Risk (when trading enabled)
RISK_PER_TRADE = 5           # Dollar risk per trade
MAX_POSITIONS = 1            # Concurrent positions
```

**Important:** After changing config, re-run deployment:
```bash
./deploy_to_qc.sh
# Re-upload config.py to QuantConnect
```

---

## 🎓 Understanding the Logs

### Extreme Detection:
```
🚨 = Price extreme detected
Z-score = How many σ the move is
Volume Anomaly = Current volume / median
Direction = up or down
```

### A-VWAP Tracking:
```
A-VWAP: Started tracking = New impulse detected
Distance: +0.85% = Price is 0.85% above A-VWAP
```

### Regime:
```
HMM Regime: Low-Vol = Market is calm
GPM: 1.0 = Full position sizing (would be, if trading)
```

### Observation Mode:
```
💡 OBSERVATION MODE = Reminder: no trades executing
Would consider X candidates = What we'd trade if enabled
```

---

## 🔜 After 4 Weeks

If everything looks good:

1. **Review** all logs and metrics
2. **Update** `main.py`:
   ```python
   self.OBSERVATION_MODE = False  # Enable trading simulation
   ```
3. **Continue** paper trading with simulated trades
4. **Monitor** for 2 more weeks
5. **Consider** live deployment with $1,000

**Don't rush this!** 4-6 weeks validation is worth it.

---

## 💡 Pro Tips

1. **Journal everything** - Keep notes on unusual behavior
2. **Compare to market** - Do detections align with news?
3. **Trust the process** - 4 weeks seems long but builds confidence
4. **Start conservative** - Better safe than sorry
5. **Scale slowly** - $1k → $5k → $10k over months

---

## 📞 Need Help?

1. **Check docs:** All questions answered in `docs/`
2. **Review logs:** Usually reveals the issue
3. **QuantConnect forums:** Active community
4. **Your strategy doc:** Re-read original spec

---

## ✨ You're Ready!

Everything is set up and documented. Just:
1. Run `./deploy_to_qc.sh`
2. Upload to QuantConnect
3. Monitor for 4 weeks
4. Scale gradually

**Good luck! 🚀**

---

*Last Updated: November 6, 2024*
