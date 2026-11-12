@echo off
setlocal
title AutoC installer
set "SRC=%~dp0AutoC"
set "DEST=%LOCALAPPDATA%\Programs\AutoC"
if defined AUTOC_INSTALL_DIR set "DEST=%AUTOC_INSTALL_DIR%"

if not exist "%SRC%\AutoC.exe" (
  echo.
  echo  Could not find the "AutoC" folder next to Install.bat.
  echo  Please right-click the ZIP, choose "Extract All...", and run Install.bat from the extracted folder.
  echo.
  if not defined AUTOC_NO_PAUSE pause
  exit /b 1
)

echo Installing AutoC to "%DEST%" ...
taskkill /f /im AutoC.exe >nul 2>&1
robocopy "%SRC%" "%DEST%" /e /njh /njs /nfl /ndl /np >nul
if errorlevel 8 (
  echo  Copy failed. Close AutoC and try again.
  if not defined AUTOC_NO_PAUSE pause
  exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-ChildItem -Path '%DEST%' -Recurse | Unblock-File" >nul 2>&1

echo Creating Desktop and Start Menu shortcuts ...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$s=New-Object -ComObject WScript.Shell; foreach($d in @([Environment]::GetFolderPath('Desktop'),[Environment]::GetFolderPath('Programs'))){ if($d){ $l=$s.CreateShortcut((Join-Path $d 'AutoC.lnk')); $l.TargetPath='%DEST%\AutoC.exe'; $l.WorkingDirectory='%DEST%'; $l.Description='AutoC - autocorrect for every language'; $l.Save() } }"

echo Adding AutoC to PATH (use "autoc-cli" in a new terminal) ...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$p=[Environment]::GetEnvironmentVariable('Path','User'); if(-not $p){$p=''}; if(($p -split ';') -notcontains '%DEST%'){ [Environment]::SetEnvironmentVariable('Path',($p.TrimEnd(';')+';%DEST%').TrimStart(';'),'User') }"

echo Starting with Windows ...
"%DEST%\AutoC.exe" autostart on
if errorlevel 1 echo  Warning: could not enable "start with Windows". You can enable it later in AutoC settings.

if not defined AUTOC_NO_START (
  echo Starting AutoC ...
  start "" "%DEST%\AutoC.exe"
)

echo.
echo  AutoC is installed and running (look for the blue icon near the clock).
echo  F12 = autocorrect on/off.  Right-click the icon for settings.
echo.
if not defined AUTOC_NO_PAUSE pause
exit /b 0
