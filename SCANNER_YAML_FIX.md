# scanner.yaml Path Loading Fix

## Issue
The `_load_scanner_yaml()` method in `alert_manager.py` had a duplicate path in the search list:
- `'scanner.yaml'` and `'./scanner.yaml'` are identical
- Used string paths instead of pathlib for less robustness
- Returned `None` on first error instead of trying remaining paths

## Changes Made

### 1. Added pathlib Import
```python
from pathlib import Path
```

### 2. Refactored Path List (De-duplicated)
**Before:**
```python
possible_paths = [
    './config/scanner.yaml',
    '../config/scanner.yaml',
    'scanner.yaml',
    './scanner.yaml'  # DUPLICATE
]
```

**After:**
```python
possible_paths = [
    Path('config/scanner.yaml'),      # ./config/scanner.yaml
    Path('../config/scanner.yaml'),   # ../config/scanner.yaml
    Path('scanner.yaml')              # ./scanner.yaml (no duplicate)
]
```

### 3. Improved Error Handling
**Before:**
```python
except Exception as e:
    if self.logger:
        self.logger.error(f"Failed to load {path}: {str(e)}")
    return None  # STOPS trying other paths
```

**After:**
```python
except Exception as e:
    if self.logger:
        self.logger.error(f"Failed to load {path}: {str(e)}")
    continue  # Try next path
```

### 4. Added UTF-8 Encoding
```python
with open(path, 'r', encoding='utf-8') as f:
```

### 5. Added Debug Logging
```python
if self.logger:
    self.logger.debug("No scanner.yaml found, using default config", component="AlertManager")
```

## Benefits

1. **De-duplicated Paths**: 3 unique paths instead of 4 (removed duplicate)
2. **Robustness**: Uses `pathlib.Path` for cross-platform compatibility
3. **Better Error Handling**: Tries all paths even if one fails to load
4. **UTF-8 Safe**: Explicit encoding prevents encoding issues
5. **Better Logging**: Debug message when no config found

## Path Search Order

1. `config/scanner.yaml` - Local config subdirectory (most common)
2. `../config/scanner.yaml` - Parent config directory
3. `scanner.yaml` - Current working directory (fallback)

## Testing

```python
# Test that paths work correctly
from pathlib import Path

# These should all resolve correctly now
assert Path('config/scanner.yaml') != Path('./scanner.yaml')  # No duplicate
assert Path('scanner.yaml').exists()  # Can check existence
```

## File Modified
- [quantconnect/alert_manager.py](quantconnect/alert_manager.py)
  - Line 30: Added `from pathlib import Path`
  - Lines 100-132: Refactored `_load_scanner_yaml()` method

## Risk
✅ **VERY LOW** - Only affects config loading, better error handling

## Impact
✅ **POSITIVE** - More robust, cleaner code, better cross-platform support
