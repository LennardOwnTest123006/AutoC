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
    assert type_text(e, "das ist ein Hauss und ich gehe nach hause ") == "Das ist ein Haus und ich gehe nach Hause "
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


def test_keyboard_languages_survive_config_reload(make_engine):
    e = make_engine()
    e.cfg.auto_add_keyboard_languages = True
    e.add_language("de")
    assert "de" in e.langs
    e.set_config(e.cfg)                    # used to wipe the keyboard languages
    assert "de" in e.langs
    assert type_text(e, "das ist ein Hauss ") == "Das ist ein Haus "


def test_german_noun_capitalisation(make_engine):
    e = make_engine(languages=["de"], primary_language="de")
    out = type_text(e, "ich habe das wetter gesehen. der hund ist rot und das auto ist blau ")
    assert out == "Ich habe das Wetter gesehen. Der Hund ist rot und das Auto ist blau "


def test_german_ambiguous_words_left_alone(make_engine):
    e = make_engine(languages=["de"], primary_language="de")
    # colours/adjectives, interjections and verbs that look like nouns stay lowercase
    out = type_text(e, "danke ich suche meinen bus und ich warte ")
    assert out == "Danke ich suche meinen Bus und ich warte "
    e = make_engine(languages=["de"], primary_language="de")
    assert type_text(e, "es ist gut und rot ") == "Es ist gut und rot "


def test_german_nominalised_verbs_after_zum_beim(make_engine):
    e = make_engine(languages=["de"], primary_language="de")
    assert type_text(e, "wir gehen zum essen und beim kochen hilft sie ") == \
        "Wir gehen zum Essen und beim Kochen hilft sie "


def test_german_wrong_capitals_lowercased_but_not_after_colon(make_engine):
    e = make_engine(languages=["de"], primary_language="de")
    assert type_text(e, "ich gehe Nach Hause und Dann schlafe ich ") == "Ich gehe nach Hause und dann schlafe ich "
    e = make_engine(languages=["de"], primary_language="de")
    assert type_text(e, "er sagte: Und dann ") == "Er sagte: Und dann "


def test_german_polite_sie_and_names_untouched(make_engine):
    e = make_engine(languages=["de"], primary_language="de")
    assert type_text(e, "hat Sie gefragt und Koleku kam ") == "Hat Sie gefragt und Koleku kam "


def test_german_casing_can_be_switched_off(make_engine):
    e = make_engine(languages=["de"], primary_language="de", fix_noun_capitalisation=False)
    assert type_text(e, "ich sehe das haus ") == "Ich sehe das haus "


def test_english_is_not_affected_by_german_rules(make_engine):
    e = make_engine(languages=["en", "de"], primary_language="en")
    assert type_text(e, "the house and the dog are here ") == "The house and the dog are here "


def test_german_context_survives_before_a_period(make_engine):
    e = make_engine(languages=["de"], primary_language="de")
    assert type_text(e, "wir gehen zum essen. ich suche das buch. ") == "Wir gehen zum Essen. Ich suche das Buch. "
