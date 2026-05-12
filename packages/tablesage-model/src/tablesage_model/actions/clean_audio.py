from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from .. import paths
from .._tools import audio_cleaning
from ..protocols import PhasedProgressEvent, PhasedProgressSink
from ..settings import AudioCleaningSettings


async def _progress(sink: PhasedProgressSink, phase: str) -> None:
    event: PhasedProgressEvent = PhasedProgressEvent(source="audio_cleaner", phase=phase)
    await sink.publish(event)


async def clean_audio(campaign_slug:str, session_slug:str, settings: AudioCleaningSettings, sink: PhasedProgressSink) -> None:
    session_dir: Path = paths.session_dir(campaign_slug, session_slug)
    source_path: Path = paths.to_absolute(session_dir, settings.raw_audio_file)
    cleaned_output_path: Path = paths.to_absolute(session_dir, settings.cleaned_audio_file)
    if not source_path.exists():
        raise FileNotFoundError(source_path)

    with TemporaryDirectory() as tmpdir:
        tmp_dir = Path(tmpdir)
        wav_48k_path = tmp_dir / "wav_48k.wav"
        post_mosfet_path = tmp_dir / "post_mosfet.wav"

        await _progress(sink, "convert to 48k wav")
        await audio_cleaning.convert_to_48k_wav(source_path, wav_48k_path)

        await _progress(sink, "clean with mossformer2")
        await audio_cleaning.enhance_with_mossformer2(wav_48k_path, post_mosfet_path)

        if settings.normalize_volume:
            await _progress(sink, "measuring loudness")
            stats = await audio_cleaning.measure_loudness(post_mosfet_path)
            await _progress(sink, "measuring normalizing and exporting to 16k mono")
            await audio_cleaning.normalize_and_export_16k_mono(post_mosfet_path, cleaned_output_path, stats)
        else:
            await _progress(sink, "exporting to 16k mono")
            await audio_cleaning.convert_to_16k_mono(post_mosfet_path, cleaned_output_path)
