from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ... import _paths
from ..._settings import AppSettings, EnhanceVoicesSettings
from ..._tools import ffmpeg
from ..._tools.embeddings import EmbeddingFactory
from ...io import load_discourse, load_player, load_player_set, load_session, save_player
from ...model.cast import Embedding, Player, ProvenanceType, VoiceSample
from ...model.transcription import Discourse, Utterance
from ...protocols import PhasedProgressEvent, PhasedProgressSink
from .remove_outliers import remove_outliers


@dataclass(frozen=True, slots=True)
class RetractionResult:
    kept: Player
    removed: tuple[VoiceSample, ...]


def select_enhancement_utterances(
    discourse: Discourse,
    attendee_name: str,
    settings: EnhanceVoicesSettings,
) -> tuple[tuple[int, Utterance], ...]:
    selected: list[tuple[int, Utterance]] = []
    for index, utterance in enumerate(discourse.utterances):
        if utterance.speaker != attendee_name:
            continue
        if utterance.similarity_margin < settings.min_margin_for_voice_sample:
            continue
        duration = utterance.end - utterance.start
        if duration < settings.min_clip_seconds or duration > settings.max_clip_seconds:
            continue
        selected.append((index, utterance))
    return tuple(selected)


def delete_voice_samples_by_source(
    player: Player,
    *,
    source: str,
    provenance_type: ProvenanceType,
) -> RetractionResult:
    kept: list[VoiceSample] = []
    removed: list[VoiceSample] = []
    for sample in player.voice_samples:
        if sample.source == source and sample.provenance_type == provenance_type:
            removed.append(sample)
        else:
            kept.append(sample)
    return RetractionResult(
        kept=player.model_copy(update={"voice_samples": tuple(kept)}),
        removed=tuple(removed),
    )


async def enhance_voices(
    campaign_slug: str,
    session_slug: str,
    app_settings: AppSettings,
    sink: PhasedProgressSink,
) -> None:
    await sink.publish(PhasedProgressEvent(source="enhance_voices", phase="loading session"))
    session = load_session(campaign_slug, session_slug)
    discourse = load_discourse(campaign_slug, session_slug)
    current_slugs = {p.slug for p in load_player_set(campaign_slug).players}

    session_dir = _paths.session_dir(campaign_slug, session_slug)
    cleaned_audio = _paths.to_absolute(session_dir, app_settings.cleaned_audio_file)

    embedding_factory = EmbeddingFactory()

    for attendee_slug in session.attendees:
        if attendee_slug not in current_slugs:
            await sink.publish(PhasedProgressEvent(source="enhance_voices", phase=f"skipping orphan {attendee_slug}"))
            continue

        await sink.publish(PhasedProgressEvent(source="enhance_voices", phase=f"enhancing {attendee_slug}"))
        await _enhance_one_attendee(
            campaign_slug=campaign_slug,
            session_slug=session_slug,
            attendee_slug=attendee_slug,
            discourse=discourse,
            cleaned_audio=cleaned_audio,
            app_settings=app_settings,
            embedding_factory=embedding_factory,
        )


async def _enhance_one_attendee(
    *,
    campaign_slug: str,
    session_slug: str,
    attendee_slug: str,
    discourse: Discourse,
    cleaned_audio: Path,
    app_settings: AppSettings,
    embedding_factory: EmbeddingFactory,
) -> None:
    player = load_player(campaign_slug, attendee_slug)
    retraction = delete_voice_samples_by_source(
        player,
        source=session_slug,
        provenance_type=ProvenanceType.SESSION_ENHANCEMENT,
    )
    player_dir = _paths.player_dir(campaign_slug, attendee_slug)
    for removed in retraction.removed:
        backing = player_dir / removed.filepath
        backing.unlink(missing_ok=True)

    selections = select_enhancement_utterances(discourse, attendee_name=player.name, settings=app_settings.enhance_voices)

    voice_clips_dir = _paths.voice_clips_dir(campaign_slug, attendee_slug)
    _paths.ensure_dir(voice_clips_dir)

    new_samples: list[VoiceSample] = []
    for utterance_index, utterance in selections:
        filename = _paths.generate_voice_sample_filename()
        target = voice_clips_dir / filename
        await ffmpeg.extract_clip(cleaned_audio, target, utterance.start, utterance.end)
        embedding: Embedding = await embedding_factory.extract_async(target)
        relative = target.relative_to(player_dir)
        new_samples.append(
            VoiceSample(
                filepath=relative,
                embedding=embedding,
                provenance_type=ProvenanceType.SESSION_ENHANCEMENT,
                source=session_slug,
                index=utterance_index,
            )
        )

    unioned = (*retraction.kept.voice_samples, *new_samples)
    updated = retraction.kept.model_copy(update={"voice_samples": unioned})
    save_player(campaign_slug, updated)

    await remove_outliers(campaign_slug, attendee_slug, app_settings)
