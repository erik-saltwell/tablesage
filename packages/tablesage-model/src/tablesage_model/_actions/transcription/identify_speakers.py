from __future__ import annotations

import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory

from ... import _paths
from ..._tools import ffmpeg
from ..._tools.embeddings import EmbeddingFactory, SimilarityComputer, SimilarityResult
from ...model.discourse import Discourse, Utterance
from ...model.player import Player
from ...protocols import IncrementalProgressEvent, IncrementalProgressSink, UnassignedSpeaker
from ...settings import AppSettings, SpeakerIdentificationSettings


async def identify_speakers(
    campaign_slug: str,
    session_slug: str,
    app_settings: AppSettings,
    attendees: list[Player],
    session_set: Discourse,
    sink: IncrementalProgressSink,
) -> Discourse:

    if len(attendees) < 2:
        msg = "Cannot identify speakers with less than 2 attendees"
        raise ValueError(msg)

    settings: SpeakerIdentificationSettings = app_settings.speaker_identification
    session_dir: Path = _paths.session_dir(campaign_slug, session_slug)
    audio_path = _paths.to_absolute(session_dir, app_settings.audio_cleaning.cleaned_audio_file)

    similarity_computer = SimilarityComputer(tuple(player.centroid for player in attendees))

    factory: EmbeddingFactory = await asyncio.to_thread(EmbeddingFactory)

    total = len(session_set.utterances)
    new_utterances: list[Utterance] = []
    try:
        with TemporaryDirectory() as tmpdir:
            tmp_file = Path(tmpdir) / "tmp.wav"
            for i, utterance in enumerate(session_set.utterances):
                await ffmpeg.extract_clip(audio_path, tmp_file, utterance.start, utterance.end)

                embedding = await factory.extract_async(tmp_file)
                result: SimilarityResult = similarity_computer.compute_similarity(embedding)
                speaker = (
                    UnassignedSpeaker if result.margin < settings.similarity_margin_threshold else attendees[result.best_match_index].name
                )
                new_utterances.append(
                    utterance.model_copy(update={"speaker": speaker, "embedding": embedding, "similarity_margin": result.margin})
                )
                await sink.publish(IncrementalProgressEvent(source="identify_speakers", completed=i + 1, total=total))
    finally:
        await sink.publish(IncrementalProgressEvent(source="identify_speakers", completed=total, total=total))

    return Discourse(utterances=tuple(new_utterances))
