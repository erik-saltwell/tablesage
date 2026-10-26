"""Input types for the Ledger Jinja template; no TableSage imports required."""

import json
from dataclasses import asdict, dataclass, field


@dataclass
class SessionAttendee:
    player_name: str
    roles: list[str] = field(default_factory=list)


@dataclass
class GlossaryEntry:
    term: str
    description: str | None = None


@dataclass
class TranscriptUtterance:
    speaker: str
    text: str


@dataclass
class LedgerPromptInputs:
    """Current-session evidence and metadata, with optional bootstrap/retry input.

    Supply starting_context only when bootstrapping without prior continuity.
    Previous Session Endcaps and Table Recaps are not Ledger inputs.
    """

    attendees: list[SessionAttendee]
    glossary: list[GlossaryEntry]
    session_utterances: list[TranscriptUtterance]
    starting_context: list[TranscriptUtterance] | None = None
    validation_feedback: str | None = None
    rejected_candidate: str | None = None

    def to_template_context(self) -> dict[str, object]:
        """Keep the existing template's text/JSON boundary and formatting."""
        return {
            "attendees": self.attendees,
            "glossary": self.glossary,
            "session_utterances": json.dumps(
                [asdict(row) for row in self.session_utterances],
                ensure_ascii=False,
                indent=2,
            ),
            "starting_context": (
                json.dumps(
                    [asdict(row) for row in self.starting_context],
                    ensure_ascii=False,
                    indent=2,
                )
                if self.starting_context is not None
                else None
            ),
            "validation_feedback": self.validation_feedback,
            "rejected_candidate": self.rejected_candidate or "",
        }
