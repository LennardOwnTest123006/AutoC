import os
import pathlib


def user_dir() -> pathlib.Path:
    base = os.environ.get("APPDATA") or str(pathlib.Path.home() / ".config")
    p = pathlib.Path(base) / "AutoC"
    p.mkdir(parents=True, exist_ok=True)
    return p


def user_dict_dir() -> pathlib.Path:
    p = user_dir() / "dictionaries"
    p.mkdir(parents=True, exist_ok=True)
    return p


def data_dir() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parent / "data"
