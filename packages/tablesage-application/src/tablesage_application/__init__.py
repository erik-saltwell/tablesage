from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from . import campaign_recap, players_from_session, session_pipeline
    from .application import Application

__all__ = [
    "Application",
    "campaign_recap",
    "players_from_session",
    "session_pipeline",
]

_SUBMODULES = {"campaign_recap", "players_from_session", "session_pipeline"}


# Loaded on first use (PEP 562): `Application` pulls in the audio and ML stack, which the read-only `tablesage`
# commands for coding agents import this package for but never need.
def __getattr__(name: str) -> Any:
    if name == "Application":
        from .application import Application

        return Application
    if name in _SUBMODULES:
        return importlib.import_module(f".{name}", __name__)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
