from __future__ import annotations

from enum import StrEnum

from ... import _paths
from ..._tools.embeddings import compute_centroid
from ...io import load_player, load_player_set, save_player
from ...model.cast import ProvenanceType
from ...settings import AppSettings


class InputChange(StrEnum):
    SUMMARY_RERUN = "summary_rerun"
    PROCESS_SESSION_RERUN = "process_session_rerun"
    AUDIO_REPLACED = "audio_replaced"
    ATTENDEES_EDITED = "attendees_edited"


_DESTRUCTIVE_CHANGES = frozenset({InputChange.PROCESS_SESSION_RERUN, InputChange.AUDIO_REPLACED, InputChange.ATTENDEES_EDITED})


def invalidate(campaign_slug: str, session_slug: str, change: InputChange, app_settings: AppSettings) -> None:
    session_dir = _paths.session_dir(campaign_slug, session_slug)
    summary = session_dir / _paths.KnownFiles.SUMMARY
    transcript = session_dir / _paths.KnownFiles.TRANSCRIPT
    discourse = session_dir / _paths.KnownFiles.DISCOURSE
    cleaned_audio = session_dir / app_settings.cleaned_audio_file

    if change == InputChange.SUMMARY_RERUN:
        summary.unlink(missing_ok=True)
    elif change in _DESTRUCTIVE_CHANGES:
        summary.unlink(missing_ok=True)
        transcript.unlink(missing_ok=True)
        discourse.unlink(missing_ok=True)
        cleaned_audio.unlink(missing_ok=True)
        _retract_session_enhanced_voice_samples(campaign_slug, session_slug)


def _retract_session_enhanced_voice_samples(campaign_slug: str, session_slug: str) -> None:
    try:
        player_set = load_player_set(campaign_slug)
    except FileNotFoundError:
        return

    for entry in player_set.players:
        try:
            player = load_player(campaign_slug, entry.slug)
        except FileNotFoundError:
            continue

        kept = []
        removed = []
        for sample in player.voice_samples:
            if sample.source == session_slug and sample.provenance_type == ProvenanceType.SESSION_ENHANCEMENT:
                removed.append(sample)
            else:
                kept.append(sample)
        if not removed:
            continue

        player_dir = _paths.player_dir(campaign_slug, entry.slug)
        for sample in removed:
            (player_dir / sample.filepath).unlink(missing_ok=True)

        centroid = compute_centroid([s.embedding for s in kept]) if kept else player.centroid
        save_player(
            campaign_slug,
            player.model_copy(update={"voice_samples": tuple(kept), "centroid": centroid}),
        )
