"""Small Unicode helpers shared by the engine."""
import unicodedata

SENTENCE_END = set(".!?…。！？؟‼⁇")
APOSTROPHES = "'’ʼ"


def is_word_char(ch: str) -> bool:
    return unicodedata.category(ch)[0] in "LM"


def is_digit(ch: str) -> bool:
    return unicodedata.category(ch)[0] == "N"


def lower(word: str, lang: str = "") -> str:
    if lang in ("tr", "az"):
        word = word.replace("İ", "i").replace("I", "ı")
    return word.lower()


def upper_first(word: str, lang: str = "") -> str:
    if not word:
        return word
    first = word[0]
    if lang in ("tr", "az") and first == "i":
        up = "İ"
    else:
        up = first.upper()
    if len(up) != 1:  # e.g. German sharp s: keep as is
        return word
    return up + word[1:]


def norm_apostrophe(word: str) -> str:
    for a in APOSTROPHES[1:]:
        word = word.replace(a, "'")
    return word


def apply_case(model: str, word: str, lang: str = "") -> str:
    """Give `word` the capitalisation pattern of `model` (typed text)."""
    if len(model) > 1 and model.isupper():
        return word.upper()
    if model[:1].isupper():
        return upper_first(word, lang)
    return word
