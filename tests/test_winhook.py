"""Drive KeyboardHook with a fake Win32 layer (no Windows needed)."""
import ctypes
from types import SimpleNamespace

from autoc import winhook as wh
from autoc.config import Config
from autoc.engine import Engine


class FakeUser32:
    def GetAsyncKeyState(self, k): return 0
    def GetKeyState(self, k): return 0
    def GetKeyboardLayout(self, tid): return 0x0409


class FakeWin:
    def __init__(self):
        self.user32 = FakeUser32()
        self.sent = []

    def foreground(self): return 1, 1, "notepad.exe"
    def layout_language(self, tid): return "en"
    def translate(self, vk, scan, hkl): return {0x20: " ", 0xBE: "."}.get(vk, chr(vk).lower())
    def send(self, bs, text, then=None): self.sent.append((bs, text, then))


def make_hook(**kw):
    cfg = Config(auto_add_keyboard_languages=False, **kw)
    eng = Engine(cfg)
    eng.reset(sentence_start=True)
    hook = wh.KeyboardHook(eng, cfg)
    hook.win = FakeWin()
    return hook


def press(hook, vk, injected=False):
    kb = wh.KBDLLHOOKSTRUCT(vk, 0, wh.LLKHF_INJECTED if injected else 0, 0, 0)
    down = hook._handle(wh.WM_KEYDOWN, kb)
    up = hook._handle(wh.WM_KEYUP, kb)
    return down, up


def test_struct_sizes():
    assert ctypes.sizeof(wh.INPUT) == (40 if ctypes.sizeof(ctypes.c_void_p) == 8 else 28)


def test_hotkey_parse():
    assert wh.parse_hotkey("f12") == (0x7B, set())
    assert wh.parse_hotkey("Ctrl+Alt+A") == (0x41, {"ctrl", "alt"})


def test_typo_is_corrected_on_space_and_space_is_swallowed():
    h = make_hook()
    for ch in "teh":
        assert press(h, ord(ch.upper())) == (False, False)
    assert press(h, 0x20) == (True, True)               # space swallowed, fix injected
    assert h.win.sent == [(3, "the ", None)]


def test_injected_keys_are_ignored():
    h = make_hook()
    assert press(h, ord("T"), injected=True) == (False, False)


def test_f12_toggles_and_old_text_stays_untouched():
    h = make_hook()
    assert press(h, 0x7B) == (True, True)               # off (swallowed)
    for ch in "hsllo":
        press(h, ord(ch.upper()))
    press(h, 0x20)
    assert h.win.sent == []                             # nothing corrected while off
    press(h, 0x7B)                                      # on again
    press(h, 0x20)
    assert h.win.sent == []                             # "Hsllo" is never touched afterwards
    for ch in "teh":
        press(h, ord(ch.upper()))
    press(h, 0x20)
    assert h.win.sent == [(3, "the ", None)]


def test_enter_key_is_resent():
    h = make_hook()
    for ch in "teh":
        press(h, ord(ch.upper()))
    assert press(h, wh.VK_RETURN) == (True, True)
    assert h.win.sent == [(3, "the", "enter")]


def test_arrow_keys_reset_state():
    h = make_hook()
    for ch in "teh":
        press(h, ord(ch.upper()))
    assert press(h, 0x25) == (False, False)             # left arrow
    press(h, 0x20)
    assert h.win.sent == []


def test_excluded_app_is_ignored():
    h = make_hook(excluded_apps=["notepad.exe"])
    for ch in "teh":
        press(h, ord(ch.upper()))
    assert press(h, 0x20) == (False, False)
