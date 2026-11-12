# Collects everything needed to find out why AutoC does not work. Does not send anything anywhere.
$ErrorActionPreference = 'SilentlyContinue'
$out  = Join-Path ([Environment]::GetFolderPath('Desktop')) 'AutoC-diagnose.txt'
$dest = if ($env:AUTOC_INSTALL_DIR) { $env:AUTOC_INSTALL_DIR } else { Join-Path $env:LOCALAPPDATA 'Programs\AutoC' }
$r = New-Object System.Collections.Generic.List[string]
function Add($t) { $r.Add([string]$t) }

Add "AutoC diagnose - $(Get-Date)"
Add "Windows: $((Get-CimInstance Win32_OperatingSystem).Caption) $([Environment]::OSVersion.Version)"
Add ""
Add "== Files (if an antivirus removed them, they are missing here) =="
Add "install folder: $dest  exists=$(Test-Path $dest)"
foreach ($f in 'AutoC.exe', 'autoc-cli.exe') {
  $p = Join-Path $dest $f
  Add ("{0}: exists={1} size={2}" -f $f, (Test-Path $p), (Get-Item $p).Length)
}
Add ""
Add "== Is AutoC running? =="
$procs = Get-Process AutoC
if ($procs) { $procs | ForEach-Object { Add "AutoC.exe running, pid $($_.Id), started $($_.StartTime)" } } else { Add "AutoC.exe is NOT running" }
Add ""
Add "== Security software =="
Get-CimInstance -Namespace root/SecurityCenter2 -ClassName AntiVirusProduct | ForEach-Object { Add "antivirus: $($_.displayName)" }
$mp = Get-MpComputerStatus
if ($mp) { Add "Defender real-time protection: $($mp.RealTimeProtectionEnabled)" }
$sac = (Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\CI\Policy').VerifiedAndReputablePolicyState
Add "Smart App Control state (0=off, 1=ON, 2=evaluation): $sac"
Add "Defender detections mentioning AutoC:"
Get-MpThreatDetection | Where-Object { $_.Resources -match 'AutoC' } | ForEach-Object { Add "  $($_.InitialDetectionTime) $($_.Resources)" }
Get-WinEvent -FilterHashtable @{LogName='Microsoft-Windows-Windows Defender/Operational'; Id=1116,1117} -MaxEvents 50 |
  Where-Object { $_.Message -match 'AutoC' } | Select-Object -First 5 | ForEach-Object { Add "  event: $($_.TimeCreated) $($_.Message.Substring(0, [Math]::Min(200, $_.Message.Length)))" }
Add ""
Add "== Does the program itself run? (30 s limit) =="
$cli = Join-Path $dest 'autoc-cli.exe'
if (Test-Path $cli) {
  $tmp = Join-Path $env:TEMP 'autoc-selftest.txt'
  Remove-Item $tmp -ErrorAction SilentlyContinue
  $env:AUTOC_NO_GUI = '1'
  $p = Start-Process $cli -ArgumentList 'doctor', '--out', "`"$tmp`"" -PassThru -WindowStyle Hidden
  if ($p.WaitForExit(30000)) {
    Add "autoc-cli.exe exit code: $($p.ExitCode)"
    if (Test-Path $tmp) { Get-Content $tmp | ForEach-Object { Add "  $_" } } else { Add "  (no output file - the program was stopped before it could write)" }
  } else { $p.Kill(); Add "autoc-cli.exe did NOT finish in 30 s (blocked or frozen - probably by security software)" }
} else { Add "autoc-cli.exe not found" }
Add ""
Add "== AutoC log =="
$log = Join-Path $env:APPDATA 'AutoC\autoc.log'
if (Test-Path $log) { Get-Content $log -Tail 30 | ForEach-Object { Add "  $_" } } else { Add "no log: AutoC has never started on this PC" }

$r | Set-Content -Path $out -Encoding UTF8
Write-Host "Report written to $out"
if (-not $env:AUTOC_NO_PAUSE) { Start-Process notepad $out }
