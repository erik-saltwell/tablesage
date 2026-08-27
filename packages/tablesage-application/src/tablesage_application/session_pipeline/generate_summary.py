from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from ..llm import PromptName, call_llm_with_prompt


@dataclass(frozen=True)
class GlossaryPromptEntry:
    term: str
    description: str | None


@dataclass(frozen=True)
class SummaryPromptData:
    transcript: str
    glossary: Sequence[GlossaryPromptEntry]


async def generate_summary(transcript: str, glossary: Sequence[GlossaryPromptEntry], model: str) -> str:
    """Generate normalized Markdown from source-agnostic summary prompt data."""
    raw = await call_llm_with_prompt(
        PromptName.SUMMARIZE_SESSION,
        SummaryPromptData(transcript=transcript, glossary=glossary),
        model,
    )
    summary = raw.strip()
    if not summary:
        raise ValueError("The summary model returned an empty response.")
    return f"{summary}\n"
