# AutoC

**Open-source autocorrect for Windows - in every language.**
AutoC runs in the background and fixes what you type in *any* program: typos,
capital letters at the start of sentences, `THe` / `hELLO` accidents, `i` → `I`,
`dont` → `don't` - automatically, while you type.

The program and its settings are in English. The *correction* works for **39 languages**
(Arabic, Bulgarian, Bengali, Catalan, Czech, Danish, German, Greek, English, Spanish,
Persian, Finnish, Filipino, French, Hebrew, Hindi, Hungarian, Indonesian, Icelandic,
Italian, Lithuanian, Latvian, Macedonian, Malay, Norwegian, Dutch, Polish, Portuguese,
Romanian, Russian, Serbo-Croatian, Slovak, Slovenian, Swedish, Tamil, Turkish, Ukrainian,
Urdu, Vietnamese) and you can add **any other language** with your own dictionary.

## Features
- Works in every Windows app (global keyboard hook, like a phone keyboard for your PC)
- **Every keyboard layout**: reads the real characters from the active layout, so
  `ä ñ ç ß й 中…` all work; languages of your installed keyboards are enabled automatically
- **Language auto-detection**: type English, then German, then French - AutoC follows
- **German noun capitalisation** (`haus` → `Haus`, `zum essen` → `zum Essen`, `Nach` → `nach`) - data-driven,
  leaves ambiguous words (`rot`, `essen`, `ich suche`) alone
- Fixes: spelling, sentence capitalisation (after `. ! ? …` and Enter), `THe`→`The`,
  caps-lock accidents, `i`→`I`, contractions (English), your own replacements
- **F12 = autocorrect on/off** (configurable). While it is off you can type
  deliberately wrong text or a name like `Koleku`; that text is **never corrected
  afterwards** - AutoC only fixes what you type after switching it back on
- **Backspace right after a fix undoes it** and teaches AutoC the word (great for names and brands)
- Never touches URLs, e-mail addresses, file names, words with digits, ACRONYMS, `camelCase`
- Excluded apps (password managers, terminals ... editable)
- 100 % offline. Nothing you type is stored, logged or sent anywhere.

## Install (Windows 10/11)
1. Download **`AutoC-Windows.zip`** from the [latest release](../../releases/latest).
2. Right-click it → **Extract All...**
3. Double-click **`Install.bat`** (SmartScreen: *More info → Run anyway*).

That's it: AutoC is installed, starts with Windows, gets a **Desktop shortcut** and
starts right away (blue icon near the clock). `Uninstall.bat` removes everything.

Terminal (open a *new* one after installing):
```
autoc-cli correct "i dont know wich langauge"
autoc-cli languages
autoc-cli selftest
```

From source (needs Python 3.9+, run inside the cloned repository):
```
pip install .
python -m autoc
```

## Try it without Windows
```
autoc-cli correct "i dont know wich langauge, teh brwon fox. THe end"
autoc-cli correct --lang de,en "das ist ein Hauss. ich gehe nach hause"
```

## Add any language
Use *Settings → Languages → Add my own dictionary*, or:
```
autoc-cli dict-add xx my-wordlist.txt        # one word per line (optional TAB + count), or a Hunspell .dic
```
Languages without spaces between words (Chinese, Japanese) are not spell-checked; every
other cased script still gets capitalisation fixes.

## How it works
`winhook.py` installs a low-level keyboard hook, translates keys with `ToUnicodeEx` and
feeds characters to `engine.py` (a platform-independent state machine). When a word is
finished and needs a fix, the hook swallows the key, sends Backspaces + the corrected
text with `SendInput`. Spell-checking = words within one edit (delete / insert /
replace / swap) of a known word, ranked by frequency. Word lists are built from
[wordfreq](https://github.com/rspeer/wordfreq) (`tools/build_dictionaries.py`).

## Good to know
- A keyboard hook is what every autocorrect/text-expander does; some antivirus tools
  flag unsigned hook programs. The code is open - read it.
- AutoC cannot see password fields. Use the F12 toggle or the excluded-apps list.
- Word lists are not complete dictionaries: rare words may be "corrected" once -
  press Backspace and AutoC never touches that word again.
- Elevated (admin) windows only receive corrections if AutoC runs as admin too.

## Development
```
pip install -e ".[dev]"
pytest
python tools/build_dictionaries.py    # rebuild word lists
pyinstaller autoc.spec                # build dist/AutoC/ (on Windows)
```

MIT licensed (code). Word lists: CC BY-SA 4.0, see [NOTICE.md](NOTICE.md). Contributions welcome.
