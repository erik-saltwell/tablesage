"""Deterministic, read-aloud Markdown from a Session's filtered Matters publication."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Iterable
from datetime import date
from importlib.resources import files
from pathlib import Path
from typing import Any

import jinja2

from . import narrative, post_session_matters

FILENAME = "summary.md"
TEMPLATE_PATH = Path(__file__).with_suffix(".j2")


def _sentence(value: str) -> str:
    text = " ".join(value.split())
    if not text:
        raise ValueError("Session Summary requires nonempty read-aloud text.")
    if not text.rstrip("\"'”’)]}").endswith((".", "?", "!", "…")):
        text += "."
    return text


# Read order, with the primary field each category is read from.
SECTIONS: tuple[tuple[str, str, str], ...] = (
    ("historical_matters", "developments", "title"),
    ("historical_matters", "revelations", "text"),
    ("historical_matters", "new_assets", "name"),
    ("open_matters", "goals", "title"),
    ("open_matters", "goal_impediments", "title"),
    ("open_matters", "opportunities", "title"),
    ("open_matters", "mysteries", "title"),
    ("open_matters", "obligations", "title"),
    ("open_matters", "brewing_troubles", "title"),
)

Prepared = dict[str, list[str]]


def _template_source() -> str:
    return files(__package__).joinpath(TEMPLATE_PATH.name).read_text("utf-8")


def prepare(document: dict[str, Any]) -> Prepared:
    """Primary read-aloud text per section, in read order; omit exact repeated sentences."""
    post_session_matters.validate(document)
    seen: set[str] = set()
    present = document["present_matters"]
    orientation = {_sentence(value).casefold() for value in [present["current_position"], *present["present_danger"]]}

    def unique(values: Iterable[str], *, returning: bool = False) -> list[str]:
        sentences = []
        for value in values:
            sentence = _sentence(value)
            key = sentence.casefold()
            if key in seen or (not returning and key in orientation):
                continue
            seen.add(key)
            sentences.append(sentence)
        return sentences

    prepared = {section: unique(item[field] for item in document[group][section]) for group, section, field in SECTIONS}
    prepared["current_position"] = unique([present["current_position"]], returning=True)
    prepared["present_danger"] = unique(present["present_danger"], returning=True)
    return prepared


def render(prepared: Prepared, *, campaign_name: str, session_date: date | None, session_cue: str) -> str:
    campaign_name = " ".join(campaign_name.split())
    if not campaign_name:
        raise ValueError("Session Summary requires a Campaign name.")
    session_cue = " ".join(session_cue.split())
    if not session_cue:
        raise ValueError("Session Summary requires a Session cue.")
    if len(prepared["current_position"]) != 1:
        raise ValueError("Session Summary requires exactly one current position.")
    # Keep source Markdown punctuation literal within read-aloud text.
    escaped = {section: [re.sub(r"([\\`*_[\]<>])", r"\\\1", _sentence(value)) for value in values] for section, values in prepared.items()}
    environment = jinja2.Environment(undefined=jinja2.StrictUndefined, trim_blocks=True, lstrip_blocks=True, autoescape=False)
    markdown = environment.from_string(_template_source()).render(
        campaign_name=campaign_name,
        session_date=session_date.isoformat() if session_date is not None else None,
        session_cue=session_cue,
        historical_matters={section: escaped[section] for group, section, _ in SECTIONS if group == "historical_matters"},
        open_matters={section: escaped[section] for group, section, _ in SECTIONS if group == "open_matters"},
        present_matters={"current_position": escaped["current_position"][0], "present_danger": escaped["present_danger"]},
    )
    if not markdown.strip():
        raise ValueError("Session Summary template produced empty Markdown.")
    return markdown.rstrip() + "\n"


def persist(folder: Path, markdown: str) -> None:
    if not markdown.strip():
        raise ValueError("Session Summary cannot be empty.")
    # Preserve any previous summary contract before replacing the readable output.
    for name in (FILENAME, "summary.json", ".summary-inputs.json", "summary.phrasing.json"):
        path = folder / name
        if path.is_file():
            content = path.read_bytes()
            digest = hashlib.sha256(content).hexdigest()[:16]
            archived = folder / "legacy" / "narrative" / digest / name
            if not archived.exists():
                narrative.atomic_write(archived, content)
    narrative.persist(folder, "summary", {FILENAME: markdown.encode("utf-8")})
    # Retired by the move to read-aloud wording in the Matters prompts; archived above.
    (folder / "summary.phrasing.json").unlink(missing_ok=True)
