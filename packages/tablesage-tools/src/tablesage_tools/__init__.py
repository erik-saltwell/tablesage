from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from . import audio, embeddings, llm, punctuation, speakers, text, transcription

__all__ = ["audio", "embeddings", "llm", "punctuation", "speakers", "text", "transcription"]


def __getattr__(name: str) -> object:
    if name in __all__:
        module = importlib.import_module(f".{name}", __name__)
        globals()[name] = module
        return module
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
