"""Platform-independent autocorrect state machine.

Feed it what the user types (`key_char`, `key_backspace`, `key_special`); when a
word is finished and needs fixing it returns an `Action`: the caller must swallow
the key just typed, press Backspace `backspaces` times, type `text` and then
optionally press `then` ("enter" / "tab").
"""
from collections import deque
from dataclasses import dataclass
from typing import Optional

from . import dictionary as dictmod
from .config import Config
from .textutil import (SENTENCE_END, apply_case, is_digit, is_word_char, lower,
                       norm_apostrophe, upper_first)

# Boundary characters that trigger a correction right away.  '.' ':' '/' '@' ...
# are deliberately not here: they may be part of URLs, e-mails and file names.
TRIGGERS = set(" \t\n\r ,;!?)]}\"”»…。！？؟،")
CODE_CHARS = set("@/\\_#=<>{}|~^:")
ABBREVIATIONS = {"mr", "mrs", "ms", "dr", "prof", "sr", "jr", "st", "vs", "etc", "inc",
                 "ltd", "no", "fig", "eg", "ie", "z", "d", "bzw", "ca", "usw", "u", "s",
                 "nr", "tel", "approx", "dept", "est", "min", "max"}
SHORT_FREQUENT_RANK = 3000
FOREIGN_TRUST_RANK = 25000     # a word from another language only counts as known if it is common there
CAPITALISED_NOUN_LANGS = {"de"}   # nouns are capitalised: mid-sentence Title Case is not a name


@dataclass
class Action:
    backspaces: int
    text: str
    then: Optional[str] = None


