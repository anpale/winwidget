# Builds dist\agent.exe, dist\console.exe and installer\BrowserAgentSetup.exe (Windows).
# Needs: Python 3.12+ and Inno Setup 6 (winget install JRSoftware.InnoSetup).
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

function Run($exe, [string[]]$rest) {
    & $exe @rest
    if ($LASTEXITCODE -ne 0) { throw "$exe failed with exit code $LASTEXITCODE" }
}

Run python -m venv .venv
$py = ".\.venv\Scripts\python.exe"
Run $py -m pip install --upgrade pip
Run $py -m pip install -r requirements.txt pyinstaller

# agent.exe is windowed (no console); --collect-all pulls in Playwright's bundled driver.
Run $py -m PyInstaller --noconfirm --onefile --windowed --name agent --collect-all playwright agent.py
Run $py -m PyInstaller --noconfirm --onefile --name console console.py

$iscc = (Get-Command iscc -ErrorAction SilentlyContinue).Source
if (-not $iscc) {
    $iscc = @("$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
              "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
              "$env:ProgramFiles\Inno Setup 6\ISCC.exe") | Where-Object { Test-Path $_ } | Select-Object -First 1
}
if (-not $iscc) { throw "Inno Setup 6 not found (winget install JRSoftware.InnoSetup)" }
Run $iscc installer.iss

Write-Host "Done: installer\BrowserAgentSetup.exe"
