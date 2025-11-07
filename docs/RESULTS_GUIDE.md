# 📊 Backtest & Paper Trading Results Guide

Complete guide to accessing and analyzing your backtest and paper trading logs.

---

## 🎯 What Gets Logged

### **Backtest Mode**
✅ All extreme detections  
✅ HMM regime changes  
✅ A-VWAP tracking  
✅ Would-be trades (observation mode)  
✅ Actual trades (when enabled)  
✅ Performance snapshots  
✅ Errors with stack traces  
✅ **Final backtest summary**  

### **Paper Trading Mode**
✅ Everything from backtest  
✅ **Real-time execution** (simulated fills)  
✅ **Live market conditions**  
✅ **Actual spread data**  
✅ **Circuit breaker triggers**  
✅ **Daily exported logs**  

---

## 📈 Backtest Results Location

### **Option 1: QuantConnect UI**
After backtest completes:
1. Click **"Logs"** tab
2. Scroll to bottom for summary
3. See all detections, errors, etc.

### **Option 2: ObjectStore (Retrievable)**
Automatically saved with keys:
```
final_results_[session_id]       ← Complete backtest summary
logs_all_[session_id]_[date]     ← Daily logs
```

### **Option 3: QuantConnect Charts/Stats**
Standard QC metrics:
- Total Return
- Sharpe Ratio
- Max Drawdown
- Win Rate
- All trades

---

## 📊 What the Backtest Summary Contains

At end of backtest, you get:

### **Portfolio Stats:**
```json
{
  "start_date": "2024-01-01",
  "end_date": "2024-11-06",
  "initial_capital": 1000,
  "final_portfolio_value": 1045.50,
  "total_profit": 45.50,
  "total_return_pct": 4.55,
  "total_fees": 2.30
}
```

### **Detection Stats:**
```json
{
  "total": 487,
  "up": 245,
  "down": 242,
  "avg_z_score": 2.34,
  "avg_vol_anomaly": 1.82
}
```

### **Trade Stats** (if enabled):
```json
{
  "total": 45,
  "entries": 23,
  "exits": 22,
  "win_rate": 0.52,
  "avg_profit": 2.15
}
```

### **Error Stats:**
```json
{
  "total": 5,
  "by_component": {
    "ExtremeDetector": 3,
    "RiskMonitor": 2
  }
}
```

---

## 🔍 How to Retrieve Backtest Results

### **Method 1: During Backtest (UI)**
Just watch the logs tab in real-time!

### **Method 2: After Backtest (Notebook)**

```python
from log_retrieval import LogRetriever
import json

qb = QuantBook()
retriever = LogRetriever(qb)

# List all available results
keys = qb.ObjectStore.GetKeys()
result_keys = [k for k in keys if k.startswith('final_results_')]
print(f"Found {len(result_keys)} backtest results")

# Get most recent
latest_key = result_keys[-1]
results_json = qb.ObjectStore.Read(latest_key)
results = json.loads(results_json)

# Print summary
print("\n" + "="*60)
print("BACKTEST RESULTS SUMMARY")
print("="*60)
print(f"Session: {results['session_id']}")
print(f"Period: {results['portfolio']['start_date']} to {results['portfolio']['end_date']}")
print(f"\nPortfolio:")
print(f"  Initial: ${results['portfolio']['initial_capital']:,.2f}")
print(f"  Final: ${results['portfolio']['final_portfolio_value']:,.2f}")
print(f"  P&L: ${results['portfolio']['total_profit']:,.2f}")
print(f"  Return: {results['portfolio']['total_return_pct']:+.2f}%")
print(f"\nDetections:")
print(f"  Total: {results['detections']['total']}")
print(f"  Up: {results['detections']['up']}")
print(f"  Down: {results['detections']['down']}")
print(f"\nRisk:")
print(f"  Max Drawdown: {results['max_drawdown']:.2%}")
```

### **Method 3: Get Daily Logs from Backtest**

```python
# Get logs for specific date during backtest
logs = retriever.get_logs('2024-05-15')

# Analyze that day
retriever.analyze_logs(logs)

# Export to CSV
retriever.export_to_csv(logs, 'backtest_2024_05_15')
```

---

## 📝 Paper Trading Results

### **Real-Time (Live Console)**
While paper trading:
1. Go to **"Live Trading"** tab
2. Click your algorithm
3. See **real-time logs**
4. Watch detections as they happen

### **Daily Exports**
Every day at market close:
```
logs_all_[session_id]_[YYYYMMDD]
```

Retrieve anytime:
```python
# Get today's paper trading logs
logs = retriever.get_logs('2024-11-06')

# See what happened
retriever.analyze_logs(logs)

# Export for review
retriever.export_to_csv(logs, 'paper_2024_11_06')
```

---

## 📊 Example: Backtest End Summary

```
============================================================
ALGORITHM COMPLETE
============================================================

Portfolio Summary:
  Period: 2024-01-01 to 2024-11-06
  Initial Capital: $1,000.00
  Final Value: $1,045.50
  Total P&L: $45.50
  Total Return: +4.55%
  Total Fees: $2.30

============================================================
EXTREME DETECTION SUMMARY
============================================================
Total Extremes: 487
  Up: 245
  Down: 242
Average |Z-score|: 2.34
Average Vol Anomaly: 1.82x

Recent Detections:
----------------------------------------
  [2024-11-05 10:00] AAPL   | Z=+2.45 | Vol=2.1x |   up
  [2024-11-05 11:30] MSFT   | Z=-2.12 | Vol=1.8x | down
  [2024-11-06 10:15] GOOGL  | Z=+2.33 | Vol=1.6x |   up
  ...

============================================================
TRADE SUMMARY (Observation Mode - No Trades Executed)
============================================================
Would have considered: 487 signals
Extremes detected: 487
A-VWAP tracks created: 156

Risk Metrics:
  Max Drawdown: 0.00% (observation mode)

Final results saved to ObjectStore: final_results_20241106_093000
All logs exported successfully
Session 20241106_093000 complete
============================================================
```

