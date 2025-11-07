# 🎯 Extreme-Aware Trading Strategy

**Phase 1 Implementation** for QuantConnect + Interactive Brokers

A regime-adaptive, extreme-aware trading system for US equities. Phase 1 focuses on observation and validation before live trading.

---

## 🚀 Quick Start

### 1️⃣ Read Documentation
Start here: **[docs/START_HERE.md](docs/START_HERE.md)**

### 2️⃣ Prepare for Deployment
Follow: **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)**

### 3️⃣ Deploy to QuantConnect
```bash
# Flatten files for QuantConnect upload
./deploy_to_qc.sh

# Then upload from quantconnect/ folder
```

---

## 📊 What Is This?

A **medium-frequency trading strategy** that:
- ✅ Detects price extremes (|Z₆₀| ≥ 2 + volume anomaly)
- ✅ Classifies market regimes (Low-Vol/High-Vol/Trending)
- ✅ Tracks anchored VWAP from impulses
- ✅ Manages risk with multiple safety layers
- ✅ **Phase 1: Observation Mode** - No trades, just monitoring

---

## 📁 Project Structure

```
extreme-aware-strategy/
├── src/                    # Source code
│   ├── main.py            # Main algorithm
│   └── components/        # Trading components
├── config/                # Configuration
├── docs/                  # Documentation
├── tests/                 # Unit tests
├── backtest_results/      # Backtest outputs
├── logs/                  # Runtime logs
└── quantconnect/         # Flattened for QC upload
```

**Detailed breakdown:** [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)

---

## 🎓 Key Features (Phase 1)

### Universe Selection
- ~1,000 most liquid US stocks
- Price range: $5-$350
- Min daily volume: $20M
- NYSE/NASDAQ common shares

### Extreme Detection
- **Z-score:** 60-min return ≥ 2 standard deviations
- **Volume anomaly:** ≥ 1.5x median (2x during auctions)
- **Cooldown:** 15-minute detection spacing
- **Result:** ~5-10 extremes detected per day

### HMM Regime (Simplified)
- **3 states:** Low-Vol, High-Vol, Trending
- **VIX-based** classification
- **GPM:** Global Position Multiplier for sizing
- **Ready** for full Gaussian HMM in Phase 2

### A-VWAP Tracking
- **Anchored** from impulse bars
- **Distance** monitoring
- **Time stops:** 5 hours
- **Multi-symbol** tracking

### Risk Management
- **Circuit breakers** monitored
- **Daily summaries** generated
- **Drawdown** tracking
- **Phase 1:** Observe only, no enforcement

---

## ⚙️ Configuration

Edit `config/config.py`:

```python
# Detection
Z_THRESHOLD = 2.0
VOLUME_ANOMALY_NORMAL = 1.5

# Capital (Phase 1)
INITIAL_CAPITAL = 1000
RISK_PER_TRADE = 5
MAX_POSITIONS = 1
MAX_TRADES_PER_DAY = 2
```

---

## 🔐 Safety Features

### Phase 1 Protections:
- 🔒 **OBSERVATION_MODE = True** (no trades execute)
- 🔒 **Paper trading only** (no real money)
- 🔒 **Conservative parameters** ($5 risk per trade)
- 🔒 **Single position** at a time
- 🔒 **Comprehensive logging** for analysis

---

## 📈 Expected Behavior

### Daily Activity:
- **Extremes detected:** 5-10 per day
- **A-VWAP tracks:** 3-8 active
- **Regime switches:** 1-3 per week
- **Log entries:** Extensive

### Log Example:
```
🚨 EXTREME DETECTED: AAPL
   Z-score: 2.45
   Volume Anomaly: 2.1x
   Direction: up
   60m Return: +1.23%

A-VWAP: Started tracking AAPL from $175.23
AAPL A-VWAP Distance: +0.85%

📊 OBSERVATION MODE - Would consider 3 candidates
```

---

## 📅 Implementation Timeline

### ✅ Week 1-2: Initial Observation
- Deploy to paper trading
- Monitor extreme detection
- Verify HMM regime switches
- Track A-VWAP behavior
- Build confidence

### ✅ Week 3-4: Validation
- Review all signals
- Check for false positives
- Confirm system stability
- Analyze metrics

### 🔜 Week 5+: Enable Trading (Still Paper)
- Set `OBSERVATION_MODE = False`
- Monitor simulated trades
- Validate position sizing
- Continue paper trading

