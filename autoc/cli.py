import argparse
import sys

from . import __version__, languages
from .config import Config
from .dictionary import available_languages


def cmd_correct(args):
    from .engine import Engine
    from .simulate import type_text
    cfg = Config.load()
    if args.lang:
        cfg.languages = args.lang.split(",")
        cfg.primary_language = cfg.languages[0]
    cfg.auto_add_keyboard_languages = False
    text = args.text if args.text is not None else sys.stdin.read()
    engine = Engine(cfg)
    engine.reset(sentence_start=True)
    # a trailing space makes the last word count as finished
    sys.stdout.write(type_text(engine, text + " ").rstrip(" ") + "\n")


def cmd_languages(_):
    for code, path in sorted(available_languages().items()):
        print(f"{code:4} {languages.name(code)}")


def cmd_dict_add(args):
    import shutil
    from . import paths
    dest = paths.user_dict_dir() / f"{args.code}{'.dic' if args.file.endswith('.dic') else '.txt'}"
    shutil.copyfile(args.file, dest)
    print(f"Added dictionary '{args.code}' -> {dest}")


def cmd_autostart(args):
    from . import app
    app.set_autostart(args.state == "on")
    print("Start with Windows:", args.state)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="autoc", description="AutoC - autocorrect for Windows, every language")
    ap.add_argument("--version", action="version", version=f"AutoC {__version__}")
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("run", help="start AutoC in the background (default)")
    sub.add_parser("settings", help="open the settings window")
    c = sub.add_parser("correct", help="test: run text through the autocorrect engine")
    c.add_argument("text", nargs="?")
    c.add_argument("--lang", help="comma separated language codes, e.g. de,en")
    sub.add_parser("languages", help="list installed dictionaries")
    d = sub.add_parser("dict-add", help="add a dictionary (word list or Hunspell .dic)")
    d.add_argument("code")
    d.add_argument("file")
    a = sub.add_parser("autostart", help="start with Windows on/off")
    a.add_argument("state", choices=["on", "off"])
    args = ap.parse_args(argv)
    cmd = args.cmd or "run"
    if cmd == "run":
        from . import app
        return app.run()
    if cmd == "settings":
        from . import settings_gui
        return settings_gui.main()
    {"correct": cmd_correct, "languages": cmd_languages, "dict-add": cmd_dict_add,
     "autostart": cmd_autostart}[cmd](args)
    return 0