class Engine:
    def __init__(self, config: Config, store: Optional[dictmod.DictionaryStore] = None):
        self.store = store or dictmod.DictionaryStore()
        self.layout_lang = ""
        self.recent = deque(maxlen=24)   # per-word language votes
        self.undone = []                  # words the user rejected (to persist)
        self._repl_cache = {}
        self.extra_langs = []             # languages of the installed keyboards (survive set_config)
        self.set_config(config)
        self.reset(sentence_start=True)

    # ---------------------------------------------------------------- config
    def set_config(self, config: Config):
        self.cfg = config
        self.user_words = {lower(w) for w in config.user_words}
        self.custom = {k.lower(): v for k, v in config.custom_replacements.items()}
        extra = self.extra_langs if config.auto_add_keyboard_languages else []
        self.langs = list(dict.fromkeys((config.languages or ["en"]) + extra))

    def add_language(self, code: str):
        if code and code in dictmod.available_languages() and code not in self.extra_langs:
            self.extra_langs.append(code)
            if self.cfg.auto_add_keyboard_languages and code not in self.langs:
                self.langs.append(code)

    def set_layout_language(self, code: str):
        self.layout_lang = code or ""
        self.add_language(code)

    def ready(self) -> bool:
        for c in self.langs:
            self.store.get(c)
        return self.store.ready(self.langs)

    def preload(self):
        for code in self.langs:
            self.store.get(code)

    # ----------------------------------------------------------------- state
    def reset(self, sentence_start: bool = False):
        self.word = []
        self.sentence_start = sentence_start
        self.pending_end = False
        self.token_code = False
        self.deferred = None     # word finished by '.', fix decided when a space follows
        self.last = None         # (original, corrected, boundary) of the latest fix
        self.prev_word = ""

    def set_enabled(self, enabled: bool):
        """F12 toggle.  Text typed while off is never corrected afterwards:
        switching on (or off) starts from a clean slate."""
        self.cfg.enabled = enabled
        self.reset(sentence_start=False)

    def invalidate(self):
        """Something we cannot follow happened (dead key, IME, paste): leave this token alone."""
        self.word = []
        self.token_code = True
        self.deferred = None
        self.last = None

    # ---------------------------------------------------------------- events
    def key_char(self, ch: str) -> Optional[Action]:
        if ch in "'\u2019\u02bc" and self.word:
            self.word.append("'")
            return None
        if is_word_char(ch) or is_digit(ch):
            if self.pending_end or self.deferred:
                self.token_code = True      # "example.com", "e.g" -> not a sentence end
                self.pending_end = False
                self.deferred = None
            self.last = None
            self.word.append(ch)
            return None
        return self._boundary(ch)

    def key_special(self, name: str) -> Optional[Action]:
        """'enter' / 'tab' are boundaries that the caller must re-send as real keys."""
        return self._boundary("\n" if name == "enter" else "\t", then=name)

    def key_backspace(self) -> Optional[Action]:
        if self.last and self.cfg.undo_with_backspace and not self.word:
            orig, fixed, tail = self.last
            self.last = None
            self._remember_undo(orig)
            self.word = list(orig)
            self.token_code = False
            return Action(len(fixed) + len(tail), orig)
        self.last = None
        if self.word:
            self.word.pop()
        elif self.deferred:
            self.deferred = None
        else:
            self.sentence_start = False
            self.pending_end = False
        return None

    # -------------------------------------------------------------- internal
    def _boundary(self, ch: str, then: Optional[str] = None) -> Optional[Action]:
        action = None
        word = "".join(self.word)
        self.word = []
        if ch.isspace() and self.deferred:                 # word + '.' + whitespace
            dword, dot, was_start = self.deferred
            self.deferred = None
            saved, self.sentence_start = self.sentence_start, was_start
            fixed = self._fix(dword)
            self.sentence_start = saved
            if fixed is not None:
                tail = dot if then else dot + ch
                action = self._make(len(dword) + len(dot), dword, fixed, tail, then)
        elif word:
            if ch == "." and not self.token_code:
                self.deferred = (word, ch, self.sentence_start)
            elif ch in TRIGGERS:
                fixed = self._fix(word)
                if fixed is not None:
                    action = self._make(len(word), word, fixed, "" if then else ch, then)
        self._track(ch, word)
        if action is None:
            self.last = None
        return action

    def _make(self, screen_len, orig, fixed, tail, then):
        self.prev_word = fixed
        self.last = None if then else (orig, fixed, tail)
        return Action(screen_len, fixed + tail, then)

    def _track(self, ch, word):
        if word:
            self.sentence_start = False
            if self.last is None:
                self.prev_word = word
        if ch.isspace():
            if ch in "\n\r":
                self.sentence_start, self.pending_end = True, False
            elif self.pending_end:
                short = lower(self.prev_word)
                if not (len(short) == 1 or short in ABBREVIATIONS or "." in self.prev_word):
                    self.sentence_start = True
                self.pending_end = False
            self.token_code = False
            self.deferred = None if not word else self.deferred
        elif ch in SENTENCE_END:
            self.pending_end = True
        elif ch in "\u00bf\u00a1\"(\u201c\u00ab[\u2018":
            pass
        elif ch in CODE_CHARS:
            self.token_code = True
            self.pending_end = False
        else:
            self.pending_end = False

    def _remember_undo(self, word):
        w = lower(norm_apostrophe(word))
        self.user_words.add(w)
        if w not in self.undone:
            self.undone.append(w)

    # ----------------------------------------------------------- correction
    def _active_lang(self):
        scores = {c: 0.0 for c in self.langs}
        for votes in self.recent:
            for c, v in votes.items():
                if c in scores:
                    scores[c] += v
        if self.layout_lang in scores:
            scores[self.layout_lang] += 3
        primary = self.cfg.primary_language
        return max(scores, key=lambda c: (scores[c], c == primary, c == self.layout_lang))

    def _known(self, word_lc):
        """{language: rank} for every enabled language whose word list contains the word."""
        out = {}
        for c in self.langs:
            d = self.store.get(c)
            if d and word_lc in d:
                out[c] = d.rank[word_lc]
        return out

    def _is_known(self, found, lang):
        """Known in the active language, or common (not just a stray entry) in another one."""
        if lang in found:
            return True
        return any(r < FOREIGN_TRUST_RANK for r in found.values())

    def _fix(self, original: str) -> Optional[str]:
        cfg = self.cfg
        if not cfg.enabled or self.token_code or any(is_digit(c) for c in original):
            return None
        core = original.rstrip("'")
        suffix = original[len(core):]
        core = core.lstrip("'")
        if not core:
            return None
        lang = self._active_lang()
        word_lc = lower(norm_apostrophe(core), lang)
        found = self._known(word_lc)
        if found and len(word_lc) >= 3:     # evidence for the language: weighted by how common the word is there
            w = {c: 1.0 / (r + 50) for c, r in found.items()}
            tot = sum(w.values())
            self.recent.append({c: v / tot for c, v in w.items()})
        known_in = self._is_known(found, lang)
        new = core

        rep = None
        if cfg.use_replacements:
            rep = self.custom.get(word_lc)
            if rep is None and lang == "en" and word_lc not in self.user_words:
                rep = self._table("en").get(word_lc)
                if word_lc == "i" and (core != "i" or not cfg.fix_standalone_i):
                    rep = None
        if rep is not None:
            new = rep if (core.isupper() and len(core) > 1 and rep != rep.lower()) else apply_case(core, rep, lang)
        elif known_in or word_lc in self.user_words:
            new = self._case_fixes(core, word_lc, lang)
        elif cfg.fix_spelling and self._eligible(core, lang):
            new = self._spell(core, word_lc, lang) or core

        if cfg.fix_sentence_start and self.sentence_start and new[:1].islower():
            new = upper_first(new, lang)
        new = new + suffix
        return None if new == original else new

    def _table(self, lang):
        if lang not in self._repl_cache:
            self._repl_cache[lang] = dictmod.load_replacements(lang)
        return self._repl_cache[lang]

    def _eligible(self, core, lang):
        if len(core) < 4 or core.isupper():
            return False                          # too short / acronym
        if any(c.isupper() for c in core[1:]):
            return False                          # camelCase, iPhone
        if core[:1].isupper() and not self.sentence_start and lang not in CAPITALISED_NOUN_LANGS:
            return False                          # probably a name
        return True

    def _spell(self, core, word_lc, lang):
        d = self.store.get(lang)
        cands = d.candidates(word_lc) if d else []
        if not cands:
            return None
        return upper_first(cands[0], lang) if core[:1].isupper() else cands[0]

    def _case_fixes(self, core, word_lc, lang):
        cfg = self.cfg
        if len(core) >= 3 and core[:2].isupper() and core[2:].islower() and cfg.fix_two_initial_caps:
            d = self.store.get(lang)
            r = d.rank.get(word_lc, 10**9) if d else 10**9
            if len(core) >= 4 or r < SHORT_FREQUENT_RANK:
                return upper_first(word_lc, lang)
        if len(core) >= 4 and core[0].islower() and core[1:].isupper() and cfg.fix_caps_lock:
            return upper_first(word_lc, lang)
        return core
