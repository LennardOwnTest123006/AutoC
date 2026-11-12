"""Windows-only glue: global low-level keyboard hook, key injection, foreground app.

Pure ctypes (no dependencies).  Importing this module is safe on any OS; the
Windows API is only touched when a hook is started.
"""
import ctypes
import os
import sys
import threading
from ctypes import wintypes

from . import languages

WH_KEYBOARD_LL, WH_MOUSE_LL = 13, 14
WM_KEYDOWN, WM_KEYUP, WM_SYSKEYDOWN, WM_SYSKEYUP = 0x100, 0x101, 0x104, 0x105
WM_QUIT = 0x12
LLKHF_INJECTED = 0x10
INPUT_KEYBOARD, KEYEVENTF_KEYUP, KEYEVENTF_UNICODE = 1, 2, 4
MAGIC = 0x41555443  # 'AUTC': marks our own injected keys

VK_BACK, VK_TAB, VK_RETURN, VK_SHIFT, VK_CONTROL, VK_MENU = 0x08, 0x09, 0x0D, 0x10, 0x11, 0x12
VK_CAPITAL, VK_PROCESSKEY = 0x14, 0xE5
MODIFIER_VKS = {0x10, 0x11, 0x12, 0xA0, 0xA1, 0xA2, 0xA3, 0xA4, 0xA5, 0x14, 0x5B, 0x5C}
# keys that move the cursor / change context: the engine can no longer follow the text
CONTEXT_VKS = {0x1B, 0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28, 0x2D, 0x2E,
               0x5D, 0x2C, 0x90, 0x91, 0x13} | set(range(0x70, 0x88))

ULONG_PTR = ctypes.c_size_t
LRESULT = ctypes.c_ssize_t


class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [("vkCode", ctypes.c_uint32), ("scanCode", ctypes.c_uint32),
                ("flags", ctypes.c_uint32), ("time", ctypes.c_uint32), ("dwExtraInfo", ULONG_PTR)]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_uint16), ("wScan", ctypes.c_uint16), ("dwFlags", ctypes.c_uint32),
                ("time", ctypes.c_uint32), ("dwExtraInfo", ULONG_PTR)]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_int32), ("dy", ctypes.c_int32), ("mouseData", ctypes.c_uint32),
                ("dwFlags", ctypes.c_uint32), ("time", ctypes.c_uint32), ("dwExtraInfo", ULONG_PTR)]


class _INPUTUNION(ctypes.Union):
    _fields_ = [("ki", KEYBDINPUT), ("mi", MOUSEINPUT)]


class INPUT(ctypes.Structure):
    _anonymous_ = ("u",)
    _fields_ = [("type", ctypes.c_uint32), ("u", _INPUTUNION)]


def parse_hotkey(spec: str):
    """'f12' / 'ctrl+alt+a' -> (vk, {'ctrl','alt','shift'})"""
    parts = [p.strip().lower() for p in spec.split("+") if p.strip()]
    mods = {p for p in parts if p in ("ctrl", "alt", "shift")}
    keys = [p for p in parts if p not in mods]
    if len(keys) != 1:
        raise ValueError(f"bad hotkey: {spec!r}")
    k = keys[0]
    named = {"pause": 0x13, "scrolllock": 0x91, "insert": 0x2D, "home": 0x24, "end": 0x23,
             "pageup": 0x21, "pagedown": 0x22, "space": 0x20, "esc": 0x1B}
    if k in named:
        return named[k], mods
    if k.startswith("f") and k[1:].isdigit() and 1 <= int(k[1:]) <= 24:
        return 0x6F + int(k[1:]), mods
    if len(k) == 1 and (k.isalpha() or k.isdigit()):
        return ord(k.upper()), mods
    raise ValueError(f"unknown key in hotkey: {spec!r}")


def build_inputs(backspaces: int, text: str, then=None):
    """INPUT array: N x Backspace, `text` as Unicode key events, optional Enter/Tab."""
    events = []

    def key(vk=0, scan=0, flags=0):
        i = INPUT(type=INPUT_KEYBOARD)
        i.ki = KEYBDINPUT(vk, scan, flags, 0, MAGIC)
        events.append(i)

    for _ in range(backspaces):
        key(VK_BACK)
        key(VK_BACK, 0, KEYEVENTF_KEYUP)
    data = text.encode("utf-16-le")
    for n in range(0, len(data), 2):
        unit = int.from_bytes(data[n:n + 2], "little")
        key(0, unit, KEYEVENTF_UNICODE)
        key(0, unit, KEYEVENTF_UNICODE | KEYEVENTF_KEYUP)
    if then:
        vk = VK_RETURN if then == "enter" else VK_TAB
        key(vk)
        key(vk, 0, KEYEVENTF_KEYUP)
    arr = (INPUT * len(events))(*events)
    return arr


