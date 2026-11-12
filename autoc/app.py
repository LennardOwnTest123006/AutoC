"""AutoC background app: keyboard hook + system-tray icon."""
import ctypes
import os
import subprocess
import sys
import threading
import time

from . import __version__, paths
from .config import Config
from .dictionary import DictionaryStore
from .engine import Engine

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def command_line(*args) -> list:
    if getattr(sys, "frozen", False):
        return [sys.executable, *args]
    return [sys.executable, "-m", "autoc", *args]


def set_autostart(on: bool):
    import winreg
    if on:
        exe = sys.executable
        if getattr(sys, "frozen", False):
            cmd = f'"{exe}" run'
        else:                                   # prefer pythonw: no console window
            cmd = f'"{exe.replace("python.exe", "pythonw.exe")}" -m autoc run'
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as k:   # creates it if missing
            winreg.SetValueEx(k, "AutoC", 0, winreg.REG_SZ, cmd)
    else:
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as k:
                winreg.DeleteValue(k, "AutoC")
        except FileNotFoundError:
            pass


def make_icon(enabled: bool):
    from PIL import Image, ImageDraw
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((2, 2, 62, 62), radius=14, fill=(34, 139, 230, 255) if enabled else (120, 120, 120, 255))
    if enabled:
        d.line([(16, 34), (28, 46), (49, 20)], fill="white", width=7, joint="curve")
    else:
        d.rectangle((20, 18, 28, 46), fill="white")
        d.rectangle((36, 18, 44, 46), fill="white")
    return img


def single_instance():
    k = ctypes.WinDLL("kernel32", use_last_error=True)
    k.CreateMutexW(None, False, "Local\\AutoC-single-instance")
    return ctypes.get_last_error() != 183   # ERROR_ALREADY_EXISTS


def run():
    if sys.platform != "win32":
        print("AutoC's background mode only runs on Windows. Try:  autoc correct \"teh text\"")
        return 1
    if not single_instance():
        print("AutoC is already running.")
        return 0
    import pystray
    from .winhook import KeyboardHook, Win

    cfg = Config.load()
    store = DictionaryStore(background=True)
    engine = Engine(cfg, store)
    try:   # every language of every installed keyboard layout
        if cfg.auto_add_keyboard_languages:
            from .dictionary import available_languages
            have = available_languages()
            for code in Win().installed_layout_languages():
                if code in have and code not in engine.langs:
                    engine.langs.append(code)
    except Exception:
        pass
    icon = pystray.Icon("AutoC", make_icon(cfg.enabled), f"AutoC {__version__}")
    hook = None

    def on_toggle(on):
        icon.icon = make_icon(on)
        icon.title = "AutoC: ON" if on else "AutoC: OFF (press the hotkey to resume)"
        try:
            ctypes.windll.user32.MessageBeep(0x40 if on else 0x30)
            icon.notify("Autocorrect is ON" if on else "Autocorrect is OFF", "AutoC")
        except Exception:
            pass

    hook = KeyboardHook(engine, cfg, on_toggle)

    def watch_config():
        path = paths.user_dir() / "config.json"
        last = path.stat().st_mtime if path.exists() else 0
        while True:
            time.sleep(2)
            try:
                m = path.stat().st_mtime
            except OSError:
                continue
            if m != last:
                last = m
                new = Config.load()
                new.enabled = hook.cfg.enabled
                store.clear()
                hook.apply_config(new)
                for c in engine.langs:
                    store.get(c)

    threading.Thread(target=hook.run, daemon=True).start()
    threading.Thread(target=watch_config, daemon=True).start()
    for c in engine.langs:
        store.get(c)

    def quit_(icon_, item):
        hook.stop()
        icon_.stop()

    icon.menu = pystray.Menu(
        pystray.MenuItem(lambda i: f"Autocorrect {'ON' if hook.cfg.enabled else 'OFF'}  ({hook.cfg.toggle_hotkey.upper()})",
                         lambda i, it: hook.toggle(), default=True),
        pystray.MenuItem("Settings...", lambda i, it: subprocess.Popen(command_line("settings"))),
        pystray.MenuItem("Open settings folder", lambda i, it: os.startfile(paths.user_dir())),
        pystray.MenuItem("Quit AutoC", quit_),
    )
    icon.run()
    return 0
