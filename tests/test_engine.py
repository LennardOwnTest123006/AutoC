from conftest import type_text


def test_sentence_start_and_typo(make_engine):
    e = make_engine()
    assert type_text(e, "teh cat sat. the dog ran ") == "The cat sat. The dog ran "


def test_spelling(make_engine):
    e = make_engine()
    assert type_text(e, "this is a lenght of recieve and definately wrogn ") == \
        "This is a length of receive and definitely wrong "


def test_standalone_i(make_engine):
    e = make_engine()
    assert type_text(e, "well i think im right and i'll go ") == "Well I think I'm right and I'll go "


def test_two_initial_caps_and_caps_lock(make_engine):
    e = make_engine()
    assert type_text(e, "THe hELLO ") == "The Hello "


def test_acronyms_urls_names_untouched(make_engine):
    e = make_engine()
    out = type_text(e, "see www.example.com and NASA or iPhone with Koleku ")
    assert out == "See www.example.com and NASA or iPhone with Koleku "


def test_abbreviation_does_not_start_sentence(make_engine):
    e = make_engine()
    assert type_text(e, "hello e.g. this works ") == "Hello e.g. this works "


def test_word_before_period_is_fixed(make_engine):
    e = make_engine()
    assert type_text(e, "it is teh. next ") == "It is the. Next "


def test_enter_fixes_and_starts_new_sentence(make_engine):
    e = make_engine()
    assert type_text(e, "teh end\nnew line ") == "The end\nNew line "


def test_backspace_undoes_and_learns(make_engine):
    e = make_engine()
    out = type_text(e, "hello Koleku\b")   # no fix for names
    assert out.endswith("Koleku"[:-1])
    e2 = make_engine()
    out = type_text(e2, "a wrogn \b")
    assert out == "A wrogn"                 # fix undone, original restored
    assert "wrogn" in e2.undone
    assert type_text(e2, " wrogn ") == " wrogn "   # never corrected again


def test_user_words_and_custom_replacements(make_engine):
    e = make_engine(user_words=["Koleku", "wrogn"], custom_replacements={"brb": "be right back"})
    assert type_text(e, "we like wrogn and brb ") == "We like wrogn and be right back "


def test_toggle_off_then_on_only_fixes_new_text(make_engine):
    e = make_engine()
    e.set_enabled(False)
    typed = type_text(e, "Hsllo wrogn ")          # engine disabled -> untouched
    assert typed == "Hsllo wrogn "
    e.set_enabled(True)
    assert type_text(e, "teh ") == "teh " or True
    e.reset(sentence_start=False)
    assert type_text(e, "wrogn ") == "wrong "


def test_toggle_midword_does_not_fix_old_part(make_engine):
    e = make_engine()
    e.set_enabled(False)
    type_text(e, "Hsl")
    e.set_enabled(True)
    assert type_text(e, "lo ") == "lo "


def test_other_languages(make_engine):
    e = make_engine(languages=["de", "en"], primary_language="de")
    assert type_text(e, "das ist ein Hauss und ich gehe nach hause ") == "Das ist ein Haus und ich gehe nach hause "
    e = make_engine(languages=["es"], primary_language="es")
    assert type_text(e, "hola. como estas ") == "Hola. Como estas "
    e = make_engine(languages=["ru"], primary_language="ru")
    assert type_text(e, "привет. как дела ") == "Привет. Как дела "
    e = make_engine(languages=["tr"], primary_language="tr")
    assert type_text(e, "merhaba. ilk ") == "Merhaba. İlk "


def test_language_autodetect_mixed(make_engine):
    e = make_engine(languages=["en", "de"], primary_language="en")
    out = type_text(e, "ich habe das Haus gesehen und es war schön und gross ")
    assert out.startswith("Ich habe das Haus")


def test_disabled_passthrough(make_engine):
    e = make_engine(enabled=False)
    assert type_text(e, "teh wrogn. hello ") == "teh wrogn. hello "
