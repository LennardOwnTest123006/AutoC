"""`autoc selftest`: verifies the engine, dictionaries and (on Windows) the real keyboard hook."""
import sys
import threading
import time

from . import __version__
from .config import Config
from .dictionary import available_languages
from .engine import Engine
from .simulate import type_text


def _engine_checks(lines):
    cfg = Config(auto_add_keyboard_languages=False, languages=["en"])
    e = Engine(cfg)
    e.reset(sentence_start=True)
    got = type_text(e, "teh quick brwon fox. i dont know ")
    want = "The quick brown fox. I don't know "
    lines.append(f"engine: {'OK' if got == want else 'FAIL'}  ({got!r})")
    langs = available_languages()
    lines.append(f"dictionaries: {'OK' if len(langs) >= 30 else 'FAIL'}  ({len(langs)} languages)")
    return got == want and len(langs) >= 30


def _hook_checks(lines):
    from . import winhook as wh
    w = wh.Win()
    n = len(w.installed_layout_languages())
    hwnd, tid, exe = w.foreground()
    lines.append(f"win32 api: OK  (keyboard languages: {w.installed_layout_languages()}, foreground exe: {exe or '-'})")
    cfg = Config(auto_add_keyboard_languages=False, languages=["en"], excluded_apps=[])
    eng = Engine(cfg)
    hook = wh.KeyboardHook(eng, cfg)
    err = []

    def go():
        try:
            hook.run()
        except Exception as exc:
            err.append(exc)
    t = threading.Thread(target=go, daemon=True)
    t.start()
    time.sleep(1.0)
    ok = bool(hook.thread_id) and not err and t.is_alive()
    lines.append(f"keyboard hook install: {'OK' if ok else 'FAIL ' + str(err)}")
    hook.stop()
    t.join(3)
    return ok


def _send_key(user32, vk, up=False):
    from .winhook import INPUT, INPUT_KEYBOARD, KEYBDINPUT, KEYEVENTF_KEYUP
    import ctypes
    i = INPUT(type=INPUT_KEYBOARD)
    i.ki = KEYBDINPUT(vk, user32.MapVirtualKeyW(vk, 0), KEYEVENTF_KEYUP if up else 0, 0, 0)
    user32.SendInput(1, ctypes.byref(i), ctypes.sizeof(INPUT))


def _e2e(lines, external=False):
    """Real keystrokes -> real hook -> real text box."""
    import ctypes
    import tkinter as tk
    from . import winhook as wh
    user32 = ctypes.WinDLL("user32")
    user32.VkKeyScanW.argtypes = [ctypes.c_wchar]
    user32.MapVirtualKeyW.argtypes = [ctypes.c_uint, ctypes.c_uint]

    root = tk.Tk()
    root.title("AutoC selftest")
    root.geometry("420x120+80+80")
    box = tk.Text(root)
    box.pack(fill="both", expand=True)
    root.attributes("-topmost", True)
    root.update()
    root.focus_force()
    box.focus_force()
    for _ in range(20):
        root.update()
        time.sleep(0.05)
    user32.GetForegroundWindow.restype = ctypes.c_void_p
    if user32.GetForegroundWindow() != root.winfo_id() and \
            user32.GetForegroundWindow() != user32.GetParent(root.winfo_id()):
        # make sure the test window owns the keyboard focus (needs an interactive desktop)
        user32.keybd_event(0x12, 0, 0, 0)
        user32.keybd_event(0x12, 0, 2, 0)
        user32.SetForegroundWindow(ctypes.c_void_p(user32.GetParent(root.winfo_id()) or root.winfo_id()))
        for _ in range(20):
            root.update()
            time.sleep(0.05)

    hook = t = None
    if not external:               # normal: run our own hook; external: a real running AutoC does it
        cfg = Config(auto_add_keyboard_languages=False, languages=["en"], excluded_apps=[])
        eng = Engine(cfg)
        eng.preload()
        hook = wh.KeyboardHook(eng, cfg)
        hook.accept_injected = True
        t = threading.Thread(target=hook.run, daemon=True)
        t.start()
    time.sleep(1.0)

    def pump(sec=0.05):
        end = time.time() + sec
        while time.time() < end:
            root.update()
            time.sleep(0.005)

    def typ(text):
        for ch in text:
            scan = user32.VkKeyScanW(ch)
            _send_key(user32, scan & 0xFF)
            _send_key(user32, scan & 0xFF, up=True)
            pump(0.04)
        pump(0.2)

    def tap(vk):
        _send_key(user32, vk)
        _send_key(user32, vk, up=True)
        pump(0.15)

    typ("teh quick brwon fox ")
    tap(0x7B)                     # F12: off
    typ("hsllo wrogn ")           # typed while off -> must stay as typed
    tap(0x7B)                     # F12: on
    typ("wrogn recieve ")
    tap(0x08)                     # Backspace right after a fix -> undo
    pump(0.3)
    got = box.get("1.0", "end-1c")
    if hook:
        hook.stop()
        t.join(3)
    root.destroy()
    want = "the quick brown fox hsllo wrogn wrong recieve"
    ok = got == want
    lines.append(f"real typing through the hook: {'OK' if ok else 'FAIL'}")
    if not ok:
        lines.append(f"   expected: {want!r}\n   got:      {got!r}")
    return ok


def run(e2e: bool = False, external: bool = False):
    lines = [f"AutoC {__version__} selftest on {sys.platform}"]
    ok = _engine_checks(lines)
    if sys.platform == "win32":
        try:
            ok = _hook_checks(lines) and ok
            if e2e:
                ok = _e2e(lines, external) and ok
        except Exception as exc:
            import traceback
            lines.append("FAIL: " + "".join(traceback.format_exception(exc)))
            ok = False
    lines.append("RESULT: " + ("ALL OK" if ok else "FAILED"))
    return ok, "\n".join(lines)
