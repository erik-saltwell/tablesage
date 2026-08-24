from __future__ import annotations

import asyncio
from pathlib import Path

import widelog
from tablesage_tools.audio import clean_clip, convert_to_16k_mono

from ..paths import ARTIFACTS, AUDIO_EXTENSIONS, ArtifactCategory, ArtifactName


def invalidate_downstream(session_folder: Path) -> None:
    """Delete every derived artifact (anything not IMPORTED) -- never the raw input audio.

    Public (not module-private) because every destructive edit invalidates:
    re-importing audio, adding/removing an attendee, editing roles, and
    (in Phase 11) rerunning Process -- all call this directly.
    """
    with widelog.wide_event(op="invalidate_downstream", session_folder=str(session_folder)):
        for spec in ARTIFACTS.values():
            if spec.category is not ArtifactCategory.IMPORTED:
                (session_folder / spec.filename).unlink(missing_ok=True)


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


def import_audio(source_path: Path, session_folder: Path, normalize_volume: bool, *, should_clean_audio: bool = True) -> None:
    """Clean (or just convert) `source_path` into the session folder as the fixed input-audio file.

    Cleaned into a temp file in the same folder first, so a failed/partial
    clean never corrupts an existing `input_audio.wav`; downstream artifacts
    are only invalidated once the clean has actually succeeded, so a failure
    leaves prior processing intact instead of destroying it for nothing.

    `should_clean_audio=False` skips the Mossformer2 noise-removal pass (and
    `normalize_volume` with it) and just runs the format conversion -- only valid for
    a `.wav` source, since a non-`.wav` recording was never previously run through
    cleaning and always needs it. Non-`.wav` sources always clean regardless of what's
    passed, since only a `.wav` can plausibly already be a cleaned export.
    """
    should_clean_audio = should_clean_audio or source_path.suffix.lower() != ".wav"
    with widelog.wide_event(
        op="import_audio",
        source_path=str(source_path),
        session_folder=str(session_folder),
        normalize_volume=normalize_volume,
        should_clean_audio=should_clean_audio,
    ):
        if not source_path.is_file():
            raise ValueError(f"'{source_path}' is not a file.")
        session_folder.mkdir(parents=True, exist_ok=True)

        input_audio_filename = ARTIFACTS[ArtifactName.INPUT_AUDIO].filename
        input_audio_path = Path(input_audio_filename)
        # ffmpeg infers its output muxer from the target's extension, so the
        # temp file must still end in `.wav` (not `.wav.tmp`) or it fails with
        # "Unable to choose an output format".
        temp_target = session_folder / f".{input_audio_path.stem}.tmp{input_audio_path.suffix}"
        try:
            if should_clean_audio:
                asyncio.run(clean_clip(source_path, temp_target, normalize=normalize_volume))
            else:
                asyncio.run(convert_to_16k_mono(source_path, temp_target))
        except Exception:
            temp_target.unlink(missing_ok=True)
            raise

        invalidate_downstream(session_folder)
        temp_target.replace(session_folder / input_audio_filename)
