from __future__ import annotations

import asyncio
import json
import shutil
import wave
from pathlib import Path
from tempfile import TemporaryDirectory

import widelog
from tablesage_model.settings import ReviewAudioNormalizationSettings
from tablesage_tools.audio import clean_clip, convert_to_16k_mono, dynamically_normalize_and_export_16k_mono

from ..paths import ARTIFACTS, AUDIO_EXTENSIONS, AUDIO_PAIR_MARKER, ArtifactName
from .atomic_files import atomic_write

_AUDIO_PAIR = (ArtifactName.INPUT_AUDIO, ArtifactName.NORMALIZED_REVIEW_AUDIO)


def _backup_path(folder: Path, filename: str) -> Path:
    return folder / f".audio-import-{filename}.bak"


def _recover_pair(folder: Path) -> None:
    """Roll back an interrupted publication before attempting another import.

    Backups survive recovery itself being interrupted; the graph rejects both
    outputs while the journal exists. Names are fixed by the registry, not read
    as arbitrary paths from the journal.
    """
    marker = folder / AUDIO_PAIR_MARKER
    if not marker.exists():
        return
    previous = json.loads(marker.read_text(encoding="utf-8"))
    filenames = [ARTIFACTS[name].filename for name in _AUDIO_PAIR]
    if not isinstance(previous, dict) or set(previous) != set(filenames) or any(type(v) is not bool for v in previous.values()):
        raise RuntimeError("Invalid audio import recovery record; the previous audio backups have been retained.")
    for filename in filenames:
        if previous[filename] and not _backup_path(folder, filename).is_file():
            raise RuntimeError(f"Cannot recover audio import: missing backup for {filename}.")
    with TemporaryDirectory(prefix=".audio-recovery-", dir=folder) as directory:
        for filename in filenames:
            target = folder / filename
            if previous[filename]:
                restored = Path(directory) / filename
                shutil.copy2(_backup_path(folder, filename), restored)
                restored.replace(target)
            else:
                target.unlink(missing_ok=True)
    marker.unlink()
    for filename in filenames:
        _backup_path(folder, filename).unlink(missing_ok=True)


def _publish_pair(staging: Path, folder: Path) -> None:
    """Publish only finished exports, retaining the old pair until both replacements succeed."""
    marker = folder / AUDIO_PAIR_MARKER
    filenames = [ARTIFACTS[name].filename for name in _AUDIO_PAIR]
    previous = {filename: (folder / filename).is_file() for filename in filenames}
    try:
        for filename in filenames:
            if previous[filename]:
                shutil.copy2(folder / filename, _backup_path(folder, filename))
        atomic_write(marker, json.dumps(previous).encode("utf-8"))
        try:
            for filename in filenames:
                (staging / filename).replace(folder / filename)
            marker.unlink()
        except BaseException:
            _recover_pair(folder)
            raise
    finally:
        # Leave the journal and backups intact if recovery failed or was interrupted.
        if not marker.exists():
            for filename in filenames:
                _backup_path(folder, filename).unlink(missing_ok=True)


def _verify_timing(processing_audio: Path, review_audio: Path) -> None:
    """Reject truncated exports or any change to the PCM timeline before publication."""
    with wave.open(str(processing_audio), "rb") as source, wave.open(str(review_audio), "rb") as normalized:
        if source.getparams() != normalized.getparams():
            raise RuntimeError("Normalized review audio changed the audio format or sample count; import was not published.")
        if source.getnframes() == 0:
            raise RuntimeError("Imported audio contains no samples.")


def import_audio(
    source_path: Path,
    session_folder: Path,
    normalize_volume: bool,
    *,
    should_clean_audio: bool = True,
    review_normalization: ReviewAudioNormalizationSettings | None = None,
) -> None:
    """Produce processing and normalized review audio, then publish them as a recoverable pair.

    Existing derivatives remain on disk and the graph checks their input fingerprints.
    Review normalization always runs, even when the user imports an already cleaned WAV.
    """
    settings = review_normalization or ReviewAudioNormalizationSettings()
    should_clean_audio = should_clean_audio or source_path.suffix.lower() != ".wav"
    with widelog.wide_event(
        op="import_audio",
        source_path=str(source_path),
        session_folder=str(session_folder),
        normalize_volume=normalize_volume,
        should_clean_audio=should_clean_audio,
        review_normalization=settings.model_dump(),
    ):
        if not source_path.is_file():
            raise ValueError(f"'{source_path}' is not a file.")
        session_folder.mkdir(parents=True, exist_ok=True)
        _recover_pair(session_folder)
        with TemporaryDirectory(prefix=".audio-import-", dir=session_folder) as directory:
            staging = Path(directory)
            processing_audio = staging / ARTIFACTS[ArtifactName.INPUT_AUDIO].filename
            review_audio = staging / ARTIFACTS[ArtifactName.NORMALIZED_REVIEW_AUDIO].filename
            if should_clean_audio:
                asyncio.run(clean_clip(source_path, processing_audio, normalize=normalize_volume))
            else:
                asyncio.run(convert_to_16k_mono(source_path, processing_audio))
            asyncio.run(
                dynamically_normalize_and_export_16k_mono(
                    processing_audio,
                    review_audio,
                    frame_length_ms=settings.frame_length_ms,
                    smoothing_frames=settings.smoothing_frames,
                    max_gain=settings.max_gain,
                    silence_threshold=settings.silence_threshold,
                    target_peak=settings.target_peak,
                )
            )
            _verify_timing(processing_audio, review_audio)
            _publish_pair(staging, session_folder)


def validate_import_source(source_path: Path) -> None:
    """Raise if `source_path` isn't a file with a recognized audio extension.

    A fast-fail UX check only -- the actual cleaning pipeline (ffmpeg) can
    handle far more than this list, but session recordings plausibly arrive
    as any of these common recorder/voice-memo formats, unlike the player
    voice-clip import's `.wav`-only source directories.
    """
    if not source_path.is_file():
        raise ValueError(f"'{source_path}' is not a file.")
    if source_path.suffix.lower() not in AUDIO_EXTENSIONS:
        raise ValueError(f"'{source_path.name}' isn't a recognized audio file.")
