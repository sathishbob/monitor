# Build wrapper script for Lab Server Monitoring Agent (Windows)
# This script delegates to the appropriate build script in build/scripts/

Param(
  [string]$Python = "python",
  [switch]$RecreateVenv
)

$ErrorActionPreference = 'Stop'

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BuildScript = Join-Path $ScriptDir 'scripts\build_windows.ps1'

if (-not (Test-Path $BuildScript)) {
    Write-Error "Build script not found at $BuildScript"
    exit 1
}

Write-Host "Building Lab Server Monitoring Agent..."
Write-Host "Using build script: $BuildScript"
Write-Host

Set-Location $ScriptDir
& $BuildScript -Python $Python -RecreateVenv:$RecreateVenv
