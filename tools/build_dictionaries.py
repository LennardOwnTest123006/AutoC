"""Build AutoC's bundled word lists from the `wordfreq` package.

Usage:  pip install wordfreq && python tools/build_dictionaries.py

Writes autoc/data/dictionaries/<code>.txt.gz (one word per line, most frequent
first).  Likely typos that wordfreq picked up from web text are pruned: a word is
dropped when a one-edit neighbour is >= PRUNE_ZIPF_GAP zipf points more frequent.
"""
import gzip
import pathlib
import unicodedata

from wordfreq import available_languages, top_n_list, zipf_frequency

OUT = pathlib.Path(__file__).resolve().parent.parent / "autoc" / "data" / "dictionaries"
SIZE = 60000
KEEP_TOP = 8000          # never prune the most frequent words
PRUNE_ZIPF_GAP = 1.5
SKIP = {"ja", "zh", "ko"}  # no space-separated words


def is_word(w: str) -> bool:
    return bool(w) and all(unicodedata.category(c)[0] in "LM" or c == "'" for c in w) and w[0] != "'"


def edits1(word, alphabet):
    out = set()
    for i in range(len(word) + 1):
        a, b = word[:i], word[i:]
        if b:
            out.add(a + b[1:])
            for c in alphabet:
                out.add(a + c + b[1:])
        if len(b) > 1:
            out.add(a + b[1] + b[0] + b[2:])
        for c in alphabet:
            out.add(a + c + b)
    out.discard(word)
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for lang in sorted(available_languages("best")):
        if lang in SKIP:
            continue
        try:
            raw = top_n_list(lang, SIZE * 2, wordlist="best")
        except Exception as exc:  # tokenizer missing etc.
            print("skip", lang, exc)
            continue
        words, seen = [], set()
        for w in raw:
            w = unicodedata.normalize("NFC", w.replace("’", "'"))
            if is_word(w) and w not in seen:
                seen.add(w)
                words.append(w)
            if len(words) >= SIZE:
                break
        alphabet = sorted({c for w in words[:5000] for c in w})
        zipf = {w: zipf_frequency(w, lang, wordlist="best") for w in words}
        kept = []
        for i, w in enumerate(words):
            if i >= KEEP_TOP and len(w) >= 4:
                best = max((zipf[n] for n in edits1(w, alphabet) if n in zipf), default=0)
                if best - zipf[w] >= PRUNE_ZIPF_GAP:
                    continue
            kept.append(w)
        with gzip.open(OUT / f"{lang}.txt.gz", "wt", encoding="utf-8", compresslevel=9) as f:
            f.write("\n".join(kept) + "\n")
        print(f"{lang}: {len(kept)} words ({len(words) - len(kept)} pruned)")


if __name__ == "__main__":
    main()
