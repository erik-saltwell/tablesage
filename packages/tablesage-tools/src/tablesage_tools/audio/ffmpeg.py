from __future__ import annotations

import asyncio
import io
import json
import math
import re
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from clearvoice import ClearVoice

from .._utils import flush_gpu_memory, run_command_async


async def convert_to_48k_wav(input_path: Path, temp_wav_path: Path) -> None:
    """Convert source audio to the mono 48 kHz PCM WAV we will feed into MossFormer2_SE_48K."""
    temp_wav_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(input_path),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "48000",
        "-c:a",
        "pcm_s16le",
        str(temp_wav_path),
    ]
    await run_command_async(cmd)


def _enhance_with_mossformer2_sync(model_input_wav: Path, enhanced_wav_path: Path) -> None:
    """Run ClearVoice speech enhancement with MossFormer2_SE_48K."""
    enhanced_wav_path.parent.mkdir(parents=True, exist_ok=True)

    _sink = io.StringIO()
    with redirect_stdout(_sink), redirect_stderr(_sink):
        clearvoice = ClearVoice(
            task="speech_enhancement",
            model_names=["MossFormer2_SE_48K"],
        )
        output_wav = clearvoice(input_path=str(model_input_wav), online_write=False)
    clearvoice.write(output_wav, output_path=str(enhanced_wav_path))

    # Explicitly tear down the GPU model while we still hold a reference.
    # ClearVoice's network_wrapper (nn.Module) keeps the model on GPU; relying
    # on GC after this function returns is unreliable and leaves ~8 GB stranded.
    for model in clearvoice.models:
        if hasattr(model, "model") and model.model is not None:
            model.model.cpu()
            model.model = None
        model.data = {}
        model.result = {}
    del output_wav, clearvoice
    flush_gpu_memory()


async def enhance_with_mossformer2(model_input_wav: Path, enhanced_wav_path: Path) -> None:
    """Run ClearVoice speech enhancement without blocking the event loop."""
    await asyncio.to_thread(_enhance_with_mossformer2_sync, model_input_wav, enhanced_wav_path)


async def measure_loudness(input_wav: Path, target_i: float = -16.0, target_lra: float = 11.0, target_tp: float = -1.5) -> dict[str, str]:
    """Run loudnorm pass 1 and parse the emitted JSON stats."""
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-i",
        str(input_wav),
        "-af",
        f"loudnorm=I={target_i}:LRA={target_lra}:TP={target_tp}:print_format=json",
        "-f",
        "null",
        "-",
    ]
    result = await run_command_async(cmd, capture_output=True)

    # FFmpeg prints loudnorm JSON to stderr.
    match = re.search(r"\{[\s\S]*?\}", result.stderr)
    if not match:
        raise RuntimeError("Could not parse loudnorm JSON from ffmpeg output.")

    data = json.loads(match.group(0))
    return {k: str(v) for k, v in data.items()}


async def extract_clip(input_path: Path, output_wav: Path, start: float, end: float) -> None:
    """Extract a time-bounded clip from input_path as 16 kHz mono PCM WAV."""
    output_wav.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-ss",
        str(start),
        "-to",
        str(end),
        "-i",
        str(input_path),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-c:a",
        "pcm_s16le",
        str(output_wav),
    ]
    await run_command_async(cmd)


async def convert_to_16k_mono(input_path: Path, output_wav: Path) -> None:
    """Convert audio to 16 kHz mono PCM WAV without loudness normalization."""
    output_wav.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(input_path),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-c:a",
        "pcm_s16le",
        str(output_wav),
    ]
    await run_command_async(cmd)


async def clean_clip(source: Path, target: Path, *, normalize: bool = False) -> None:
    """Run a source audio file through the cleaning pipeline and write the result to *target*.

    Pipeline: 48 kHz wav -> Mossformer2 enhancement -> 16 kHz mono export
    (with optional loudness normalization when *normalize* is True).
    """
    from tempfile import TemporaryDirectory

    target.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        wav_48k = tmp / "wav_48k.wav"
        post_mosfet = tmp / "post_mosfet.wav"
        await convert_to_48k_wav(source, wav_48k)
        await enhance_with_mossformer2(wav_48k, post_mosfet)
        if normalize:
            stats = await measure_loudness(post_mosfet)
            await normalize_and_export_16k_mono(post_mosfet, target, stats)
        else:
            await convert_to_16k_mono(post_mosfet, target)


async def normalize_and_export_16k_mono(
    input_wav: Path,
    output_wav: Path,
    stats: dict[str, str],
    *,
    target_i: float = -16.0,
    target_lra: float = 11.0,
    target_tp: float = -1.5,
) -> None:
    """Run loudnorm pass 2 and export the final 16 kHz mono PCM WAV."""
    output_wav.parent.mkdir(parents=True, exist_ok=True)

    loudnorm_filter = (
        "loudnorm="
        f"I={target_i}:"
        f"LRA={target_lra}:"
        f"TP={target_tp}:"
        f"measured_I={stats['input_i']}:"
        f"measured_LRA={stats['input_lra']}:"
        f"measured_TP={stats['input_tp']}:"
        f"measured_thresh={stats['input_thresh']}:"
        f"offset={stats['target_offset']}:"
        "linear=true:"
        "print_format=summary"
    )

    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(input_wav),
        "-af",
        loudnorm_filter,
        "-ac",
        "1",
        "-ar",
        "16000",
        "-c:a",
        "pcm_s16le",
        str(output_wav),
    ]
    await run_command_async(cmd)


async def dynamically_normalize_and_export_16k_mono(
    input_wav: Path,
    output_wav: Path,
    *,
    frame_length_ms: int = 500,
    smoothing_frames: int = 5,
    max_gain: float = 4.0,
    silence_threshold: float = 0.003,
    target_peak: float = 0.9,
) -> None:
    """Level changing audio sections and export a 16 kHz mono PCM WAV.

    Use after any denoising step: dynamic gain can also raise residual noise.
    The gain cap and low-level threshold limit amplification of near-silence.
    This helper is intentionally separate from ``clean_clip`` until its use is
    chosen by the caller.
    """
    if not 10 <= frame_length_ms <= 8000:
        raise ValueError("frame_length_ms must be between 10 and 8000")
    if not 3 <= smoothing_frames <= 301 or smoothing_frames % 2 == 0:
        raise ValueError("smoothing_frames must be an odd number between 3 and 301")
    if not math.isfinite(max_gain) or not 1 <= max_gain <= 100:
        raise ValueError("max_gain must be between 1 and 100")
    if not math.isfinite(silence_threshold) or not 0 <= silence_threshold <= 1:
        raise ValueError("silence_threshold must be between 0 and 1")
    if not math.isfinite(target_peak) or not 0 < target_peak <= 0.95:
        raise ValueError("target_peak must be greater than 0 and at most 0.95")

    output_wav.parent.mkdir(parents=True, exist_ok=True)
    filters = (
        f"dynaudnorm=framelen={frame_length_ms}:gausssize={smoothing_frames}:"
        f"peak={target_peak}:maxgain={max_gain}:threshold={silence_threshold},"
        "alimiter=limit=0.95:level=false:latency=true"
    )
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(input_wav),
        "-vn",
        "-af",
        filters,
        "-ac",
        "1",
        "-ar",
        "16000",
        "-c:a",
        "pcm_s16le",
        str(output_wav),
    ]
    await run_command_async(cmd)
