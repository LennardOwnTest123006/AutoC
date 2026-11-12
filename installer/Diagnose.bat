@echo off
title AutoC diagnose
echo Collecting information (takes up to 30 seconds) ...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Diagnose.ps1"
if not defined AUTOC_NO_PAUSE pause
