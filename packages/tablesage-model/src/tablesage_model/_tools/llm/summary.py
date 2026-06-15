from __future__ import annotations

from ...model import GlossaryEntry
from ...model.discourse import Discourse


async def _call_llm(prompt: str, model: str) -> str:
    import litellm

    response = await litellm.acompletion(model=model, messages=[{"role": "user", "content": prompt}])
    return response["choices"][0]["message"]["content"]


def _render_glossary(glossary: tuple[GlossaryEntry, ...]) -> str:
    if not glossary:
        return ""
    lines = [f"- {entry.term}: {entry.description}" for entry in glossary]
    return "Proper nouns in this campaign:\n" + "\n".join(lines)


def _render_discourse(discourse: Discourse) -> str:
    return "\n".join(f"{u.speaker}: {u.text}" for u in discourse.utterances)


def _build_prompt(discourse: Discourse, glossary: tuple[GlossaryEntry, ...]) -> str:
    parts: list[str] = []
    glossary_block = _render_glossary(glossary)
    if glossary_block:
        parts.append(glossary_block)
    parts.append("Transcript:\n" + _render_discourse(discourse))
    parts.append(
        "Write a short, player-ready recap of the session above in markdown. Use the proper nouns from the glossary exactly as spelled."
    )
    return "\n\n".join(parts)


async def generate_summary(discourse: Discourse, glossary: tuple[GlossaryEntry, ...], model: str) -> str:
    prompt = _build_prompt(discourse, glossary)
    return await _call_llm(prompt, model)