---

## 🔄 Comparing Multiple Backtests

```python
# Get results from multiple backtests
backtest1 = json.loads(qb.ObjectStore.Read('final_results_session1'))
backtest2 = json.loads(qb.ObjectStore.Read('final_results_session2'))

# Compare
print(f"Backtest 1 Return: {backtest1['portfolio']['total_return_pct']:.2f}%")
print(f"Backtest 2 Return: {backtest2['portfolio']['total_return_pct']:.2f}%")

print(f"Backtest 1 Detections: {backtest1['detections']['total']}")
print(f"Backtest 2 Detections: {backtest2['detections']['total']}")

print(f"Backtest 1 Max DD: {backtest1['max_drawdown']:.2%}")
print(f"Backtest 2 Max DD: {backtest2['max_drawdown']:.2%}")
```

---

## 📤 Sharing Backtest Results

### **Quick Share (JSON):**
```python
# Get final results
results = json.loads(qb.ObjectStore.Read('final_results_20241106_093000'))

# Print formatted
print(json.dumps(results, indent=2))

# Copy and share
```

### **Detailed Share (with all logs):**
```python
# Get complete logs for date range
logs = retriever.get_date_range_logs('2024-01-01', '2024-11-06')

# Export everything
retriever.export_to_csv(logs, 'full_backtest')

# Share CSV files:
# - full_backtest_detections.csv (487 rows)
# - full_backtest_errors.csv (if any)
# - full_backtest_performance.csv (daily snapshots)
```

### **Summary Share (for quick review):**
```python
# Get final results
results = json.loads(qb.ObjectStore.Read('final_results_20241106_093000'))

# Create summary
summary = f"""
BACKTEST RESULTS
Period: {results['portfolio']['start_date']} to {results['portfolio']['end_date']}
Return: {results['portfolio']['total_return_pct']:+.2f}%
Detections: {results['detections']['total']}
Max DD: {results['max_drawdown']:.2%}
Errors: {results['errors']['total']}
"""

print(summary)
# Copy and share
```

---

## 🎯 Key Questions to Answer from Logs

### **1. Did the backtest work?**
```python
# Check for errors
if results['errors']['total'] > 0:
    print("⚠️ Errors occurred!")
    # Get error details from logs
else:
    print("✅ Clean run")
```

### **2. How many signals detected?**
```python
print(f"Total extremes: {results['detections']['total']}")
print(f"Average per day: {results['detections']['total'] / 300:.1f}")  # ~300 trading days
```

### **3. What was the performance?**
```python
print(f"Return: {results['portfolio']['total_return_pct']:+.2f}%")
print(f"Max DD: {results['max_drawdown']:.2%}")
print(f"Fees: ${results['portfolio']['total_fees']:.2f}")
```

### **4. Were there any issues?**
```python
# Get error details
logs = retriever.get_logs('2024-05-15')  # Specific date
errors = logs.get('errors', [])

for error in errors:
    print(f"{error['timestamp']}: {error['message']}")
```

### **5. What patterns emerged?**
```python
# Analyze detections
logs = retriever.get_date_range_logs('2024-01-01', '2024-11-06')
det_df = pd.DataFrame(logs['detections'])

# Most detected symbols
print(det_df['symbol'].value_counts().head(10))

# Average Z-scores
print(f"Avg Z-score: {det_df['z_score'].abs().mean():.2f}")

# Direction distribution
print(det_df['direction'].value_counts())
```

---

## 🔔 Paper Trading Specific

### **Daily Monitoring:**
```python
# Check yesterday
yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
logs = retriever.get_logs(yesterday)

# Quick health check
summary = logs.get('summary', {})
print(f"Logs: {summary.get('total_logs', 0)}")
print(f"Errors: {summary.get('total_errors', 0)}")
print(f"Detections: {summary.get('total_detections', 0)}")
```

### **Weekly Review:**
```python
# Get week's logs
logs = retriever.get_date_range_logs('2024-11-01', '2024-11-07')

# Analyze
retriever.analyze_logs(logs)

# Export
retriever.export_to_csv(logs, 'week_1_paper')
```

---

## ✅ Checklist: After Each Backtest

- [ ] Check logs tab for errors
- [ ] Review detection summary
- [ ] Note final portfolio value
- [ ] Check max drawdown
- [ ] Export logs to CSV
- [ ] Save session_id for reference
- [ ] Compare to previous backtests

---

## ✅ Checklist: Daily (Paper Trading)

- [ ] Retrieve yesterday's logs
- [ ] Check error count (should be 0)
- [ ] Review detections (5-10 expected)
- [ ] Monitor portfolio value trend
- [ ] Export to CSV for records
- [ ] Note any unusual behavior

---

## 💡 Pro Tips

1. **Export regularly** - Don't rely only on ObjectStore
2. **Compare backtests** - Track improvement over time
3. **Watch error trends** - Same error repeatedly = fix needed
4. **Monitor detection rate** - Big changes indicate issues
5. **Share context** - When asking for help, include session_id and date range

---

**Your backtest and paper trading results are fully logged and easy to retrieve. Everything is captured, stored, and shareable!** 📊

---

*Last Updated: November 6, 2024*
