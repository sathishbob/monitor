# PowerShell Installer for Monitor Agent
# This script installs the monitor agent as a Windows service

$ErrorActionPreference = "Stop"

# Configuration
$InstallDir = "C:\Program Files\las-agent"
$ServiceName = "las-agent"
$ServiceDisplayName = "Lab Server Monitoring AI Agent"
$ServiceDescription = "Comprehensive monitoring and AI analytics for lab server environments"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Monitor Agent Windows Installation" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check for administrator privileges
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "ERROR: This script must be run as Administrator" -ForegroundColor Red
    Write-Host "Please run PowerShell as Administrator and try again."
    Read-Host "Press Enter to exit"
    exit 1
}

try {
    # Step 1: Create installation directory
    Write-Host "[1/6] Creating installation directory..." -ForegroundColor Yellow
    if (-not (Test-Path $InstallDir)) {
        New-Item -ItemType Directory -Path $InstallDir | Out-Null
    }
    if (-not (Test-Path "$InstallDir\logs")) {
        New-Item -ItemType Directory -Path "$InstallDir\logs" | Out-Null
    }

    # Step 2: Copy application files
    Write-Host "[2/6] Copying application files..." -ForegroundColor Yellow
    Copy-Item -Path "agent" -Destination "$InstallDir\agent" -Recurse -Force
    Copy-Item -Path "monitor_agent.py" -Destination "$InstallDir\" -Force
    Copy-Item -Path "requirements.txt" -Destination "$InstallDir\" -Force
    Copy-Item -Path "config.json" -Destination "$InstallDir\" -Force

    # Step 3: Setup Python environment
    Write-Host "[3/6] Setting up Python environment..." -ForegroundColor Yellow
    Push-Location $InstallDir
    
    if (-not (Test-Path "venv")) {
        python -m venv venv
        & "venv\Scripts\Activate.ps1"
        python -m pip install --upgrade pip | Out-Null
        pip install -r requirements.txt | Out-Null
        deactivate
    } else {
        & "venv\Scripts\Activate.ps1"
        python -m pip install --upgrade pip | Out-Null
        pip install -r requirements.txt | Out-Null
        deactivate
    }
    
    Pop-Location

    # Step 4: Check for NSSM
    Write-Host "[4/6] Checking for NSSM..." -ForegroundColor Yellow
    $nssmPath = "$InstallDir\tools\nssm\nssm.exe"
    
    if (-not (Test-Path $nssmPath)) {
        Write-Host "NSSM not found. Please install it first:" -ForegroundColor Yellow
        Write-Host "  Download: https://nssm.cc/download" -ForegroundColor Yellow
        Write-Host "  Or use: winget install NSSM.NSSM" -ForegroundColor Yellow
        
        # Try to find NSSM in PATH
        $nssmExe = Get-Command nssm -ErrorAction SilentlyContinue
        if ($nssmExe) {
            $nssmPath = $nssmExe.Source
            Write-Host "Found NSSM in PATH: $nssmPath" -ForegroundColor Green
        } else {
            Write-Host "ERROR: NSSM is required to install as a service" -ForegroundColor Red
            Read-Host "Press Enter to exit"
            exit 1
        }
    }

    # Step 5: Create Windows Service
    Write-Host "[5/6] Creating Windows Service..." -ForegroundColor Yellow
    & $nssmPath install $ServiceName "$InstallDir\venv\Scripts\python.exe" "$InstallDir\monitor_agent.py"
    & $nssmPath set $ServiceName DisplayName $ServiceDisplayName
    & $nssmPath set $ServiceName Description $ServiceDescription
    & $nssmPath set $ServiceName Start SERVICE_AUTO_START
    & $nssmPath set $ServiceName AppStdout "$InstallDir\logs\service.log"
    & $nssmPath set $ServiceName AppStderr "$InstallDir\logs\service-error.log"

    # Step 6: Start service
    Write-Host "[6/6] Starting service..." -ForegroundColor Yellow
    Start-Service -Name $ServiceName

    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Installation Complete!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
Write-Host "Service Name: $ServiceName" -ForegroundColor Cyan
    Write-Host "Installation: $InstallDir" -ForegroundColor Cyan
    Write-Host "Logs: $InstallDir\logs" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "To manage the service:" -ForegroundColor Yellow
    Write-Host "  - Start:   Start-Service -Name $ServiceName"
    Write-Host "  - Stop:    Stop-Service -Name $ServiceName"
    Write-Host "  - Status:  Get-Service -Name $ServiceName"
    Write-Host ""

} catch {
    Write-Host "ERROR: Installation failed" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Read-Host "Press Enter to exit"

