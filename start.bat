@echo off
setlocal
REM SearchStudio double-click launcher: repo root -> webapp\start.ps1
set "LAUNCHDIR=%~dp0webapp"
cd /d "%LAUNCHDIR%"
if not exist "%CD%" (
  echo [ERROR] searchstudio-mcp launch folder not found: %LAUNCHDIR%
  exit /b 1
)
if not exist "start.ps1" (
  echo [ERROR] No start.ps1 in %CD%
  exit /b 1
)
powershell -NoProfile -ExecutionPolicy Bypass -File "start.ps1" %*
set "EXITCODE=%ERRORLEVEL%"
if not "%EXITCODE%"=="0" (
  echo [searchstudio-mcp-start.bat] exited with error - window held open, instacrash guard
  pause
)
endlocal
