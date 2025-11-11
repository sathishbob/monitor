Param(
  [string]$Python = "python",
  [switch]$RecreateVenv
)

$ErrorActionPreference = 'Stop'

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $ScriptDir)
Set-Location $ProjectRoot

$VenvPath = Join-Path $ProjectRoot 'venv'
if ($RecreateVenv -and (Test-Path $VenvPath)) {
  Remove-Item -Recurse -Force $VenvPath
}

if (-not (Test-Path $VenvPath)) {
  Write-Host "[build] Creating virtualenv..."
  & $Python -m venv $VenvPath
}

$Activate = Join-Path $VenvPath 'Scripts\Activate.ps1'
. $Activate

Write-Host "[build] Upgrading pip..."
python -m pip install --upgrade pip | Out-Null

Write-Host "[build] Installing requirements..."
pip install -r requirements.txt | Out-Null
pip install pyinstaller | Out-Null

Write-Host "[build] Building onefile binary..."
pyinstaller --onefile --name las-agent.exe --clean --distpath build\dist --workpath build\monitor-agent --specpath build monitor_agent.py

Write-Host "[build] Done. Binary at: $ProjectRoot\build\dist\las-agent.exe"