class Win:
    """Thin, lazily bound wrappers around the Win32 calls we need."""

    def __init__(self):
        self.user32 = ctypes.WinDLL("user32", use_last_error=True)
        self.kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        u, k = self.user32, self.kernel32
        HOOKPROC = ctypes.WINFUNCTYPE(LRESULT, ctypes.c_int, ctypes.c_size_t, ctypes.c_ssize_t)
        self.HOOKPROC = HOOKPROC
        u.SetWindowsHookExW.argtypes = [ctypes.c_int, HOOKPROC, wintypes.HMODULE, wintypes.DWORD]
        u.SetWindowsHookExW.restype = wintypes.HHOOK
        u.CallNextHookEx.argtypes = [wintypes.HHOOK, ctypes.c_int, ctypes.c_size_t, ctypes.c_ssize_t]
        u.CallNextHookEx.restype = LRESULT
        u.UnhookWindowsHookEx.argtypes = [wintypes.HHOOK]
        u.SendInput.argtypes = [wintypes.UINT, ctypes.c_void_p, ctypes.c_int]
        u.GetKeyboardLayoutList.argtypes = [ctypes.c_int, ctypes.c_void_p]
        u.GetAsyncKeyState.argtypes = [ctypes.c_int]
        u.GetKeyState.argtypes = [ctypes.c_int]
        u.GetForegroundWindow.restype = wintypes.HWND
        u.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
        u.GetWindowThreadProcessId.restype = wintypes.DWORD
        u.GetKeyboardLayout.argtypes = [wintypes.DWORD]
        u.GetKeyboardLayout.restype = ctypes.c_void_p
        u.ToUnicodeEx.argtypes = [wintypes.UINT, wintypes.UINT, ctypes.c_void_p, wintypes.LPWSTR,
                                  ctypes.c_int, wintypes.UINT, ctypes.c_void_p]
        u.ToUnicodeEx.restype = ctypes.c_int
        u.GetMessageW.argtypes = [ctypes.c_void_p, wintypes.HWND, wintypes.UINT, wintypes.UINT]
        u.PostThreadMessageW.argtypes = [wintypes.DWORD, wintypes.UINT, ctypes.c_size_t, ctypes.c_ssize_t]
        k.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
        k.GetModuleHandleW.restype = wintypes.HMODULE
        k.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        k.OpenProcess.restype = wintypes.HANDLE
        k.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR,
                                                 ctypes.POINTER(wintypes.DWORD)]
        k.CloseHandle.argtypes = [wintypes.HANDLE]
        k.GetCurrentThreadId.restype = wintypes.DWORD

    def foreground(self):
        """(hwnd, thread_id, exe_name_lowercase)"""
        u, k = self.user32, self.kernel32
        hwnd = u.GetForegroundWindow()
        pid = wintypes.DWORD(0)
        tid = u.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        exe = ""
        h = k.OpenProcess(0x1000, False, pid.value)  # PROCESS_QUERY_LIMITED_INFORMATION
        if h:
            buf = ctypes.create_unicode_buffer(520)
            size = wintypes.DWORD(520)
            if k.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(size)):
                exe = os.path.basename(buf.value).lower()
            k.CloseHandle(h)
        return hwnd, tid, exe

    def layout_language(self, tid) -> str:
        hkl = self.user32.GetKeyboardLayout(tid) or 0
        return languages.LANGID.get((hkl & 0xFFFF) & 0x3FF, "")

    def installed_layout_languages(self):
        n = self.user32.GetKeyboardLayoutList(0, None)
        arr = (ctypes.c_void_p * n)()
        self.user32.GetKeyboardLayoutList(n, arr)
        out = []
        for hkl in arr:
            code = languages.LANGID.get(((hkl or 0) & 0xFFFF) & 0x3FF, "")
            if code and code not in out:
                out.append(code)
        return out

    def send(self, backspaces, text, then=None):
        arr = build_inputs(backspaces, text, then)
        self.user32.SendInput(len(arr), ctypes.byref(arr), ctypes.sizeof(INPUT))

    def translate(self, vk, scan, hkl):
        """Character(s) this key produces right now in the active layout ('' none, None dead key)."""
        u = self.user32
        state = (ctypes.c_ubyte * 256)()
        for key in (VK_SHIFT, VK_CONTROL, VK_MENU):
            if u.GetAsyncKeyState(key) & 0x8000:
                state[key] = 0x80
        if u.GetKeyState(VK_CAPITAL) & 1:
            state[VK_CAPITAL] = 1
        buf = ctypes.create_unicode_buffer(8)
        n = u.ToUnicodeEx(vk, scan, state, buf, 8, 0x4, hkl)   # 0x4: do not disturb dead-key state
        if n < 0:
            return None
        return buf.value[:n]


