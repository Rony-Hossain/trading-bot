#!/bin/bash

# Deploy to QuantConnect Script
# Flattens the organized project structure for QuantConnect upload
# QuantConnect requires all files in the root of the project

set -e

echo "================================================"
echo "  Deploying to QuantConnect Format"
echo "================================================"
echo ""

# Create quantconnect folder
echo "📁 Creating quantconnect/ folder..."
rm -rf quantconnect
mkdir -p quantconnect

# Copy Python files to root (flat structure)
echo "📦 Copying source files..."
cp config/config.py quantconnect/
cp src/components/logger.py quantconnect/
cp src/components/log_retrieval.py quantconnect/
cp src/components/universe_filter.py quantconnect/
cp src/components/extreme_detector.py quantconnect/
cp src/components/hmm_regime.py quantconnect/
cp src/components/avwap_tracker.py quantconnect/
cp src/components/risk_monitor.py quantconnect/
cp src/main.py quantconnect/

# Copy documentation for reference
echo "📄 Copying documentation..."
cp docs/README.md quantconnect/GUIDE.md
cp docs/DEPLOYMENT.md quantconnect/

# Create upload instructions
cat > quantconnect/UPLOAD_ORDER.txt << 'EOF'
# QuantConnect Upload Order

Upload these files to QuantConnect in this exact order:

1. config.py              ← Configuration (no dependencies)
2. logger.py              ← Logging system (no dependencies)
3. log_retrieval.py       ← Log retrieval (for notebooks, optional)
4. universe_filter.py     ← Universe selection
5. extreme_detector.py    ← Extreme detection
6. hmm_regime.py         ← HMM regime classifier
7. avwap_tracker.py      ← A-VWAP tracking
8. risk_monitor.py       ← Risk monitoring
9. main.py               ← Main algorithm (LAST!)

## How to Upload

1. Go to https://www.quantconnect.com
2. Create new algorithm: "Extreme-Aware-Phase1"
3. For each file above:
   - Click "+" in file explorer
   - Select "Upload File"
   - Choose the file
   - Click "Upload"
4. After all files uploaded, click "Backtest"
5. Check logs for errors

## Important

- Upload in ORDER (config.py first, main.py last)
- All files must be in ROOT of QC project (no folders)
- Set OBSERVATION_MODE = True for safety
- Use Paper Trading, not live account

See DEPLOYMENT.md for detailed instructions.
EOF

# List what was created
echo ""
echo "✅ Deployment package created in quantconnect/"
echo ""
echo "📋 Files ready for upload:"
ls -1 quantconnect/*.py

echo ""
echo "================================================"
echo "  Next Steps:"
echo "================================================"
echo ""
echo "1. Review files in quantconnect/ folder"
echo "2. Read UPLOAD_ORDER.txt for instructions"
echo "3. Upload to QuantConnect in specified order"
echo "4. Run backtest to verify"
echo "5. Deploy to paper trading"
echo ""
echo "See docs/DEPLOYMENT.md for detailed guide"
echo ""
