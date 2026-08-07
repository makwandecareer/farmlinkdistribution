$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

$AdminJs = "frontend\admin\admin.js"
if (-not (Test-Path $AdminJs)) {
  throw "Could not find $AdminJs. Extract this package into the repository root."
}

$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$Backup = "frontend\admin\admin.js.before-dom-fix-$Stamp.bak"
Copy-Item $AdminJs $Backup -Force

$Utf8 = New-Object System.Text.UTF8Encoding($false)
$Content = [IO.File]::ReadAllText((Resolve-Path $AdminJs))

$Marker = "FARMLINK_SAFE_INSERT_BEFORE_V1"
$Guard = @'
/* FARMLINK_SAFE_INSERT_BEFORE_V1
   Prevents repeated table-enhancement observers from calling insertBefore
   with a reference node that has already moved to another parent. */
(() => {
  if (window.__farmLinkSafeInsertBeforeInstalled) return;
  window.__farmLinkSafeInsertBeforeInstalled = true;

  const nativeInsertBefore = Node.prototype.insertBefore;
  Node.prototype.insertBefore = function(newNode, referenceNode) {
    if (referenceNode == null) {
      return nativeInsertBefore.call(this, newNode, null);
    }

    if (referenceNode.parentNode !== this) {
      return this.appendChild(newNode);
    }

    return nativeInsertBefore.call(this, newNode, referenceNode);
  };
})();

'@

if (-not $Content.Contains($Marker)) {
  $Content = $Guard + $Content
  [IO.File]::WriteAllText((Resolve-Path $AdminJs), $Content, $Utf8)
}

# Validate ASCII safety of the inserted guard and JavaScript syntax.
if ($Guard.ToCharArray() | Where-Object { [int]$_ -gt 127 }) {
  Copy-Item $Backup $AdminJs -Force
  throw "The DOM guard unexpectedly contains non-ASCII characters."
}

if (Get-Command node -ErrorAction SilentlyContinue) {
  node --check $AdminJs
  if ($LASTEXITCODE -ne 0) {
    Copy-Item $Backup $AdminJs -Force
    throw "JavaScript syntax validation failed. Original admin.js restored."
  }
}

$Updated = [IO.File]::ReadAllText((Resolve-Path $AdminJs))
foreach ($codepoint in @(0x00E2,0x00C2,0x00C3,0x251C,0x0393,0x252C)) {
  if ($Updated.Contains([string][char]$codepoint)) {
    Copy-Item $Backup $AdminJs -Force
    throw "Encoding validation failed. Original admin.js restored."
  }
}

Write-Host ""
Write-Host "FarmLink admin DOM hotfix installed successfully." -ForegroundColor Green
Write-Host "Backup: $Backup"
Write-Host ""
Write-Host "Next commands:"
Write-Host "  git diff --check"
Write-Host "  node --check frontend\admin\admin.js"
Write-Host "  git add frontend\admin\admin.js"
Write-Host '  git commit -m "Fix admin table DOM insertion error"'
Write-Host "  git push origin main"
