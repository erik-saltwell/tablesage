from __future__ import annotations

from pathlib import Path

from .. import paths
from .._tools import eleven_labs
from ..model import TranscribedUtterance, TranscribedWord, Transcript
from ..protocols import PhasedProgressEvent, PhasedProgressSink
from ..settings import TranscriptionAndDiarizationSettings


async def _progress(sink: PhasedProgressSink, phase: str) -> None:
    event: PhasedProgressEvent = PhasedProgressEvent(source="transcribe_and_diarize", phase=phase)
    await sink.publish(event)


async def transcribe_and_diarize(
    session_dir: Path,
    settings: TranscriptionAndDiarizationSettings,
    speaker_count: int | None,
    sink: PhasedProgressSink,
) -> Transcript:
    input_audio_path = paths.to_absolute(session_dir, settings.input_audio_file)
    await _progress(sink, "transcribing and diarizing with elevenlabs")
    transcribed_words: list[eleven_labs.TranscriptionWord] = await eleven_labs.transcribe_and_diarize(
        input_audio_path, settings.language_code, settings.model_id, settings.timeout, settings.tag_audio_events, speaker_count
    )

    await _progress(sink, "building transcript")
    current_words: list[TranscribedWord] = []
    current_speaker: str | None = None
    utterances: list[TranscribedUtterance] = []

    for word in transcribed_words:
        if word.type != eleven_labs.SpeechType.WORD:
            continue
        if current_speaker is None:
            current_speaker = word.speaker
        if word.speaker != current_speaker:
            utterances.append(TranscribedUtterance.from_words(current_words))
            current_words = []
            current_speaker = word.speaker
        current_words.append(TranscribedWord(text=word.text, start=word.start, end=word.end, speaker=word.speaker))
    if current_words:
        utterances.append(TranscribedUtterance.from_words(current_words))

    if not utterances:
        msg = "No speech found in audio — transcript would be empty"
        raise ValueError(msg)

    return Transcript(utterances=tuple(utterances))
