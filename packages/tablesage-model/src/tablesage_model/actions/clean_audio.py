from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from ..protocols.progress_syncs import PhasedProgressEvent, PhasedProgressSink
from ..tools import audio_cleaning


async def _progress(sink: PhasedProgressSink, phase: str) -> None:
    event: PhasedProgressEvent = PhasedProgressEvent(source="audio_cleaner", phase=phase)
    await sink.publish(event)


async def clean_audio(source_path: Path, cleaned_output_path: Path, normalize_volume: bool, sink: PhasedProgressSink) -> None:
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

        if normalize_volume:
            await _progress(sink, "measuring loudness")
            stats = await audio_cleaning.measure_loudness(post_mosfet_path)
            await _progress(sink, "measuring normalizing and exporting to 16k mono")
            await audio_cleaning.normalize_and_export_16k_mono(post_mosfet_path, cleaned_output_path, stats)
        else:
            await _progress(sink, "exporting to 16k mono")
            await audio_cleaning.convert_to_16k_mono(post_mosfet_path, cleaned_output_path)
