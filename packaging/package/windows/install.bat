@echo off
REM Windows Installer for Monitor Agent
REM This script installs the monitor agent as a Windows service

setlocal enabledelayedexpansion
set "INSTALL_DIR=C:\Program Files\las-agent"
set "SERVICE_NAME=las-agent"
set "SERVICE_DISPLAY_NAME=Lab Server Monitoring AI Agent"
set "SERVICE_DESCRIPTION=Comprehensive monitoring and AI analytics for lab server environments"

echo ========================================
echo Monitor Agent Windows Installation
echo ========================================
echo.

REM Check for administrator privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This script must be run as Administrator
    echo Please run as Administrator and try again.
    pause
    exit /b 1
)

echo [1/6] Creating installation directory...
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
if not exist "%INSTALL_DIR%\logs" mkdir "%INSTALL_DIR%\logs"

echo [2/6] Copying application files...
xcopy /E /I /Y "agent" "%INSTALL_DIR%\agent"
copy /Y "monitor_agent.py" "%INSTALL_DIR%\"
copy /Y "requirements.txt" "%INSTALL_DIR%\"
copy /Y "config.json" "%INSTALL_DIR%\"

echo [3/6] Setting up Python environment...
cd "%INSTALL_DIR%"
if not exist "venv" (
    python -m venv venv
    call venv\Scripts\activate.bat
    python -m pip install --upgrade pip >nul 2>&1
    pip install -r requirements.txt >nul 2>&1
    deactivate
) else (
    call venv\Scripts\activate.bat
    python -m pip install --upgrade pip >nul 2>&1
    pip install -r requirements.txt >nul 2>&1
    deactivate
)

echo [4/6] Setting up NSSM (Non-Sucking Service Manager)...
set "NSSM_DIR=%INSTALL_DIR%\tools\nssm"
if not exist "%NSSM_DIR%" (
    mkdir "%NSSM_DIR%"
    echo Please download NSSM and extract to %NSSM_DIR%
    echo NSSM download: https://nssm.cc/download
    echo Or use: winget install NSSM.NSSM
    pause
    exit /b 1
)

echo [5/6] Creating Windows Service...
%NSSM_DIR%\nssm.exe install %SERVICE_NAME% "%INSTALL_DIR%\venv\Scripts\python.exe" "%INSTALL_DIR%\monitor_agent.py"
%NSSM_DIR%\nssm.exe set %SERVICE_NAME% DisplayName "%SERVICE_DISPLAY_NAME%"
%NSSM_DIR%\nssm.exe set %SERVICE_NAME% Description "%SERVICE_DESCRIPTION%"
%NSSM_DIR%\nssm.exe set %SERVICE_NAME% Start SERVICE_AUTO_START
%NSSM_DIR%\nssm.exe set %SERVICE_NAME% AppStdout "%INSTALL_DIR%\logs\service.log"
%NSSM_DIR%\nssm.exe set %SERVICE_NAME% AppStderr "%INSTALL_DIR%\logs\service-error.log"

echo [6/6] Starting service...
net start %SERVICE_NAME%

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo Service Name: %SERVICE_NAME%
echo Installation: %INSTALL_DIR%
echo Logs: %INSTALL_DIR%\logs
echo.
echo To manage the service:
echo   - Start:   net start %SERVICE_NAME%
echo   - Stop:    net stop %SERVICE_NAME%
echo   - Status:  sc query %SERVICE_NAME%
echo.
pause

