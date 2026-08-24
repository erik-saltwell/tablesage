from __future__ import annotations

from enum import StrEnum
from importlib.resources import files

_RESOURCE_PACKAGE = __name__.rsplit(".", maxsplit=1)[0]


class PromptName(StrEnum):
    """Each member names a subdirectory of `_prompts/` holding a `system.md` + `template.j2` pair."""

    SUMMARIZE_SESSION = "summarize_session"
    PROPOSE_SPEAKERS = "propose_speakers"
    CLASSIFY_BACKCHANNELS = "classify_backchannels"


def read_system_prompt(name: PromptName) -> str:
    return files(_RESOURCE_PACKAGE).joinpath(name.value, "system.md").read_text("utf-8")


def read_prompt_template(name: PromptName) -> str:
    return files(_RESOURCE_PACKAGE).joinpath(name.value, "template.j2").read_text("utf-8")
