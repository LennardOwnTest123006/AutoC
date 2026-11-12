"""Settings, stored as JSON in %APPDATA%\\AutoC\\config.json."""
import json
from dataclasses import asdict, dataclass, field, fields

from . import paths

DEFAULT_EXCLUDED = [
    "keepass.exe", "keepassxc.exe", "1password.exe", "bitwarden.exe", "lastpass.exe",
    "cmd.exe", "powershell.exe", "pwsh.exe", "windowsterminal.exe", "conhost.exe",
    "putty.exe", "mstsc.exe", "vmconnect.exe",
]


@dataclass
class Config:
    enabled: bool = True
    languages: list = field(default_factory=lambda: ["en"])
    primary_language: str = "en"
    auto_add_keyboard_languages: bool = True
    fix_spelling: bool = True
    fix_sentence_start: bool = True        # capitalise first word of a sentence
    fix_two_initial_caps: bool = True      # THe -> The
    fix_caps_lock: bool = True             # hELLO -> Hello
    fix_standalone_i: bool = True          # English: i -> I, im -> I'm ...
    use_replacements: bool = True          # built-in + custom replacement tables
    undo_with_backspace: bool = True       # Backspace right after a fix restores your text
    excluded_apps: list = field(default_factory=lambda: list(DEFAULT_EXCLUDED))
    custom_replacements: dict = field(default_factory=dict)
    user_words: list = field(default_factory=list)
    toggle_hotkey: str = "f12"      # press once to pause AutoC, again to resume
    start_with_windows: bool = False

    @classmethod
    def load(cls, path=None) -> "Config":
        path = path or paths.user_dir() / "config.json"
        cfg = cls()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return cfg
        names = {f.name for f in fields(cls)}
        for k, v in data.items():
            if k in names:
                setattr(cfg, k, v)
        return cfg

    def save(self, path=None) -> None:
        path = path or paths.user_dir() / "config.json"
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(asdict(self), indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(path)