### 🔜 Week 8+: Consider Live (Cautiously)
- After thorough validation
- Start with $1,000
- $5 risk per trade
- Scale slowly

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [START_HERE.md](docs/START_HERE.md) | 👈 **Start here!** Quick overview |
| [DEPLOYMENT.md](docs/DEPLOYMENT.md) | Step-by-step QuantConnect setup |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design & data flow |
| [CHECKLIST.md](docs/CHECKLIST.md) | Weekly progress tracking |
| [README.md](docs/README.md) | Full usage guide |
| [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) | File organization |

---

## 🛠️ Tech Stack

- **Platform:** QuantConnect (LEAN Engine)
- **Language:** Python 3.11
- **Broker:** Interactive Brokers
- **Data:** Minute bars + fundamentals
- **Capital:** $1,000 starting (Phase 1)

---

## ⚠️ Important Reminders

1. **Start in OBSERVATION MODE** - No money at risk
2. **Paper trade first** - 4+ weeks minimum
3. **Review daily logs** - Understand every signal
4. **Stay disciplined** - Don't skip validation
5. **Start small** - $5 risk per trade when live
6. **Scale slowly** - Build confidence gradually

---

## 🎯 Success Criteria (Phase 1)

Before considering live trading:
- ✅ Runs 4+ weeks without errors
- ✅ 5-10 extremes detected daily
- ✅ HMM classifications sensible
- ✅ A-VWAP tracking correct
- ✅ No data quality issues
- ✅ IBKR connection stable
- ✅ You understand all signals

---

## 🔜 Future Phases

### Phase 2 (Week 5-8):
- Drawdown ladder enforcement
- PVS psychological governor
- Exhaustion signals
- Sector neutrality

### Phase 3 (Week 9-12):
- Options data integration (GEX, IV, skew)
- Options as features (not positions)
- Enhanced risk management

### Phase 4 (Week 13+):
- Full system active
- Consider tiny options positions
- Scale capital gradually
- Meta-fitness tracking

---

## 📞 Support

- **QuantConnect Docs:** https://www.quantconnect.com/docs
- **IBKR API:** https://www.interactivebrokers.com/en/software/api/
- **Strategy Document:** Review your original spec
- **Community:** QuantConnect forums

---

## 📊 Performance Targets

**Phase 1 Goals (Observation):**
- Detect extremes reliably
- Classify regimes accurately
- Track A-VWAP correctly
- Build system confidence

**Live Goals (Future):**
- IR ≥ 0.7 (post-cost)
- Max DD ≤ 15%
- VaR utilization ≤ 80%
- Slippage ≤ model + 20%

---

## 🎓 Key Concepts

- **Extreme:** 60-min move ≥ 2σ with volume confirmation
- **Z-score:** Standardized return (return / volatility)
- **Volume Anomaly:** Current hour volume / 20-day median
- **A-VWAP:** Anchored VWAP from impulse bar
- **HMM:** Hidden Markov Model for regime classification
- **GPM:** Global Position Multiplier (regime-based sizing)

---

## ✨ You're Ready!

1. **Read** [docs/START_HERE.md](docs/START_HERE.md)
2. **Deploy** using [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
3. **Monitor** logs daily
4. **Track** progress in [docs/CHECKLIST.md](docs/CHECKLIST.md)
5. **Scale** gradually after validation

**Good luck! 🚀**

---

*Phase 1 Implementation - November 6, 2024*  
*For $1,000 starting capital, observation mode first*  
*QuantConnect + Interactive Brokers*

## Safety Checklist (quick runbook)
- `OBSERVATION_MODE` = **True** unless you explicitly want live orders.
- `REQUIRE_CONFIRM` = **true** (asks before placing any order).
- `MAX_DAILY_LOSS` = 1% NAV (halts trading for the day if breached).
- `MAX_TRADES_PER_DAY` = 2 (prevents overtrading).
- Use `.env` for secrets (never commit it). See `.env.example`.

## Safety Checklist (quick runbook)
- `OBSERVATION_MODE` = **True** unless you explicitly want live orders.
- `REQUIRE_CONFIRM` = **true** (asks before placing any order).
- `MAX_DAILY_LOSS` = 1% NAV (halts trading for the day if breached).
- `MAX_TRADES_PER_DAY` = 2 (prevents overtrading).
- Use `.env` for secrets (never commit it). See `.env.example`.

## Safety Checklist (quick runbook)
- `OBSERVATION_MODE` = **True** unless you explicitly want live orders.
- `REQUIRE_CONFIRM` = **true** (asks before placing any order).
- `MAX_DAILY_LOSS` = 1% NAV (halts trading for the day if breached).
- `MAX_TRADES_PER_DAY` = 2 (prevents overtrading).
- Use `.env` for secrets (never commit it). See `.env.example`.
