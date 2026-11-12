# Data sources and licenses

AutoC's **code** is MIT licensed (see `LICENSE`).
The bundled **word lists** in `autoc/data/` are derived from the following sources and are
distributed under **CC BY-SA 4.0** (https://creativecommons.org/licenses/by-sa/4.0/):

- `autoc/data/dictionaries/*` - word frequency lists from **wordfreq** by Robyn Speer
  (https://github.com/rspeer/wordfreq), data licensed CC BY-SA 4.0. Built by
  `tools/build_dictionaries.py`, which keeps the top words and prunes likely typos.
- `autoc/data/casing/de.*` - German capitalisation data built by `tools/build_german_casing.py` from
  - **german-nouns** (https://github.com/gambolputty/german-nouns), noun forms extracted from
    Wiktionary, CC BY-SA 4.0
  - the **Universal Dependencies German-GSD** treebank
    (https://github.com/UniversalDependencies/UD_German-GSD), CC BY-SA 4.0, used only to
    count how often words are written with a capital letter and as which part of speech.

Derived files may be reused under CC BY-SA 4.0 with attribution to the sources above.
`autoc/data/replacements/en.txt` is original work (MIT).
