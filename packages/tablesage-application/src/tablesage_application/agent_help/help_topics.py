"""Help topics: the public documentation pages, one topic per page, served to coding agents from the installed app.

Topics are derived from the pages themselves, so there is no manifest to maintain: the ID is the page's path
without `.md`, the title its H1, and the description its first paragraph. Rendering a topic rewrites links to
other pages as `topic:<id>` references and image links as absolute paths to the bundled images.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

SECTION_ORDER = ("getting-started", "concepts", "guides", "reference")
_DESCRIPTION_LIMIT = 220
_LINK = re.compile(r"(!?)\[([^\]]*)\]\(([^)\s]+)((?:\s+\"[^\"]*\")?)\)")
_INLINE_MARKUP = re.compile(r"\*\*|__|`")
_EXTERNAL_PREFIXES = ("http://", "https://", "mailto:", "#")


@dataclass(frozen=True)
class HelpTopic:
    id: str
    title: str
    description: str
    path: Path

    @property
    def section(self) -> str:
        return self.id.split("/", 1)[0] if "/" in self.id else ""


def list_topics(docs_root: Path) -> list[HelpTopic]:
    """Every page under `docs_root`, grouped by section, each section's index first. Hidden folders are skipped."""
    topics = [
        _read_topic(docs_root, page)
        for page in docs_root.rglob("*.md")
        if not any(part.startswith(".") for part in page.relative_to(docs_root).parts)
    ]

    def order(topic: HelpTopic) -> tuple[int, str, bool, str]:
        section = SECTION_ORDER.index(topic.section) if topic.section in SECTION_ORDER else len(SECTION_ORDER)
        folder, _, name = topic.id.rpartition("/")
        return section, folder, name != "index", name

    return sorted(topics, key=order)


def find_topic(docs_root: Path, topic_id: str) -> HelpTopic | None:
    wanted = topic_id.strip().partition("#")[0].removeprefix("topic:").removeprefix("docs/").removesuffix(".md").strip("/")
    return next((topic for topic in list_topics(docs_root) if topic.id == wanted), None)


def render_topic(docs_root: Path, topic: HelpTopic) -> str:
    lines: list[str] = []
    fenced = False
    for line in topic.path.read_text(encoding="utf-8").splitlines():
        if line.lstrip().startswith("```"):
            fenced = not fenced
        lines.append(line if fenced else _LINK.sub(lambda match: _rewrite_link(docs_root, topic, match), line))
    return "\n".join(lines).rstrip() + "\n"


def _rewrite_link(docs_root: Path, topic: HelpTopic, match: re.Match[str]) -> str:
    bang, text, target, title = match.groups()
    if target.startswith(_EXTERNAL_PREFIXES):
        return match.group(0)
    path, _, anchor = target.partition("#")
    resolved = (topic.path.parent / path).resolve()
    if not bang and resolved.suffix == ".md" and resolved.is_relative_to(docs_root.resolve()):
        topic_id = resolved.relative_to(docs_root.resolve()).with_suffix("").as_posix()
        return f"[{text}](topic:{topic_id}{'#' + anchor if anchor else ''}{title})"
    return f"{bang}[{text}]({resolved}{'#' + anchor if anchor else ''}{title})"


def _read_topic(docs_root: Path, page: Path) -> HelpTopic:
    topic_id = page.relative_to(docs_root).with_suffix("").as_posix()
    title = topic_id
    paragraph: list[str] = []
    seen_title = False
    for raw in page.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not seen_title:
            if line.startswith("# "):
                title, seen_title = line[2:].strip(), True
            continue
        if not line:
            if paragraph:
                break
            continue
        # Headings, images, tables, and breadcrumb trails ("[Screen Reference](index.md) › Page") don't describe the page.
        if not paragraph and (line.startswith(("!", "#", "|", "```", "<", ">")) or " › " in line):
            continue
        paragraph.append(line)
    return HelpTopic(topic_id, title, _one_line(" ".join(paragraph)), page)


def _one_line(text: str) -> str:
    text = _INLINE_MARKUP.sub("", _LINK.sub(lambda match: match.group(2), text))
    text = " ".join(text.split())
    if len(text) <= _DESCRIPTION_LIMIT:
        return text
    return text[:_DESCRIPTION_LIMIT].rsplit(" ", 1)[0].rstrip(",;:") + "…"
