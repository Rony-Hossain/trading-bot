param(
  [Parameter(Mandatory=$true)][string]$Bucket,
  [string]$Prefix = "trading-bot"
)

$version = (Get-Content VERSION | Select-Object -First 1).Trim()
$zip = Join-Path "dist" "trading-bot-$version.zip"
if (-not (Test-Path $zip)) { throw "Artifact not found: $zip" }

$dest = "s3://$Bucket/$Prefix/$($version)/trading-bot-$version.zip"
aws s3 cp $zip $dest --only-show-errors
Write-Host "Uploaded to $dest"
