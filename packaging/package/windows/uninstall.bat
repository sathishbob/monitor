@echo off
REM Windows Uninstaller for Monitor Agent

setlocal
set "SERVICE_NAME=las-agent"
set "INSTALL_DIR=C:\Program Files\las-agent"

echo ========================================
echo Monitor Agent Uninstallation
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

echo [1/3] Stopping service...
net stop %SERVICE_NAME% 2>nul

echo [2/3] Removing Windows Service...
set "NSSM_DIR=%INSTALL_DIR%\tools\nssm"
if exist "%NSSM_DIR%\nssm.exe" (
    "%NSSM_DIR%\nssm.exe" remove %SERVICE_NAME% confirm
) else (
    sc delete %SERVICE_NAME%
)

echo [3/3] Removing installation directory...
if exist "%INSTALL_DIR%" (
    echo WARNING: Removing %INSTALL_DIR%
    echo All data will be lost!
    pause
    rmdir /S /Q "%INSTALL_DIR%"
)

echo.
echo ========================================
echo Uninstallation Complete!
echo ========================================
echo.
echo Service removed successfully.
pause

