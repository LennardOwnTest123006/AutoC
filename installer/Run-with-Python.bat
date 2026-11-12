@echo off
setlocal
title AutoC (Python edition)
rem Use this if your antivirus blocks AutoC.exe. It runs AutoC through Python, which Microsoft signs.
set "SRC=%~dp0source"
if not exist "%SRC%\autoc" ( echo Please extract the whole ZIP first. & if not defined AUTOC_NO_PAUSE pause & exit /b 1 )

set "PY="
where py >nul 2>&1 && set "PY=py -3"
if not defined PY ( where python >nul 2>&1 && set "PY=python" )
if not defined PY (
  echo Python is not installed. Installing Python 3.12 with winget ^(about 1 minute^) ...
  winget install -e --id Python.Python.3.12 --silent --accept-package-agreements --accept-source-agreements
  if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set "PY=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
)
if not defined PY (
  echo.
  echo  Could not find or install Python automatically.
  echo  Install it from https://www.python.org/downloads/ ^(tick "Add python.exe to PATH"^), then run this file again.
  if not defined AUTOC_NO_PAUSE pause
  exit /b 1
)

echo Installing AutoC for your user ...
%PY% -m pip install --user --quiet --upgrade "%SRC%"
if errorlevel 1 ( echo pip install failed. & if not defined AUTOC_NO_PAUSE pause & exit /b 1 )

%PY% -c "import autoc" || ( echo AutoC could not be imported. & if not defined AUTOC_NO_PAUSE pause & exit /b 1 )

echo Enabling start with Windows ...
%PY% -m autoc autostart on

if not defined AUTOC_NO_START (
  echo Starting AutoC ...
  for /f "delims=" %%i in ('%PY% -c "import sys,os;print(os.path.join(os.path.dirname(sys.executable),'pythonw.exe'))"') do set "PYW=%%i"
  start "" "%PYW%" -m autoc run
)
echo.
echo  AutoC runs now (blue icon near the clock). F12 = on/off.
echo  Test it:  %PY% -m autoc selftest
if not defined AUTOC_NO_PAUSE pause
exit /b 0
