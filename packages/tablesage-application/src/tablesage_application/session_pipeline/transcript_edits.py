"""Review Transcript's decision: the reviewer's edits to the spellchecked transcript, as an edit list.

Edits are keyed by an utterance's immutable time span (plus its position among utterances sharing that span),
so the list stays small, reads as exactly what the reviewer changed, and still applies when the reviewer
reopens the step. Review only relabels speakers, rewrites displayed text, and deletes utterances; it never adds
or reorders them.
"""

from __future__ import annotations

from collections.abc import Iterator

from pydantic import BaseModel
from tablesage_tools.model import Transcript, Utterance


class UtteranceEdit(BaseModel, frozen=True):
    start: float
    end: float
    # Which of the utterances sharing this exact span, in transcript order.
    occurrence: int = 0
    deleted: bool = False
    speaker: str | None = None
    punctuated_text: str | None = None
    adjusted: bool | None = None


class TranscriptEdits(BaseModel, frozen=True):
    edits: tuple[UtteranceEdit, ...] = ()


def _keyed(transcript: Transcript) -> Iterator[tuple[tuple[float, float, int], Utterance]]:
    seen: dict[tuple[float, float], int] = {}
    for utterance in transcript.utterances:
        span = (utterance.start, utterance.end)
        occurrence = seen.get(span, 0)
        seen[span] = occurrence + 1
        yield (utterance.start, utterance.end, occurrence), utterance


def diff(source: Transcript, edited: Transcript) -> TranscriptEdits:
    """The edits that turn `source` into `edited`."""
    edited_by_key = dict(_keyed(edited))
    edits: list[UtteranceEdit] = []
    for key, original in _keyed(source):
        start, end, occurrence = key
        current = edited_by_key.get(key)
        if current is None:
            edits.append(UtteranceEdit(start=start, end=end, occurrence=occurrence, deleted=True))
            continue
        changes: dict[str, object] = {}
        if current.speaker != original.speaker:
            changes["speaker"] = current.speaker
        if current.punctuated_text != original.punctuated_text:
            changes["punctuated_text"] = current.punctuated_text
        if current.adjusted != original.adjusted:
            changes["adjusted"] = current.adjusted
        if changes:
            edits.append(UtteranceEdit.model_validate({"start": start, "end": end, "occurrence": occurrence, **changes}))
    return TranscriptEdits(edits=tuple(edits))


def apply(source: Transcript, edits: TranscriptEdits) -> Transcript:
    """`source` with `edits` applied. An edit whose utterance no longer exists in `source` is ignored."""
    by_key = {(edit.start, edit.end, edit.occurrence): edit for edit in edits.edits}
    utterances: list[Utterance] = []
    for key, utterance in _keyed(source):
        edit = by_key.get(key)
        if edit is None:
            utterances.append(utterance)
            continue
        if edit.deleted:
            continue
        update: dict[str, object] = {}
        if edit.speaker is not None:
            update["speaker"] = edit.speaker
        if edit.punctuated_text is not None:
            update["punctuated_text"] = edit.punctuated_text
        if edit.adjusted is not None:
            update["adjusted"] = edit.adjusted
        utterances.append(utterance.model_copy(update=update))
    return Transcript(utterances=utterances)
