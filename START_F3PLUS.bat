@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
title F3+ 2.0.0 - LucidOcelot

if not exist "%~dp0WINDOWS_BOOTSTRAP.ps1" (
  echo ERROR: WINDOWS_BOOTSTRAP.ps1 is missing.
  echo Extract the complete F3+ ZIP, then try again.
  pause
  exit /b 1
)
if not exist "%~dp0updater.py" (
  echo ERROR: updater.py is missing.
  echo Extract the complete F3+ ZIP, then try again.
  pause
  exit /b 1
)

powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0WINDOWS_BOOTSTRAP.ps1"
set "RC=%ERRORLEVEL%"
exit /b %RC%