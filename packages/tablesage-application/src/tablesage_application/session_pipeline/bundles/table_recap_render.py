"""Render a validated Table Recap as player-facing Markdown."""

from typing import Any


def render_markdown(recap: dict[str, Any], title: str = "Table Recap") -> str:
    lines = [f"# {title}", "", recap["orientation"]]
    if recap["threads"]:
        lines += ["", "## Open threads", ""]
        lines += [f"- **{t['label']}:** {t['text']}" for t in recap["threads"]]
    return "\n".join(lines) + "\n"