class KeyboardHook:
    def __init__(self, engine, config, on_toggle=None):
        self.engine, self.cfg, self.on_toggle = engine, config, on_toggle
        self.lock = threading.Lock()
        self.win = None
        self.accept_injected = False   # tests only: treat SendInput keys as typing
        self.thread_id = None
        self._swallowed = set()
        self._fg = (None, "", False)   # hwnd, layout, excluded
        self._hotkey = None
        self.apply_config(config)

    # called from any thread
    def apply_config(self, config):
        try:
            hk = parse_hotkey(config.toggle_hotkey)
        except ValueError:
            hk = parse_hotkey("f12")
        with self.lock:
            self.cfg, self._hotkey = config, hk
            self._excluded = {e.lower() for e in config.excluded_apps}
            self.engine.set_config(config)

    def toggle(self):
        with self.lock:
            on = not self.cfg.enabled
            self.engine.set_enabled(on)      # clean slate: old text is never fixed retroactively
        if self.on_toggle:
            threading.Thread(target=self.on_toggle, args=(on,), daemon=True).start()
        return on

    # ------------------------------------------------------------ hook procs
    def _kb_proc(self, nCode, wParam, lParam):
        try:
            if nCode == 0 and self._handle(wParam, KBDLLHOOKSTRUCT.from_address(lParam)):
                return 1
        except Exception:      # never let an error break the user's typing
            pass
        return self.win.user32.CallNextHookEx(None, nCode, wParam, lParam)

    def _mouse_proc(self, nCode, wParam, lParam):
        if nCode == 0 and wParam in (0x201, 0x204, 0x207):   # any button down
            self.engine.reset()
        return self.win.user32.CallNextHookEx(None, nCode, wParam, lParam)

    def _handle(self, wParam, kb) -> bool:
        """True = swallow this key event."""
        if kb.dwExtraInfo == MAGIC or (kb.flags & LLKHF_INJECTED and not self.accept_injected):
            return False
        vk, up = kb.vkCode, wParam in (WM_KEYUP, WM_SYSKEYUP)
        if up:
            if vk in self._swallowed:
                self._swallowed.discard(vk)
                return True
            return False
        w = self.win
        hotvk, hotmods = self._hotkey
        if vk == hotvk and self._mods_match(hotmods):
            self._swallowed.add(vk)
            self.toggle()
            return True
        with self.lock:
            if not self.cfg.enabled or not self.engine.ready():
                return False
            hwnd, tid, exe = w.foreground()
            if hwnd != self._fg[0]:
                lay = w.layout_language(tid)
                self._fg = (hwnd, lay, exe in self._excluded)
                self.engine.reset()
                self.engine.set_layout_language(lay)
            if self._fg[2]:
                return False
            return self._on_key(vk, kb.scanCode, tid)

    def _mods_match(self, mods):
        a = self.win.user32.GetAsyncKeyState
        want = {"ctrl": VK_CONTROL, "alt": VK_MENU, "shift": VK_SHIFT}
        return all(bool(a(v) & 0x8000) == (m in mods) for m, v in want.items())

    def _on_key(self, vk, scan, tid) -> bool:
        w, eng = self.win, self.engine
        if vk in MODIFIER_VKS:
            return False
        a = w.user32.GetAsyncKeyState
        ctrl, alt = bool(a(VK_CONTROL) & 0x8000), bool(a(VK_MENU) & 0x8000)
        if (ctrl or alt or a(0x5B) & 0x8000 or a(0x5C) & 0x8000) and not (ctrl and alt):  # shortcut, not AltGr
            eng.reset()
            return False
        if vk == VK_PROCESSKEY:
            eng.invalidate()
            return False
        if vk in CONTEXT_VKS:
            eng.reset()
            return False
        if vk == VK_BACK:
            act = eng.key_backspace()
        elif vk in (VK_RETURN, VK_TAB):
            act = eng.key_special("enter" if vk == VK_RETURN else "tab")
        else:
            chars = w.translate(vk, scan, w.user32.GetKeyboardLayout(tid))
            if chars is None:
                eng.invalidate()          # dead key: the next letter is composed by Windows
                return False
            act = None
            for ch in chars:
                act = eng.key_char(ch) or act
        if act is None:
            return False
        w.send(act.backspaces, act.text, act.then)
        self._swallowed.add(vk)
        return True

    # ----------------------------------------------------------------- loop
    def run(self):
        """Install the hooks and pump messages (blocks until stop())."""
        self.win = w = Win()
        self.thread_id = w.kernel32.GetCurrentThreadId()
        self._kb_cb = w.HOOKPROC(self._kb_proc)
        self._ms_cb = w.HOOKPROC(self._mouse_proc)
        mod = w.kernel32.GetModuleHandleW(None)
        h1 = w.user32.SetWindowsHookExW(WH_KEYBOARD_LL, self._kb_cb, mod, 0)
        h2 = w.user32.SetWindowsHookExW(WH_MOUSE_LL, self._ms_cb, mod, 0)
        if not h1:
            raise OSError(f"could not install keyboard hook (error {ctypes.get_last_error()})")
        msg = wintypes.MSG()
        while w.user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            pass
        w.user32.UnhookWindowsHookEx(h1)
        if h2:
            w.user32.UnhookWindowsHookEx(h2)

    def stop(self):
        if self.win and self.thread_id:
            self.win.user32.PostThreadMessageW(self.thread_id, WM_QUIT, 0, 0)
