"""Input types for the Scene Log Jinja template; no TableSage imports required."""

import json
from dataclasses import dataclass, field


@dataclass
class SessionAttendee:
    player_name: str
    roles: list[str] = field(default_factory=list)


@dataclass
class GlossaryEntry:
    term: str
    description: str | None = None


@dataclass
class PresentMatters:
    """The previous session's Present Matters, as written by Campaign Matters."""

    current_position: str
    immediate_goals: list[str] = field(default_factory=list)
    present_danger: list[str] = field(default_factory=list)

    def to_passage(self) -> str:
        parts = [f"Current position: {self.current_position}"]
        if self.immediate_goals:
            parts.append("Immediate goals: " + " ".join(self.immediate_goals))
        if self.present_danger:
            parts.append("Present danger: " + " ".join(self.present_danger))
        return "\n".join(parts)


def choose_starting_situation(
    ledger_starting_situation: str | None,
    previous_present_matters: PresentMatters | None,
) -> str | None:
    """Prefer this session's own framing; fall back to where the previous session stopped."""
    if ledger_starting_situation:
        return ledger_starting_situation
    if previous_present_matters is not None:
        return previous_present_matters.to_passage()
    return None


@dataclass
class SceneLogPromptInputs:
    """One session's Ledger entries plus the context needed to read them.

    starting_situation is context only; pass the result of choose_starting_situation.
    Earlier sessions' Open Matters are not Scene Log inputs.
    """

    attendees: list[SessionAttendee]
    glossary: list[GlossaryEntry]
    ledger_entries: list[dict]
    starting_situation: str | None = None

    def to_template_context(self) -> dict[str, object]:
        # One entry per line keeps every field while staying compact and readable.
        rows = ",\n".join("  " + json.dumps(entry, ensure_ascii=False) for entry in self.ledger_entries)
        return {
            "attendees": self.attendees,
            "glossary": self.glossary,
            "ledger": f"[\n{rows}\n]",
            "starting_situation": self.starting_situation,
        }
