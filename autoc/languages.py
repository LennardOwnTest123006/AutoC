"""Language codes and names (ISO 639-1/-3 as used by the bundled word lists)."""

NAMES = {
    "ar": "Arabic", "bg": "Bulgarian", "bn": "Bengali", "ca": "Catalan",
    "cs": "Czech", "da": "Danish", "de": "German", "el": "Greek",
    "en": "English", "es": "Spanish", "fa": "Persian", "fi": "Finnish",
    "fil": "Filipino", "fr": "French", "he": "Hebrew", "hi": "Hindi",
    "hu": "Hungarian", "id": "Indonesian", "is": "Icelandic", "it": "Italian",
    "lt": "Lithuanian", "lv": "Latvian", "mk": "Macedonian", "ms": "Malay",
    "nb": "Norwegian", "nl": "Dutch", "pl": "Polish", "pt": "Portuguese",
    "ro": "Romanian", "ru": "Russian", "sh": "Serbo-Croatian", "sk": "Slovak",
    "sl": "Slovenian", "sv": "Swedish", "ta": "Tamil", "tr": "Turkish",
    "uk": "Ukrainian", "ur": "Urdu", "vi": "Vietnamese",
}

# Windows primary language id (LANGID & 0x3FF) -> code
LANGID = {
    0x01: "ar", 0x02: "bg", 0x03: "ca", 0x05: "cs", 0x06: "da", 0x07: "de",
    0x08: "el", 0x09: "en", 0x0A: "es", 0x0B: "fi", 0x0C: "fr", 0x0D: "he",
    0x0E: "hu", 0x0F: "is", 0x10: "it", 0x13: "nl", 0x14: "nb", 0x15: "pl",
    0x16: "pt", 0x18: "ro", 0x19: "ru", 0x1A: "sh", 0x1B: "sk", 0x1C: "sl",
    0x1D: "sv", 0x1F: "tr", 0x20: "ur", 0x21: "id", 0x22: "uk", 0x29: "fa",
    0x2A: "vi", 0x2F: "mk", 0x26: "lv", 0x27: "lt", 0x39: "hi", 0x45: "bn",
    0x49: "ta", 0x3E: "ms", 0x64: "fil",
}


def name(code: str) -> str:
    return NAMES.get(code, code)
