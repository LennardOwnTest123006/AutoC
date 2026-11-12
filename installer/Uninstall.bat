@echo off
setlocal
title AutoC uninstaller
set "DEST=%LOCALAPPDATA%\Programs\AutoC"
if defined AUTOC_INSTALL_DIR set "DEST=%AUTOC_INSTALL_DIR%"
echo Removing AutoC ...
if exist "%DEST%\AutoC.exe" "%DEST%\AutoC.exe" autostart off
taskkill /f /im AutoC.exe >nul 2>&1
powershell -NoProfile -ExecutionPolicy Bypass -Command "foreach($d in @([Environment]::GetFolderPath('Desktop'),[Environment]::GetFolderPath('Programs'))){ if($d){ Remove-Item (Join-Path $d 'AutoC.lnk') -ErrorAction SilentlyContinue } }; $p=[Environment]::GetEnvironmentVariable('Path','User'); if($p){ [Environment]::SetEnvironmentVariable('Path',(($p -split ';' | Where-Object { $_ -and $_ -ne '%DEST%' }) -join ';'),'User') }"
timeout /t 2 /nobreak >nul
rmdir /s /q "%DEST%" >nul 2>&1
echo Done. (Your settings stay in %%APPDATA%%\AutoC - delete that folder too if you want.)
if not defined AUTOC_NO_PAUSE pause
exit /b 0
