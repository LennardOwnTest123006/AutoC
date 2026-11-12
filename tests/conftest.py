import pytest

from autoc.config import Config
from autoc.engine import Engine
from autoc.simulate import type_text  # noqa: F401


@pytest.fixture
def make_engine():
    def _make(**kw):
        cfg = Config(auto_add_keyboard_languages=False, **kw)
        e = Engine(cfg)
        e.reset(sentence_start=True)
        return e
    return _make
