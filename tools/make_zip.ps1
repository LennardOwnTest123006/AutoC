# Builds AutoC-Windows.zip from dist\AutoC (run `pyinstaller autoc.spec` first).
$ErrorActionPreference = 'Stop'
if (Test-Path pkg) { Remove-Item pkg -Recurse -Force }
New-Item -ItemType Directory pkg | Out-Null
Copy-Item dist\AutoC pkg\AutoC -Recurse
Copy-Item installer\* pkg\
# plain source for Run-with-Python.bat (no .exe needed)
New-Item -ItemType Directory pkg\source | Out-Null
Copy-Item autoc pkg\source\autoc -Recurse
Get-ChildItem pkg\source -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force
Copy-Item pyproject.toml, README.md, LICENSE pkg\source\
if (Test-Path AutoC-Windows.zip) { Remove-Item AutoC-Windows.zip }
Compress-Archive -Path pkg\* -DestinationPath AutoC-Windows.zip
Get-ChildItem pkg | Format-Table Name
