"""Build AutoC's German capitalisation data.

Sources (both CC BY-SA 4.0, see NOTICE.md):
  * german-nouns (pip, from Wiktionary): every inflected form of ~100k German nouns
  * Universal Dependencies German-GSD treebank: real German text, used to learn which
    words are *actually* written with a capital letter (so `rot`, `essen`, `gut` stay
    lowercase even though `Rot`, `Essen`, `Gut` are also nouns).

Usage:  pip install --no-deps german-nouns && python tools/build_german_casing.py
Writes autoc/data/casing/de.inf.txt.gz    verb infinitives (capitalised after zum/beim/vom/ins)
       autoc/data/casing/de.caps.txt.gz   lowercase forms that must start with a capital
       autoc/data/casing/de.lower.txt.gz  words that are (almost) never capitalised mid-sentence
"""
import collections
import csv
import gzip
import importlib.metadata as md
import pathlib
import urllib.request

OUT = pathlib.Path(__file__).resolve().parent.parent / "autoc" / "data" / "casing"
UD = "https://raw.githubusercontent.com/UniversalDependencies/UD_German-GSD/master/de_gsd-ud-{}.conllu"
# interjections / answers that are never capitalised mid-sentence, plus nouns that double as common adjectives
EXCLUDE = {"danke", "bitte", "hallo", "ach", "tschüss", "ciao", "okay", "ehrlich", "ernst", "weise", "mist",
           "bad", "top", "arm", "bar", "dank", "fast", "recht", "rat", "wert", "voll", "fick", "spass",
           "gut", "schön", "klar", "ganz", "neu", "alt", "jung", "lang", "kurz", "groß", "gross", "klein"}
NON_NOUN_UPOS = {"VERB", "AUX", "ADJ", "ADV", "ADP", "CCONJ", "SCONJ", "PRON", "DET", "PART", "INTJ"}
VERBISH = ("e", "en", "t", "st", "te", "es")   # sage, warte, lese ... : verb forms look like these
POLITE = {"sie", "ihr", "ihre", "ihren", "ihrem", "ihrer", "ihres", "ihnen", "euch", "euer", "eure"}


def noun_forms():
    path = next(f for f in md.files("german-nouns") if str(f).endswith("nouns.csv")).locate()
    forms, nominalised = set(), set()
    csv.field_size_limit(10 ** 8)
    with open(path, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            lemma = (row.get("lemma") or "").strip()
            plural = (row.get("nominativ plural") or "").strip()
            if lemma.lower().endswith(("en", "eln", "ern")) and (row.get("genus") or "") == "n" \
                    and plural in ("", lemma):       # Essen, Lachen, Erzählen: nominalised verbs
                nominalised.add(lemma.lower())
            for key, val in row.items():
                if key == "lemma" or key.split(" ")[0] in ("nominativ", "genitiv", "dativ", "akkusativ"):
                    for w in (val or "").split(","):
                        w = w.strip()
                        if w.isalpha() and w[0].isupper() and len(w) >= 3:
                            forms.add(w.lower())
    return forms, nominalised


def corpus_counts():
    up, low = collections.Counter(), collections.Counter()
    nonnoun, infinitives = set(), set()
    for split in ("train", "dev", "test"):
        with urllib.request.urlopen(UD.format(split), timeout=120) as r:
            for line in r.read().decode("utf-8").splitlines():
                if not line or line[0] == "#":
                    continue
                cols = line.split("\t")
                if len(cols) < 4 or not cols[0].isdigit():
                    continue
                form = cols[1]
                if not form.isalpha():
                    continue
                if cols[3] in NON_NOUN_UPOS:                 # seen as verb/adjective/adverb/...
                    nonnoun.add(form.lower())
                    nonnoun.add(cols[2].lower())
                if cols[3] in ("VERB", "AUX"):
                    lem = cols[2].lower()
                    if lem.isalpha() and len(lem) >= 4 and lem.endswith(("en", "ern", "eln")):
                        infinitives.add(lem)
                if cols[0] == "1":                           # sentence start: capital is positional
                    continue
                (up if form[0].isupper() else low)[form.lower()] += 1
    return up, low, nonnoun, infinitives


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    nouns, nominalised = noun_forms()
    up, low, nonnoun, infinitives = corpus_counts()
    from wordfreq import top_n_list
    english = set(top_n_list("en", 20000))
    common = set(top_n_list("de", 6000))     # very common words that the treebank never shows capitalised
    caps, lower = set(), set()
    for w in set(up) | set(low) | nouns:
        u, l = up[w], low[w]
        total = u + l
        if len(w) < 3:
            continue
        ratio = u / total if total else 0.0
        if total >= 15 and ratio <= 0.04 and w not in POLITE:
            lower.add(w)
        if w in EXCLUDE:
            continue
        if total >= 3:
            if ratio >= 0.85 and (w in nouns or (total >= 5 and ratio >= 0.95 and w not in english)):
                caps.add(w)
        elif w in nouns and l == 0 and w not in nonnoun and w not in nominalised \
                and not (w in common and w.endswith(VERBISH)):
            caps.add(w)                    # rare noun never seen as verb/adjective/lowercase
    infinitives |= nominalised
    for name, words in (("de.caps", caps), ("de.lower", lower), ("de.inf", infinitives)):
        with gzip.open(OUT / f"{name}.txt.gz", "wt", encoding="utf-8", compresslevel=9) as f:
            f.write("\n".join(sorted(words)) + "\n")
        print(name, len(words))


if __name__ == "__main__":
    main()
