from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import widelog
from tablesage_tools.model import Transcript, Utterance
from tablesage_tools.speakers import UNASSIGNED_SPEAKER

from ..paths import ARTIFACTS, ArtifactName
from .remove_backchannels import remove_backchannels
from .transcript_review import load_review_transcript


class Stage(Enum):
    """A `clean_transcript` pipeline stage, reported to `on_progress`.

    Both stages are single opaque calls -- `on_progress` fires with `total=0` on entry
    (indeterminate: show the stage label, not a moving bar) and `(1, 1)` on completion.
    """

    REMOVING_BACKCHANNELS = "removing_backchannels"
    ASSIGNING_ROLES = "assigning_roles"


OnProgress = Callable[[Stage, int, int], None]


@dataclass(frozen=True)
class CleanTranscriptResult:
    """The outcome of a Clean Transcript run, for the caller to report to the user."""

    utterance_count: int
    removed_count: int


def can_clean_transcript(session_folder: Path) -> tuple[bool, str | None]:
    if not (session_folder / ARTIFACTS[ArtifactName.TRANSCRIPT].filename).is_file():
        return False, "Transcribe the session first."
    return True, None


def _report(on_progress: OnProgress | None, stage: Stage, completed: int, total: int) -> None:
    if on_progress is not None:
        on_progress(stage, completed, total)


def _apply_roles(transcript: Transcript, role_names: dict[str, str]) -> Transcript:
    """Return a copy of `transcript` with each assigned utterance's speaker replaced by its role name.

    An utterance whose speaker has no known role (an attendee without a role, or a role_names
    lookup miss) keeps its player name. `UNASSIGNED_SPEAKER` is never renamed -- there's no
    attendee, and so no role, behind it.
    """

    def _with_role(utterance: Utterance) -> Utterance:
        if utterance.speaker == UNASSIGNED_SPEAKER:
            return utterance
        return utterance.model_copy(update={"speaker": role_names.get(utterance.speaker, utterance.speaker)})

    return Transcript(utterances=[_with_role(utterance) for utterance in transcript.utterances])


def render_role_transcript_text(session_folder: Path) -> str:
    """Render the completed `role_transcript.json` as role-attributed text for Ledger generation.

    Unlike the machine/reviewed transcript's rendering, no role lookup happens here -- the speaker
    field in `role_transcript.json` already holds the role name (or `UNASSIGNED_SPEAKER`), baked
    in by `clean_transcript`.
    """
    transcript = Transcript.load(session_folder / ARTIFACTS[ArtifactName.ROLE_TRANSCRIPT].filename)
    return "\n\n".join(_render_utterance(utterance) for utterance in transcript.utterances) + "\n"


def _render_utterance(utterance: Utterance) -> str:
    text = utterance.punctuated_text if utterance.punctuated_text is not None else utterance.text
    return f"**{utterance.speaker}** - {text}"


def clean_transcript(
    session_folder: Path,
    max_words: int,
    question_timeout: float,
    llm_model_lite: str,
    role_names: dict[str, str],
    on_progress: OnProgress | None = None,
) -> CleanTranscriptResult:
    """Remove backchannels from and assign roles to a session's preferred transcript, writing `role_transcript.json`.

    Reads the completed Manual Review when present, otherwise the machine transcript (see
    `load_review_transcript`) -- neither source is modified. The result is a new, independent
    artifact: `transcript.json` and `transcript_reviewed.json` are untouched by this step.
    Regenerating `role_transcript.json` invalidates any Ledger and Summary built from the previous
    copy, since both are derived from it.
    """
    transcript = load_review_transcript(session_folder)
    original_count = len(transcript.utterances)

    async def _run() -> Transcript:
        _report(on_progress, Stage.REMOVING_BACKCHANNELS, 0, 0)
        cleaned = await remove_backchannels(transcript, max_words, llm_model_lite, question_timeout)
        _report(on_progress, Stage.REMOVING_BACKCHANNELS, 1, 1)
        return cleaned

    with widelog.wide_event(op="clean_transcript", session_folder=str(session_folder)) as log:
        cleaned = asyncio.run(_run())

        _report(on_progress, Stage.ASSIGNING_ROLES, 0, 0)
        role_transcript = _apply_roles(cleaned, role_names)
        _report(on_progress, Stage.ASSIGNING_ROLES, 1, 1)

        target = session_folder / ARTIFACTS[ArtifactName.ROLE_TRANSCRIPT].filename
        temporary = target.with_name(f".{target.stem}.tmp{target.suffix}")
        try:
            role_transcript.save(temporary)
            temporary.replace(target)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise

        for name in (ArtifactName.LEDGER, ArtifactName.SUMMARY):
            (session_folder / ARTIFACTS[name].filename).unlink(missing_ok=True)

        removed_count = original_count - len(cleaned.utterances)
        log.set(utterance_count=len(cleaned.utterances), removed_count=removed_count)
        return CleanTranscriptResult(utterance_count=len(cleaned.utterances), removed_count=removed_count)
