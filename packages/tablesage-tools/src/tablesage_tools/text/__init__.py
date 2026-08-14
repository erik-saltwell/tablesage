from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .cleaning import clean_multiple_texts, clean_text_for_evaluation
    from .punctuation import punctuate_text

__all__ = ["clean_multiple_texts", "clean_text_for_evaluation", "punctuate_text"]

_MODULE_BY_NAME = {
    "clean_multiple_texts": "cleaning",
    "clean_text_for_evaluation": "cleaning",
    "punctuate_text": "punctuation",
}


def __getattr__(name: str) -> object:
    module_name = _MODULE_BY_NAME.get(name)
    if module_name is None:
        msg = f"module {__name__!r} has no attribute {name!r}"
        raise AttributeError(msg)
    module = importlib.import_module(f".{module_name}", __name__)
    value = getattr(module, name)
    globals()[name] = value
    return value
