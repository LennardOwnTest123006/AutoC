"""Word lists + one-edit candidate search (works for any alphabet)."""
import gzip
import math
import pathlib
import threading

from . import paths
from .textutil import lower, norm_apostrophe

_LETTERS_FROM_TOP = 5000
_KIND_PENALTY = {0: 0.0, 1: 1.0, 2: 1.5, 3: 1.5}   # swapped, wrong key, missing, extra


class Dictionary:
    def __init__(self, code: str, words):
        self.code = code
        self.rank = {}
        for w in words:
            w = lower(norm_apostrophe(w.strip()), code)
            if w and w not in self.rank:
                self.rank[w] = len(self.rank)
        top = list(self.rank)[:_LETTERS_FROM_TOP]
        self.alphabet = sorted({c for w in top for c in w})

    def __contains__(self, word: str) -> bool:
        return word in self.rank

    def __len__(self):
        return len(self.rank)

    def candidates(self, word: str):
        """Known words within one edit, best first.

        Ranking: same first letter, then the kind of typo (swapped neighbours are the most
        common mistake, then a wrong key, then a missing letter, then an extra letter),
        then word frequency."""
        rank, alpha = self.rank, self.alphabet
        found = {}                       # word -> typo kind (lower = more likely)

        def add(w, kind):
            if w in rank and w != word and found.get(w, 9) > kind:
                found[w] = kind
        for i in range(len(word) + 1):
            a, b = word[:i], word[i:]
            if len(b) > 1:
                add(a + b[1] + b[0] + b[2:], 0)       # swapped
            for c in alpha:
                if b:
                    add(a + c + b[1:], 1)             # wrong key
                add(a + c + b, 2)                     # missing letter
            if b:
                add(a + b[1:], 3)                     # extra letter
        # score = log(rank) + typo-kind penalty: a frequent word one extra/missing letter away
        # beats a rare word one wrong key away, but a swapped pair beats both
        return sorted(found, key=lambda w: (w[:1] != word[:1],
                                            math.log(rank[w] + 10) + _KIND_PENALTY[found[w]]))


def read_wordlist(path: pathlib.Path):
    """Plain list (`word` or `word<TAB>count`) or Hunspell .dic (`word/FLAGS`)."""
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if i == 0 and line.isdigit():  # hunspell word count header
                continue
            yield line.split("/")[0].split()[0]


def available_languages():
    """code -> path, user dictionaries override bundled ones."""
    found = {}
    for folder in (paths.data_dir() / "dictionaries", paths.user_dict_dir()):
        for p in folder.glob("*.txt*"):
            found[p.name.split(".")[0]] = p
        for p in folder.glob("*.dic"):
            found[p.stem] = p
    return found


class Casing:
    """Language-specific capitalisation data (currently German noun capitalisation)."""

    def __init__(self, caps, lower, inf):
        self.caps, self.lower, self.inf = caps, lower, inf


def _read_set(path):
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return frozenset(f.read().split())


def load_casing(code: str):
    folder = paths.data_dir() / "casing"
    caps = folder / f"{code}.caps.txt.gz"
    if not caps.exists():
        return None
    lower, inf = folder / f"{code}.lower.txt.gz", folder / f"{code}.inf.txt.gz"
    return Casing(_read_set(caps),
                  _read_set(lower) if lower.exists() else frozenset(),
                  _read_set(inf) if inf.exists() else frozenset())


class DictionaryStore:
    """`background=True`: get() never blocks - unloaded dictionaries load in a
    thread and read as None until ready (required inside the keyboard hook)."""

    def __init__(self, background: bool = False):
        self.background = background
        self._dicts = {}
        self._casing = {}
        self._loading = set()
        self._lock = threading.Lock()

    def get(self, code: str):
        with self._lock:
            if code in self._dicts:
                return self._dicts[code]
            if self.background:
                if code not in self._loading:
                    self._loading.add(code)
                    threading.Thread(target=self._load, args=(code,), daemon=True).start()
                return None
        return self._load(code)

    def casing(self, code: str):
        key = "casing:" + code
        with self._lock:
            if code in self._casing:
                return self._casing[code]
            if self.background:
                if key not in self._loading:
                    self._loading.add(key)
                    threading.Thread(target=self._load_casing, args=(code,), daemon=True).start()
                return None
        return self._load_casing(code)

    def _load_casing(self, code: str):
        c = load_casing(code)
        with self._lock:
            self._casing[code] = c
            self._loading.discard("casing:" + code)
        return c

    def _load(self, code: str):
        path = available_languages().get(code)
        d = Dictionary(code, read_wordlist(path)) if path else None
        with self._lock:
            self._dicts[code] = d
            self._loading.discard(code)
        return d

    def ready(self, codes) -> bool:
        with self._lock:
            return all(c in self._dicts for c in codes)

    def clear(self):
        with self._lock:
            self._dicts.clear()
            self._casing.clear()


def load_replacements(code: str) -> dict:
    p = paths.data_dir() / "replacements" / f"{code}.txt"
    out = {}
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                out[k.strip().lower()] = v.strip()
    return out
