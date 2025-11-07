$ErrorActionPreference = "Stop"
$version = (Get-Content VERSION | Select-Object -First 1).Trim()

Write-Host "Deploying trading-bot version $version to QuantConnect..."
# If you already have deploy_to_qc.bat/.sh, call it here. Example:
# & .\deploy_to_qc.bat
# Or: bash ./deploy_to_qc.sh

# If your deploy script accepts args, pass the artifact path:
# & .\deploy_to_qc.bat "dist\trading-bot-$version.zip"

Write-Host "Deployment call issued for version $version."
