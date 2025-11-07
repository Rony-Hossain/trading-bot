# 📝 Logging System Guide

Complete guide to the **advanced logging system** for monitoring, debugging, and sharing logs.

---

## 🎯 Overview

The logging system provides:
- ✅ **Multiple log levels** (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- ✅ **Structured JSON logs** for analysis
- ✅ **Specialized loggers** for trades, detections, performance
- ✅ **Automatic export** to ObjectStore
- ✅ **Easy sharing** - export logs to analyze/share
- ✅ **Error tracing** with full stack traces
- ✅ **Daily summaries** and reports

---

## 📊 What Gets Logged

### 1. **General Logs** (INFO level)
- Algorithm initialization
- Hourly checks
- Component updates
- Daily summaries

### 2. **Extreme Detections**
Every extreme detected gets logged with:
- Symbol
- Z-score
- Volume anomaly
- Direction (up/down)
- 60-minute return
- Timestamp

### 3. **Trade Executions** (when enabled)
Every trade logged with:
- Trade type (entry/exit/hedge)
- Symbol
- Quantity
- Price
- Reason for trade
- Portfolio value after

### 4. **Regime Changes**
HMM regime switches logged with:
- Old regime → New regime
- State probabilities
- GPM (Global Position Multiplier)

### 5. **Circuit Breakers**
Any breaker activation logged with:
- Breaker type
- Reason triggered
- Action taken

### 6. **Performance Snapshots**
Periodic captures of:
- Total portfolio value
- Cash balance
- Holdings value
- Unrealized P&L
- Position count

### 7. **A-VWAP Tracking**
Updates for each tracked symbol:
- Current VWAP
- Distance from price
- Bars since impulse

### 8. **Risk Metrics**
Regular captures of:
- Drawdown level
- VaR utilization
- Portfolio beta
- PVS score

### 9. **Errors & Exceptions**
Full error tracking with:
- Error message
- Component that failed
- Exception type
- Full stack trace
- Context data

---

## 🎨 Log Levels

```python
DEBUG    # Detailed tracing (disabled by default)
INFO     # Normal operations (default level)
WARNING  # Potential issues
ERROR    # Something went wrong
CRITICAL # System failure
```

**Change level:**
```python
# In main.py
self.logger.set_log_level('DEBUG')  # More verbose
self.logger.set_log_level('WARNING')  # Less verbose
```

---

## 📥 Accessing Logs

### Method 1: Real-Time (QuantConnect UI)
- Go to your algorithm in QC
- Click "Logs" tab
- See real-time log output
- Scroll through history

### Method 2: Daily Export (ObjectStore)
Logs are automatically exported daily to ObjectStore with key format:
```
logs_all_[session_id]_[YYYYMMDD]
```

**Retrieve in Research Notebook:**
```python
from log_retrieval import LogRetriever

qb = QuantBook()
retriever = LogRetriever(qb)

# List available
retriever.list_available_logs()

# Get specific date
logs = retriever.get_logs('2024-11-06')

# Analyze
retriever.analyze_logs(logs)
```

### Method 3: Export to CSV/JSON
```python
# In notebook
retriever.export_to_csv(logs, 'my_logs')

# Creates:
# - my_logs_detections.csv
# - my_logs_trades.csv
# - my_logs_errors.csv
# - my_logs_performance.csv
```

---

## 📤 Sharing Logs

### Quick Share (for support/review):

**Option A: Export JSON**
```python
# In QuantConnect notebook
logs = retriever.get_logs('2024-11-06')
json_str = json.dumps(logs, indent=2)

# Copy to clipboard or save to file
with open('logs_to_share.json', 'w') as f:
    f.write(json_str)
```

**Option B: Generate Summary Report**
```python
logs = retriever.get_logs('2024-11-06')
retriever.analyze_logs(logs)

# Copy the printed report
```

**Option C: Get Specific Log Type**
```python
# Just errors
error_logs = retriever.get_logs('2024-11-06', 'errors')

# Just trades
trade_logs = retriever.get_logs('2024-11-06', 'trades')

# Just detections
detection_logs = retriever.get_logs('2024-11-06', 'detections')
```

### Share via CSV (for Excel/analysis):
```python
logs = retriever.get_logs('2024-11-06')
retriever.export_to_csv(logs, 'share_2024_11_06')

# Email or share the CSV files
```

---

## 🔍 Log Examples

### Startup Logs:
```
[2024-11-06 09:30:00] [INFO    ] [Main] ============================================================
[2024-11-06 09:30:00] [INFO    ] [Main] EXTREME-AWARE TRADING STRATEGY - PHASE 1
[2024-11-06 09:30:00] [INFO    ] [Main] ============================================================
[2024-11-06 09:30:01] [INFO    ] [Main] Phase 1 Observation Mode - Initialized
[2024-11-06 09:30:01] [INFO    ] [Main] Capital: $1,000.00
[2024-11-06 09:30:01] [INFO    ] [Main] Observation Mode: True
[2024-11-06 09:30:01] [INFO    ] [Main] Max Positions: 1
[2024-11-06 09:30:01] [INFO    ] [Main] Risk/Trade: $5
```

### Extreme Detection:
```
[2024-11-06 10:00:00] [INFO    ] [ExtremeDetector] 🚨 EXTREME: AAPL | Z=+2.45 | VolAnom=2.1x | Dir=up | Ret=+1.23%
[2024-11-06 10:00:00] [INFO    ] [AVWAPTracker] A-VWAP: Started tracking AAPL from $175.23 (up extreme, Z=2.45)
```

### Performance Snapshot:
```
[2024-11-06 16:00:00] [INFO    ] [Logger] Performance snapshot captured
```

### Error Example:
```
[2024-11-06 11:30:00] [ERROR   ] [ExtremeDetector] ❌ Failed to calculate Z-score for TSLA
    Exception: ZeroDivisionError: division by zero
    [Full stack trace included]
```

### Daily Close:
```
[2024-11-06 16:00:00] [INFO    ] [Main] ============================================================
[2024-11-06 16:00:00] [INFO    ] [Main] Market Close: 2024-11-06
[2024-11-06 16:00:00] [INFO    ] [Main] Daily Summary:
[2024-11-06 16:00:00] [INFO    ] [Main]   Extremes Detected: 12
[2024-11-06 16:00:00] [INFO    ] [Main]   HMM Regime: Low-Vol
[2024-11-06 16:00:00] [INFO    ] [Main]   Active A-VWAP Tracks: 3
[2024-11-06 16:00:00] [INFO    ] [Main]   💡 OBSERVATION MODE - No trades executed
[2024-11-06 16:00:00] [INFO    ] [Logger] Log Summary: 245 logs, 2 errors, 12 detections
[2024-11-06 16:00:00] [INFO    ] [Main] Daily logs exported to ObjectStore
```

---

## 📋 Specialized Reports

### Detection Summary:
```python
# At market close, automatically printed:

============================================================
EXTREME DETECTION SUMMARY
============================================================

Total Extremes: 12

  Up: 7
  Down: 5

Average |Z-score|: 2.34
Average Vol Anomaly: 1.82x

Recent Detections:
----------------------------------------
  [10:00] AAPL   | Z=+2.45 | Vol=2.1x |   up
  [10:30] MSFT   | Z=-2.12 | Vol=1.8x | down
  [11:00] GOOGL  | Z=+2.33 | Vol=1.6x |   up
  ...
```

### Error Report (if errors occurred):
```python
============================================================
ERROR REPORT
============================================================

ExtremeDetector (2 errors):
----------------------------------------
  [11:30:00] Failed to calculate Z-score for TSLA
    ZeroDivisionError: division by zero
  [14:15:00] Invalid bar data for NVDA
    ValueError: Empty array

RiskMonitor (1 errors):
----------------------------------------
  [15:00:00] Failed to calculate drawdown
    KeyError: 'total_value'
```

### Trade Summary (when trades executed):
```python
============================================================
TRADE SUMMARY
============================================================

Total Trades: 5
  Entries: 2
  Exits: 2
  Hedges: 1

Recent Trades:
----------------------------------------
  [10:15:00] ENTRY +100 AAPL @ $175.50
    Reason: Continuation signal after extreme
  [10:45:00] HEDGE -10 SPY @ $450.25
    Reason: Beta neutrality
  ...
```

---

## 🛠️ Troubleshooting

### No logs appearing in ObjectStore:
```python
# Check if ObjectStore is enabled in your QC account
# Try manual export in OnMarketClose:
try:
    self.logger.export_logs_json('all')
except Exception as e:
    self.Log(f"Export failed: {e}")
```

### Too many logs (performance impact):
```python
# Reduce log level
self.logger.set_log_level('WARNING')

# Or disable debug logs
self.logger.set_log_level('INFO')
```

### Can't retrieve logs in notebook:
```python
# Verify the key format
retriever.list_available_logs()

# Try different date format
logs = retriever.get_logs('20241106')  # YYYYMMDD format
```

### Logs too large:
```python
# Get only specific type
errors_only = retriever.get_logs('2024-11-06', 'errors')
trades_only = retriever.get_logs('2024-11-06', 'trades')

# Or clear old logs periodically (careful!)
self.logger.clear_logs()  # Clears in-memory buffers
```

---

## 📊 Log Analysis Tips

### Find all errors for a symbol:
```python
logs = retriever.get_logs('2024-11-06')
for error in logs['errors']:
    if 'AAPL' in error.get('message', ''):
        print(error)
```

### Track performance over time:
```python
logs = retriever.get_date_range_logs('2024-11-01', '2024-11-06')
perf_df = pd.DataFrame(logs['performance'])
perf_df.plot(x='timestamp', y='total_value')
```

### Analyze detection patterns:
```python
det_df = pd.DataFrame(logs['detections'])
print(det_df['direction'].value_counts())
print(det_df.groupby('symbol').size().sort_values(ascending=False).head(10))
```

### Find most problematic components:
```python
logs = retriever.get_logs('2024-11-06')
for error in logs['errors']:
    print(f"{error['component']}: {error['message']}")
```

---

## 🔐 Best Practices

1. **Keep logs for at least 30 days** - helps with debugging patterns
2. **Export weekly** - download CSVs for external analysis
3. **Review errors daily** - catch issues early
4. **Monitor log counts** - sudden spikes indicate problems
5. **Share context** - when asking for help, include relevant log snippets
6. **Use log levels appropriately** - DEBUG for development, INFO for production
7. **Don't log sensitive data** - avoid logging API keys, credentials

---

## 📝 Quick Reference

### In Your Algorithm:
```python
# Info
self.logger.info("Message", component="ComponentName")

# Warning
self.logger.warning("Potential issue", component="ComponentName")

# Error with exception
try:
    # code
except Exception as e:
    self.logger.error("Failed", component="ComponentName", exception=e)

# Specialized logs
self.logger.log_extreme_detection(symbol, extreme_info)
self.logger.log_trade('entry', symbol, 100, 175.50, "Signal")
self.logger.log_regime_change('Low-Vol', 'High-Vol', regime_data)
```

### In Research Notebook:
```python
from log_retrieval import LogRetriever

retriever = LogRetriever(qb)
logs = retriever.get_logs('2024-11-06')
retriever.analyze_logs(logs)
retriever.export_to_csv(logs, 'logs')
```

---

**The logging system is comprehensive and production-ready. Use it to monitor, debug, and share your trading system's behavior!** 📊

---

*Last Updated: November 6, 2024*
