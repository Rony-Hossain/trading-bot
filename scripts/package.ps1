$ErrorActionPreference = "Stop"
$version = (Get-Content VERSION | Select-Object -First 1).Trim()
if (-not $version) { throw "VERSION empty." }

$dist = "dist"
if (-not (Test-Path $dist)) { New-Item -ItemType Directory $dist | Out-Null }

$zip = Join-Path $dist "trading-bot-$version.zip"
if (Test-Path $zip) { Remove-Item $zip -Force }

# Exclude dist/.git/.venv/large files if needed
$exclude = @("dist", ".git", ".venv", ".mypy_cache", ".pytest_cache", "__pycache__", "node_modules")

# Compress-Archive's -Exclude can behave differently across PS versions. Using pattern-based exclude in a clean repo is recommended.
try {
    Compress-Archive -Path * -DestinationPath $zip -Force -CompressionLevel Optimal -ErrorAction Stop
    Write-Host "Packaged $zip"
} catch {
    Write-Warning "Compress-Archive failed; you may use 7z or package from a clean clone. Error: $_"
    throw $_
}
