import argparse
import sys

from . import __version__, languages
from .config import Config
from .dictionary import available_languages


def _attach_console():
    """The windowed .exe has no console: borrow the parent terminal's so output shows."""
    if sys.platform != "win32" or (sys.stdout is not None and sys.stderr is not None):
        return
    try:
        import ctypes
        if ctypes.windll.kernel32.AttachConsole(-1):
            sys.stdout = open("CONOUT$", "w", encoding="utf-8")
            sys.stderr = sys.stdout
    except Exception:
        pass


def _emit(text, out=None):
    if out:
        with open(out, "w", encoding="utf-8") as f:
            f.write(text + "\n")
    elif sys.stdout is not None:
        sys.stdout.write(text + "\n")


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
    _emit(type_text(engine, text + " ").rstrip(" "), args.out)


def cmd_languages(_):
    for code, path in sorted(available_languages().items()):
        _emit(f"{code:4} {languages.name(code)}")


def cmd_selftest(args):
    from . import selftest
    ok, report = selftest.run(e2e=args.e2e)
    _emit(report, args.out)
    return 0 if ok else 1


def cmd_dict_add(args):
    import shutil
    from . import paths
    dest = paths.user_dict_dir() / f"{args.code}{'.dic' if args.file.endswith('.dic') else '.txt'}"
    shutil.copyfile(args.file, dest)
    _emit(f"Added dictionary '{args.code}' -> {dest}")


def cmd_autostart(args):
    from . import app
    app.set_autostart(args.state == "on")
    _emit(f"Start with Windows: {args.state}")


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    interactive = not argv or argv[0] in ("run", "settings")
    try:
        return _main(argv)
    except SystemExit:
        raise
    except Exception as exc:     # windowed .exe: show + log instead of silently dying
        from . import crash
        crash.report(exc, gui=interactive)
        return 1


def _main(argv=None):
    ap = argparse.ArgumentParser(prog="autoc", description="AutoC - autocorrect for Windows, every language")
    ap.add_argument("--version", action="version", version=f"AutoC {__version__}")
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("run", help="start AutoC in the background (default)")
    sub.add_parser("settings", help="open the settings window")
    c = sub.add_parser("correct", help="test: run text through the autocorrect engine")
    c.add_argument("text", nargs="?")
    c.add_argument("--lang", help="comma separated language codes, e.g. de,en")
    c.add_argument("--out", help="write the result to this file instead of the terminal")
    t = sub.add_parser("selftest", help="check that AutoC works on this PC")
    t.add_argument("--e2e", action="store_true", help="also type real keys into a test window")
    t.add_argument("--out", help="write the report to this file")
    sub.add_parser("languages", help="list installed dictionaries")
    d = sub.add_parser("dict-add", help="add a dictionary (word list or Hunspell .dic)")
    d.add_argument("code")
    d.add_argument("file")
    a = sub.add_parser("autostart", help="start with Windows on/off")
    a.add_argument("state", choices=["on", "off"])
    args = ap.parse_args(argv)
    cmd = args.cmd or "run"
    if cmd not in ("run", "settings"):
        _attach_console()
    if cmd == "run":
        from . import app
        return app.run()
    if cmd == "settings":
        from . import settings_gui
        return settings_gui.main()
    r = {"correct": cmd_correct, "languages": cmd_languages, "dict-add": cmd_dict_add,
         "autostart": cmd_autostart, "selftest": cmd_selftest}[cmd](args)
    return r or 0
