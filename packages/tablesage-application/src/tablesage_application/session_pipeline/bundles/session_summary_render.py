"""Render validated Summary JSON; generation supplies scene bullets only."""

from typing import Any

KINDS = ["active_goal", "unresolved_mystery", "outstanding_obligation", "developing_threat", "available_opportunity"]
LABELS = ["Active Goals", "Unresolved Mysteries", "Outstanding Obligations", "Developing Threats", "Available Opportunities"]


def render_markdown(summary: dict[str, Any], title: str = "Session Summary") -> str:
    lines = [f"# {title}", "", "## Opening Situation", "", summary["opening_situation"], "", "## Scenes"]
    for scene in summary["scenes"]:
        lines += ["", f"### {scene['title']}", ""]
        lines += [f"- {bullet}" for bullet in scene["bullets"]]
    lines += ["", "## Endcap", "", "### End Situation", "", summary["endcap"]["end_situation"]]
    for kind, label in zip(KINDS, LABELS, strict=True):
        entries = [m for m in summary["endcap"]["session_matters"] if m["kind"] == kind]
        if entries:
            lines += ["", f"### {label}", ""]
            lines += [f"- **{m['matter']}:** {m['text']}" for m in entries]
    if not summary["endcap"]["session_matters"]:
        lines += ["", "None open."]
    return "\n".join(lines) + "\n"
