# Configuration Guide

## Overview

This directory contains the **unified configuration** for the Extreme-Aware Trading Strategy.

## Single Configuration File

**`config.py`** - The only configuration file you need.

All previous config files (`config_phase2.py`, `src/components/config.py`) have been consolidated into this single file to prevent confusion.

## Usage

### Phase 1 (Observation Mode - No Trading)

```python
from config.config import Config

# Create Phase 1 config
config = Config(phase=1)

# Observation mode is automatically enabled
assert config.OBSERVATION_MODE == True
```

### Phase 2 (Live Trading Enabled)

```python
from config.config import Config

# Create Phase 2 config
config = Config(phase=2)

# Trading is enabled, all Phase 2 features active
assert config.OBSERVATION_MODE == False
assert config.ENABLE_EXHAUSTION == True
assert config.ENABLE_PVS == True
assert config.ENABLE_CASCADE_PREVENTION == True
```

## Accessing Configuration Values

The `Config` class supports **both** dictionary-style and attribute-style access:

```python
config = Config(phase=2)

# Dictionary style (used by main algorithm)
risk = config['RISK_PER_TRADE']  # 5.0
max_trades = config['MAX_TRADES_PER_DAY']  # 2

# Attribute style (cleaner, used by components)
risk = config.RISK_PER_TRADE  # 5.0
max_trades = config.MAX_TRADES_PER_DAY  # 2

# Also supports .get() with defaults
spread = config.get('MAX_SPREAD_BPS', 30)  # 35
```

## Configuration Sections

### Mode Control
- `OBSERVATION_MODE` - Auto-set based on phase (True for Phase 1, False for Phase 2)

### Basic Settings
- `INITIAL_CAPITAL` - Starting capital ($1,000)
- `RISK_PER_TRADE` - Base position size ($5)
- `MAX_POSITIONS` - Max concurrent positions (1)
- `MAX_TRADES_PER_DAY` - Daily trade limit (2)

### Universe Selection
- `UNIVERSE_SIZE` - Number of stocks to track (1,000)
- `MIN_PRICE` / `MAX_PRICE` - Price range ($5 - $350)
- `MIN_DOLLAR_VOLUME` - Minimum daily volume ($20M)
- `BLACKLIST` - Symbols to exclude

### Extreme Detection
- `Z_THRESHOLD` - Z-score threshold (2.0)
- `VOLUME_ANOMALY_NORMAL` - Volume multiplier (1.5x)
- `LOOKBACK_MINUTES` - Lookback window (60 min)

### Phase 2 Features (Auto-enabled in Phase 2)
- `ENABLE_EXHAUSTION` - Exhaustion/fade detection
- `ENABLE_PVS` - Psychological Volatility Score
- `ENABLE_CASCADE_PREVENTION` - Multi-violation blocking
- `ENABLE_DYNAMIC_SIZING` - Kelly-inspired sizing
- `ENABLE_ENTRY_TIMING` - Entry timing protocol
- `ENFORCE_DRAWDOWN_LADDER` - Progressive size reduction
- `ENFORCE_SECTOR_NEUTRALITY` - Portfolio constraints

### Cascade Prevention
Nested dictionary with thresholds:
```python
config.CASCADE_PREVENTION = {
    'MIN_EDGE_THRESHOLD': 2.0,
    'CASCADE_THRESHOLD': 2,
    'MAX_CONSECUTIVE_LOSSES': 2,
    'PVS_THRESHOLD': 7,
    'MAX_TRADES_PER_HOUR': 3,
    'MIN_REGIME_CONFIDENCE': 0.5
}

# Access nested values
min_edge = config.CASCADE_PREVENTION['MIN_EDGE_THRESHOLD']
```

## Helper Functions

### GetTimeOfDayMultiplier(hour, minute)
Returns position size multiplier based on time of day:
- First 30 min (9:30-10:00): 0.7x
- Morning (10:00-11:30): 1.0x
- Lunch (11:30-13:00): 0.8x
- Afternoon (13:00-15:30): 1.0x
- Last 30 min (15:30-16:00): 0.6x
- Outside hours: 0.5x

### IsAuctionPeriod(time)
Returns `True` if in auction period (first/last 30 minutes).

### GetPhaseDescription()
Returns human-readable phase description.

## Modifying Configuration

To change settings, you have two options:

### Option 1: Edit config.py directly
```python
# In config.py, change the default value
self.RISK_PER_TRADE = 10.0  # Was 5.0
```

### Option 2: Override after creation
```python
config = Config(phase=2)
config['RISK_PER_TRADE'] = 10.0  # Override for this instance
```

## Migration Notes

**Old files removed:**
- `config/config_phase2.py` ❌ (consolidated)
- `src/components/config.py` ❌ (consolidated)

**New unified file:**
- `config/config.py` ✅ (single source of truth)

All previous settings have been preserved and merged into the new unified config.
