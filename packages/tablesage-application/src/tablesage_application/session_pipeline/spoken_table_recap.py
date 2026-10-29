"""Second-person Table Recap presentation from the current Markdown Session Summary."""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import jsonschema
import widelog

from ..llm import PromptName, call_llm_with_prompt
from . import narrative

PROMPT = PromptName.GENERATE_SPOKEN_TABLE_RECAP
CONTRACT_VERSION = 1
CLOSING_HEADING = "As we return"
DANGER_HEADING = "The danger right now"


@dataclass(frozen=True)
class Section:
    heading: str
    bullets: tuple[str, ...]


@dataclass(frozen=True)
class SummaryInput:
    markdown: str
    preamble: str
    sections: tuple[Section, ...]
    position: Section
    danger: Section | None

    def to_template_context(self) -> dict[str, Any]:
        return {
            "summary_markdown": self.markdown,
            "layout": [{"heading": section.heading, "bullet_count": len(section.bullets)} for section in self.sections],
        }


def parse(markdown: str) -> SummaryInput:
    """Accept the deterministic Summary's bullet layout; fail rather than silently lose text."""
    preamble: list[str] = []
    headings: list[str] = []
    bullets: list[list[str]] = []
    for line in markdown.splitlines():
        if not line.strip():
            continue
        if line.startswith("## "):
            heading = line[3:].strip()
            if not heading or heading in headings:
                raise ValueError("Session Summary requires nonempty, unique section headings.")
            headings.append(heading)
            bullets.append([])
        elif not headings:
            preamble.append(line)
        elif line.startswith("- ") and line[2:].strip():
            bullets[-1].append(line[2:].strip())
        else:
            raise ValueError("Table Recap requires a bullet-list Session Summary; regenerate Summary first.")
    if not preamble or not preamble[0].startswith("# ") or not preamble[0][2:].strip():
        raise ValueError("Session Summary requires a title.")
    if any(not values for values in bullets):
        raise ValueError("Session Summary has an empty section.")
    sections = tuple(Section(heading, tuple(values)) for heading, values in zip(headings, bullets, strict=True))
    by_heading = {section.heading: section for section in sections}
    position = by_heading.get(CLOSING_HEADING)
    danger = by_heading.get(DANGER_HEADING)
    if position is None or len(position.bullets) != 1:
        raise ValueError('Session Summary requires one current-position bullet under "As we return".')
    ending = (position, danger) if danger else (position,)
    if sections[-len(ending) :] != ending:
        raise ValueError("Session Summary must end with the current position and optional immediate danger.")
    return SummaryInput(markdown, "\n".join(preamble), sections[: -len(ending)], position, danger)


def _plain_text(value: str) -> str:
    value = value.strip()
    if not value or "\n" in value or "\r" in value or re.match(r"^(?:#{1,6}\s|[-*+]\s|\d+[.)]\s|>)", value):
        raise ValueError("Table Recap text must be nonempty, single-line prose without headings or bullet markers.")
    return value


def validate(source: SummaryInput, result: dict[str, Any]) -> None:
    narrative.validate(PROMPT, result)
    sections = result["sections"]
    if len(sections) != len(source.sections):
        raise ValueError("Table Recap must retain every non-closing Summary section in order.")
    for expected, actual in zip(source.sections, sections, strict=True):
        if actual["heading"] != expected.heading or len(actual["bullets"]) != len(expected.bullets):
            raise ValueError(f'Table Recap must retain heading and bullet count for "{expected.heading}".')
        for bullet in actual["bullets"]:
            _plain_text(bullet)
    _plain_text(result["closing"])


def _escape(value: str) -> str:
    # Models may preserve the Summary's literal Markdown escapes. Normalize before escaping once.
    value = re.sub(r"\\([\\`*_[\]<>])", r"\1", _plain_text(value))
    return re.sub(r"([\\`*_[\]<>])", r"\\\1", value)


def render(source: SummaryInput, result: dict[str, Any]) -> str:
    validate(source, result)
    lines = [source.preamble, ""]
    for section in result["sections"]:
        lines.extend([f"## {section['heading']}", ""])
        lines.extend(f"- {_escape(bullet)}" for bullet in section["bullets"])
        lines.append("")
    lines.extend([f"## {CLOSING_HEADING}", "", _escape(result["closing"]), ""])
    return "\n".join(lines)


async def generate(
    source: SummaryInput,
    model: str,
    timeout: float,
    model_options: Mapping[str, Any],
    *,
    validation_retries: int,
    folder: Path,
) -> str:
    """Retry structural failures only; transport and filesystem failures propagate immediately."""
    if validation_retries not in (0, 1):
        raise ValueError("Table Recap validation retries must be 0 or 1.")
    with widelog.wide_event(op="generate_spoken_table_recap", model=model) as log:
        for attempt in range(validation_retries + 1):
            raw = await call_llm_with_prompt(
                PROMPT, source, model, response_model=narrative.schema(PROMPT), timeout=timeout, model_options=model_options
            )
            narrative.atomic_write(folder / ".generation-records" / PROMPT.value / f"{uuid.uuid4().hex}.json", raw.encode("utf-8"))
            try:
                result = json.loads(raw)
                markdown = render(source, result)
            except (ValueError, jsonschema.ValidationError) as exc:
                log.set(attempt=attempt + 1, validation_error=str(exc))
                if attempt == validation_retries:
                    raise ValueError(f"Table Recap failed validation after {attempt + 1} attempt(s): {exc}") from exc
            else:
                log.set(attempts=attempt + 1, section_count=len(source.sections), failed=False)
                return markdown
    raise AssertionError("Table Recap generation did not return or raise.")


def persist(folder: Path, markdown: str) -> None:
    if not markdown.strip():
        raise ValueError("Table Recap cannot be empty.")
    for name in ("table_recap.md", "table_recap.json"):
        path = folder / name
        if path.is_file():
            content = path.read_bytes()
            digest = hashlib.sha256(content).hexdigest()[:16]
            archived = folder / "legacy" / "narrative" / digest / name
            if not archived.exists():
                narrative.atomic_write(archived, content)
    narrative.persist(folder, "table_recap", {"table_recap.md": markdown.encode("utf-8")})
    # The legacy structured companion does not represent the new Markdown-only artifact.
    (folder / "table_recap.json").unlink(missing_ok=True)
