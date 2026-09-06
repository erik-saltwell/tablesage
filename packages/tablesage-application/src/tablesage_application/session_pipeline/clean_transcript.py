from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import widelog
from tablesage_tools.backchannels import find_backchannel_candidates
from tablesage_tools.model import Transcript, Utterance
from tablesage_tools.speakers import UNASSIGNED_SPEAKER

from ..paths import ARTIFACTS, ArtifactName
from .artifacts import delete_artifact
from .role_transcript import RoleTranscript, RoleTranscriptUtterance
from .transcript_review import load_review_transcript


class Stage(Enum):
    """A `clean_transcript` pipeline stage, reported to `on_progress`.

    Both stages are single opaque calls -- `on_progress` fires with `total=0` on entry
    (indeterminate: show the stage label, not a moving bar) and `(1, 1)` on completion. Neither
    stage makes an LLM call (that judgment already happened in the pre-review pass, see
    `remove_backchannels.py`), so both complete essentially instantly.
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


def _remove_unassigned_backchannels(transcript: Transcript, max_words: int) -> Transcript:
    """Drop a wordlist-matched candidate only if it is still `UNASSIGNED_SPEAKER`.

    This is the post-review pass: a human has already had the chance to assign a real speaker to
    (or delete) every utterance, so anything still unassigned and backchannel-shaped is very
    likely genuine noise -- no LLM judgment needed. Every candidate whose speaker *was* resolved
    already went through the pre-review pass's "is the previous utterance a question?" check (see
    `remove_backchannels.py`); re-asking that here would be redundant.
    """
    candidate_indices = find_backchannel_candidates(transcript, max_words)
    to_remove = {index for index in candidate_indices if transcript.utterances[index].speaker == UNASSIGNED_SPEAKER}
    if not to_remove:
        return transcript
    kept = [utterance for index, utterance in enumerate(transcript.utterances) if index not in to_remove]
    return Transcript(utterances=kept)


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
    transcript = RoleTranscript.load(session_folder / ARTIFACTS[ArtifactName.ROLE_TRANSCRIPT].filename)
    return "\n\n".join(_render_utterance(utterance) for utterance in transcript.utterances) + "\n"


def _render_utterance(utterance: RoleTranscriptUtterance) -> str:
    return f"**{utterance.speaker}** - {utterance.text}"


def clean_transcript(
    session_folder: Path,
    max_words: int,
    role_names: dict[str, str],
    on_progress: OnProgress | None = None,
) -> CleanTranscriptResult:
    """Remove leftover backchannels from and assign roles to a session's preferred transcript, writing `role_transcript.json`.

    Reads the completed Manual Review when present, otherwise the machine transcript (see
    `load_review_transcript`) -- neither source is modified. The result is a new, independent
    artifact: `transcript.json` and `transcript_reviewed.json` are untouched by this step.
    Regenerating `role_transcript.json` invalidates any Ledger and Summary built from the previous
    copy, since both are derived from it.

    Unlike the pre-review pass (`remove_backchannels.py`, run automatically during Transcribe),
    this step makes no LLM call -- see `_remove_unassigned_backchannels`.
    """
    transcript = load_review_transcript(session_folder)
    original_count = len(transcript.utterances)

    with widelog.wide_event(op="clean_transcript", session_folder=str(session_folder)) as log:
        _report(on_progress, Stage.REMOVING_BACKCHANNELS, 0, 0)
        cleaned = _remove_unassigned_backchannels(transcript, max_words)
        _report(on_progress, Stage.REMOVING_BACKCHANNELS, 1, 1)

        _report(on_progress, Stage.ASSIGNING_ROLES, 0, 0)
        role_transcript = RoleTranscript.from_transcript(_apply_roles(cleaned, role_names))
        _report(on_progress, Stage.ASSIGNING_ROLES, 1, 1)

        target = session_folder / ARTIFACTS[ArtifactName.ROLE_TRANSCRIPT].filename
        temporary = target.with_name(f".{target.stem}.tmp{target.suffix}")
        try:
            role_transcript.save(temporary)
            temporary.replace(target)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise

        for name in (
            ArtifactName.TRANSCRIPT_SECTIONS,
            ArtifactName.LEDGER,
            ArtifactName.PLAYER_INTRODUCTIONS,
            ArtifactName.RECAP_SUMMARY,
            ArtifactName.SUMMARY,
        ):
            delete_artifact(session_folder, name)

        removed_count = original_count - len(cleaned.utterances)
        log.set(utterance_count=len(cleaned.utterances), removed_count=removed_count)
        return CleanTranscriptResult(utterance_count=len(cleaned.utterances), removed_count=removed_count)
