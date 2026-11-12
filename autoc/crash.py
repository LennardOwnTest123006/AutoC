"""Error reporting for the windowed .exe, where a traceback would otherwise vanish."""
import sys
import time
import traceback

from . import paths


def log(text: str):
    try:
        with open(paths.user_dir() / "autoc.log", "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {text}\n")
    except OSError:
        pass


def report(exc: BaseException, title: str = "AutoC error"):
    text = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    log(text)
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(
                None, f"{exc}\n\nDetails: %APPDATA%\\AutoC\\autoc.log", title, 0x10)
        except Exception:
            pass
    else:
        sys.stderr.write(text)
