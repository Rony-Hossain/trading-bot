param(
  [ValidateSet("major","minor","patch")] [string]$part = "patch"
)

$versionPath = "VERSION"
if (-not (Test-Path $versionPath)) { throw "VERSION file not found." }
$ver = Get-Content $versionPath | Select-Object -First 1
if ($ver -notmatch '^\d+\.\d+\.\d+$') { throw "VERSION must be SemVer, e.g. 1.2.3" }
$nums = $ver.Split('.') | ForEach-Object { [int]$_ }

switch ($part) {
  "major" { $nums[0] = $nums[0] + 1; $nums[1] = 0; $nums[2] = 0 }
  "minor" { $nums[1] = $nums[1] + 1; $nums[2] = 0 }
  "patch" { $nums[2] = $nums[2] + 1 }
}
$newVer = "$($nums[0]).$($nums[1]).$($nums[2])"
$newVer | Set-Content -Encoding UTF8 $versionPath

git add VERSION
git commit -m "chore(release): bump version to $newVer"
git tag "v$newVer"
git push
git push --tags

Write-Host "Bumped to $newVer and pushed tag v$newVer."
