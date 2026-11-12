AutoC - autocorrect for Windows, in every language
====================================================

INSTALL (30 seconds)
 1. Right-click the ZIP -> "Extract All..." -> Extract.
 2. Open the extracted folder and double-click  Install.bat
    (If Windows SmartScreen warns: "More info" -> "Run anyway". AutoC is open source.)
 3. Done. AutoC starts, adds a Desktop shortcut and starts with Windows.
    Blue icon near the clock = ON. Right-click it for Settings.

USE
 * Just type. AutoC fixes typos and capital letters in every program.
 * F12 = autocorrect OFF / ON again. Text you type while it is OFF is never
   corrected later (good for names like Koleku or deliberate typos).
 * Backspace right after a fix = undo, and AutoC never touches that word again.

IT DOES NOTHING? (very common: the antivirus blocks new unsigned programs)
 1. Double-click  Diagnose.bat  -> it creates AutoC-diagnose.txt on your Desktop and shows
    whether files were removed, whether your antivirus/Smart App Control blocked AutoC, and
    what AutoC's log says. (Tray icon -> "Check that everything works..." does the same.)
 2. Add the folder  %LOCALAPPDATA%\Programs\AutoC  to your antivirus exclusions
    (Windows Security -> Virus & threat protection -> Manage settings -> Exclusions),
    restore AutoC from the antivirus quarantine, run Install.bat again.
 3. Or avoid the .exe completely: double-click  Run-with-Python.bat  (installs Python if
    needed and runs AutoC through it - Microsoft-signed, rarely blocked).
 AutoC is intentionally NOT active in terminals (cmd, PowerShell, Windows Terminal) and in
 password managers. Test it in Notepad, Word, a browser or a chat.

TERMINAL (open a NEW terminal after installing)
   autoc-cli correct "i dont know wich langauge"
   autoc-cli languages
   autoc-cli selftest

UNINSTALL: run Uninstall.bat.
Source code: https://github.com/LennardOwnTest123006/AutoC   (MIT license)
