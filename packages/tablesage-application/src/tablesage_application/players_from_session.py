from __future__ import annotations

import asyncio
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from sqlmodel import Session
from tablesage_model.settings import EnhanceVoicesSettings, RemoveOutliersSettings
from tablesage_tools.audio import extract_clip
from tablesage_tools.embeddings import Embedding
from tablesage_tools.model import Transcript, Utterance

from .entities.sessions import list_attendance
from .paths import ARTIFACTS, ArtifactName
from .voice_clips import clips


class Stage(Enum):
    """An `enhance_players_from_session` pipeline stage, reported to `on_progress`.

    EXTRACTING reports one running count across every attendee's qualifying utterances
    (not reset per attendee). RECOMPUTING_CENTROIDS reports one count per attendee (not
    per-clip -- a single attendee's own centroid recompute isn't itemized to this stage).
    """

    EXTRACTING = "extracting"
    RECOMPUTING_CENTROIDS = "recomputing_centroids"


OnProgress = Callable[[Stage, int, int], None]


@dataclass(frozen=True)
class EnhanceResult:
    """The outcome of an "enhance players from session" run, for the caller to report to the user."""

    enhanced_player_count: int
    clip_count: int


def select_enhancement_utterances(
    utterances: list[Utterance],
    player_name: str,
    min_margin: float,
    min_seconds: float,
    max_seconds: float,
) -> list[Utterance]:
    """Utterances attributed to `player_name` that are confident and well-sized enough to bank as a voice sample.

    Comparing `utterance.speaker == player_name` already excludes every other attendee's
    utterances and `UNASSIGNED_SPEAKER` (never a real player name) in one check. A `None`
    `similarity_margin` (only possible for a transcript produced before that field existed)
    fails the filter rather than passing it -- see `.documentation/enhance_players_from_session.md`.
    """
    selected = []
    for utterance in utterances:
        if utterance.speaker != player_name:
            continue
        if utterance.similarity_margin is None or utterance.similarity_margin < min_margin:
            continue
        duration = utterance.end - utterance.start
        if duration < min_seconds or duration > max_seconds:
            continue
        selected.append(utterance)
    return selected


def _generated_session_filename(player_name: str, campaign_name: str, session_name: str, session_hash: str) -> str:
    slug = clips.slugify
    return f"session-{slug(player_name)}-{slug(campaign_name)}-{slug(session_name)}-{session_hash}-{uuid.uuid4().hex}.wav"


def _report(on_progress: OnProgress | None, stage: Stage, completed: int, total: int) -> None:
    if on_progress is not None:
        on_progress(stage, completed, total)


def enhance_players_from_session(
    session: Session,
    session_id: uuid.UUID,
    session_folder: Path,
    campaign_name: str,
    session_name: str,
    player_folders: dict[uuid.UUID, Path],
    embed: Callable[[Path], Embedding],
    enhance_settings: EnhanceVoicesSettings,
    outlier_settings: RemoveOutliersSettings,
    on_progress: OnProgress | None = None,
) -> EnhanceResult:
    """Pull high-confidence voice clips for every attendee out of the session's transcript.

    For each attendee: capture their prior clips from this session (by filename hash
    segment), extract fresh qualifying clips from the transcript, then delete the
    captured prior clips -- extract-then-delete-old, so a failure partway through never
    leaves an attendee worse off than before the run. This replace-as-a-unit rule is
    unconditional: even an attendee with zero qualifying utterances this run has their
    prior session clips deleted (see `select_enhancement_utterances` and the design doc).
    Every attendee's centroid is recomputed afterward, regardless of whether they got new
    clips, since a zero-new-clips attendee may still have had stale clips retracted.
    """
    transcript = Transcript.load(session_folder / ARTIFACTS[ArtifactName.TRANSCRIPT].filename)
    input_audio_path = session_folder / ARTIFACTS[ArtifactName.INPUT_AUDIO].filename
    session_hash = clips.hash8(str(session_id))

    attendees = list_attendance(session, session_id)
    utterances_by_player: dict[uuid.UUID, list[Utterance]] = {
        attendee.player_id: select_enhancement_utterances(
            transcript.utterances,
            attendee.player_name,
            enhance_settings.min_margin_for_voice_sample,
            enhance_settings.min_clip_seconds,
            enhance_settings.max_clip_seconds,
        )
        for attendee in attendees
    }
    total_clips = sum(len(utterances) for utterances in utterances_by_player.values())

    async def _extract_all() -> dict[uuid.UUID, int]:
        written_counts: dict[uuid.UUID, int] = {}
        completed = 0
        _report(on_progress, Stage.EXTRACTING, 0, total_clips)
        for attendee in attendees:
            folder = player_folders[attendee.player_id]
            prior_clips = clips.find_clips_by_hash_segment(folder, "session", session_hash)

            written = 0
            for utterance in utterances_by_player[attendee.player_id]:
                filename = _generated_session_filename(attendee.player_name, campaign_name, session_name, session_hash)
                await extract_clip(input_audio_path, folder / filename, utterance.start, utterance.end)
                written += 1
                completed += 1
                _report(on_progress, Stage.EXTRACTING, completed, total_clips)

            for old_clip in prior_clips:
                old_clip.unlink(missing_ok=True)

            written_counts[attendee.player_id] = written
        return written_counts

    written_counts = asyncio.run(_extract_all())

    for index, attendee in enumerate(attendees, start=1):
        folder = player_folders[attendee.player_id]
        clips.recompute_centroid(
            session, attendee.player_id, folder, embed, None, outlier_settings.min_sample_similarity, outlier_settings.min_samples
        )
        _report(on_progress, Stage.RECOMPUTING_CENTROIDS, index, len(attendees))

    enhanced_player_count = sum(1 for count in written_counts.values() if count > 0)
    return EnhanceResult(enhanced_player_count=enhanced_player_count, clip_count=total_clips)
