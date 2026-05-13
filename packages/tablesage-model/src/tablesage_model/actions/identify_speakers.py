from __future__ import annotations

import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory

from .. import paths
from .._tools import embeddings, ffmpeg
from ..model import RegisteredSpeaker, SessionSet, SessionUtterance
from ..protocols import IncrementalProgressEvent, IncrementalProgressSink, UnassignedSpeaker
from ..settings import AppSettings, SpeakerIdentificationSettings


async def identify_speakers(
    campaign_slug: str,
    session_slug: str,
    app_settings: AppSettings,
    attendees: list[RegisteredSpeaker],
    session_set: SessionSet,
    sink: IncrementalProgressSink,
) -> SessionSet:

    if len(attendees) < 2:
        msg = "Cannot identify speakers with less than 2 attendees"
        raise ValueError(msg)

    settings: SpeakerIdentificationSettings = app_settings.speaker_identification
    session_dir: Path = paths.session_dir(campaign_slug, session_slug)
    audio_path = paths.to_absolute(session_dir, app_settings.cleaned_audio_file)

    speakers_tensor = embeddings.convert_multiple_to_tensors([s.embedding for s in attendees])
    factory = await asyncio.to_thread(embeddings.EmbeddingFactory)

    total = len(session_set.utterances)
    new_utterances: list[SessionUtterance] = []
    try:
        with TemporaryDirectory() as tmpdir:
            tmp_file = Path(tmpdir) / "tmp.wav"
            for i, utterance in enumerate(session_set.utterances):
                await ffmpeg.extract_clip(audio_path, tmp_file, utterance.start, utterance.end)

                embedding = await asyncio.to_thread(factory.extract, tmp_file)
                utterance_tensor = embeddings.convert_to_tensor(embedding)

                similarities = embeddings.compute_similarity_multiple(utterance_tensor, speakers_tensor)
                best_idx, best_similarity = max(enumerate(similarities), key=lambda x: x[1])

                avg_similarity = sum(similarities) / len(similarities)
                residual = best_similarity - avg_similarity
                speaker = UnassignedSpeaker if residual < settings.similarity_residual_threshold else attendees[best_idx].name
                new_utterances.append(
                    utterance.model_copy(update={"speaker": speaker, "embedding": tuple(embedding), "similarity_residual": residual})
                )
                await sink.publish(IncrementalProgressEvent(source="identify_speakers", completed=i + 1, total=total))
    finally:
        await sink.publish(IncrementalProgressEvent(source="identify_speakers", completed=total, total=total))

    return SessionSet(utterances=tuple(new_utterances))
