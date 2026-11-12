"""Word lists + one-edit candidate search (works for any alphabet)."""
import gzip
import pathlib
import threading

from . import paths
from .textutil import lower, norm_apostrophe

_LETTERS_FROM_TOP = 5000


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
        """Known words within one edit (delete/insert/replace/transpose), best first."""
        rank, alpha = self.rank, self.alphabet
        found = set()
        for i in range(len(word) + 1):
            a, b = word[:i], word[i:]
            if b and a + b[1:] in rank:
                found.add(a + b[1:])
            if len(b) > 1 and a + b[1] + b[0] + b[2:] in rank:
                found.add(a + b[1] + b[0] + b[2:])
            for c in alpha:
                if b and a + c + b[1:] in rank:
                    found.add(a + c + b[1:])
                if a + c + b in rank:
                    found.add(a + c + b)
        found.discard(word)
        # a typo rarely changes the first letter: prefer candidates keeping it
        return sorted(found, key=lambda w: (w[:1] != word[:1], rank[w]))


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


class DictionaryStore:
    """`background=True`: get() never blocks - unloaded dictionaries load in a
    thread and read as None until ready (required inside the keyboard hook)."""

    def __init__(self, background: bool = False):
        self.background = background
        self._dicts = {}
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


def load_replacements(code: str) -> dict:
    p = paths.data_dir() / "replacements" / f"{code}.txt"
    out = {}
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                out[k.strip().lower()] = v.strip()
    return out
