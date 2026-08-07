$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

$AdminJs = "frontend\admin\admin.js"
if (-not (Test-Path $AdminJs)) {
  throw "Could not find $AdminJs. Extract this package into the FarmLink repository root."
}

$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$Backup = "frontend\admin\admin.js.before-agristart-trigger-fix-$Stamp.bak"
Copy-Item $AdminJs $Backup -Force

$Utf8 = New-Object System.Text.UTF8Encoding($false)
$Path = (Resolve-Path $AdminJs)
$Content = [IO.File]::ReadAllText($Path)

if ($Content.Contains("FARMLINK_AGRISTART_TRIGGER_FIX_V1")) {
  Write-Host "AgriStart trigger fix is already installed." -ForegroundColor Yellow
  exit 0
}

$Pattern = '\[\s*[''"]farmers[''"]\s*,\s*[''"]buyers[''"]\s*,\s*[''"]orders[''"]\s*,\s*[''"]memberships[''"]\s*\]\.includes\((?<argument>[^)]+)\)'
$Matches = [regex]::Matches($Content, $Pattern)

if ($Matches.Count -eq 0) {
  Copy-Item $Backup $AdminJs -Force
  throw "Could not find the admin resource-loading condition. Original admin.js restored."
}

$Content = [regex]::Replace(
  $Content,
  $Pattern,
  "['farmers','buyers','orders','memberships','entrepreneurs'].includes(`${argument})"
)

$Marker = @'

/* FARMLINK_AGRISTART_TRIGGER_FIX_V1
   Adds the entrepreneurs resource to the existing admin data-loading path. */
'@

$Content += $Marker
[IO.File]::WriteAllText($Path, $Content, $Utf8)

if (Get-Command node -ErrorAction SilentlyContinue) {
  node --check $AdminJs
  if ($LASTEXITCODE -ne 0) {
    Copy-Item $Backup $AdminJs -Force
    throw "JavaScript validation failed. Original admin.js restored."
  }
}

$Updated = [IO.File]::ReadAllText($Path)
if (-not $Updated.Contains("'entrepreneurs'].includes(")) {
  Copy-Item $Backup $AdminJs -Force
  throw "The entrepreneurs resource was not added to the loading condition."
}

foreach ($codepoint in @(0x00E2,0x00C2,0x00C3,0x251C,0x0393,0x252C)) {
  if ($Updated.Contains([string][char]$codepoint)) {
    Copy-Item $Backup $AdminJs -Force
    throw "Encoding validation failed. Original admin.js restored."
  }
}

Write-Host ""
Write-Host "FarmLink AgriStart admin trigger fixed successfully." -ForegroundColor Green
Write-Host "Backup: $Backup"
Write-Host ""
Write-Host "Deploy with:"
Write-Host "  git diff --check"
Write-Host "  node --check frontend\admin\admin.js"
Write-Host "  git add frontend\admin\admin.js"
Write-Host '  git commit -m "Load AgriStart applications in admin centre"'
Write-Host "  git push origin main"
