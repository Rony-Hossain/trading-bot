#!/bin/bash

# Deploy to QuantConnect Script (v2)
# This script now uses the new Python-based CLI for building.

set -e

echo "================================================"
echo "  Deploying to QuantConnect Format (via CLI)"
echo "================================================"
echo ""

# Run the Python CLI build command with --force to overwrite
echo "Running Python build script..."
python3 -m tools.deploy_cli build --force

# List what was created
echo ""
echo "✅ Deployment package created in quantconnect/"
echo ""
echo "📋 Files ready for upload:"
ls -1 quantconnect/*.py
ls -1 quantconnect/*.md
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
