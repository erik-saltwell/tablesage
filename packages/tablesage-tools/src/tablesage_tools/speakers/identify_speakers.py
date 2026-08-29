from __future__ import annotations

import json
import logging
import math
import struct
import wave
from collections.abc import Callable
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Final

import widelog

from ..audio.ffmpeg import extract_clip
from ..embeddings.similarity import SimilarityComputer, SimilarityResult
from ..embeddings.types import Embedding
from ..embeddings.wespeaker import EmbeddingFactory
from ..model.transcript import Transcript, Utterance

UNASSIGNED_SPEAKER: Final[str] = "Unassigned Speaker"

# fbank itself only needs >=25ms (window_size=400 samples at 16kHz) to produce a single
# frame, but empirically ERes2NetV2's downstream layers return NaN for anything shorter
# than ~110ms even though fbank succeeds -- a 2026-08-24 production run showed a hard
# cliff, every clip <=0.10s NaN, every clip >=0.11s fine. This floor is set clear of that
# cliff, not just fbank's, so those clips are skipped as too-short instead of reaching the
# model at all. Public (not module-private): a benchmark that scores this function's output
# against hand-corrected ground truth needs the identical floor to exclude utterances this
# function could never have judged in the first place -- see
# `session_pipeline.transcript_review.generate_benchmark_transcript`.
MIN_UTTERANCE_DURATION_SECONDS: Final[float] = 0.15

# Per-utterance diagnostics live outside widelog's one-line-per-operation model: a single
# transcribe run can carry hundreds of utterances, and root-causing a specific
# misidentification needs the per-utterance detail (who it was closest to, who was
# second, the raw similarity vector) that one aggregated wide event can't carry without
# becoming unreadable. The TUI's composition root wires this logger to its own rotating
# file, same as widelog's -- `tablesage-tools` itself never touches the filesystem for it.
_diagnostics_logger = logging.getLogger("tablesage.speaker_identification")


def _log_diagnostic(**fields: Any) -> None:
    _diagnostics_logger.info(json.dumps(fields, default=str))


def _clip_amplitude_stats(path: Path) -> dict[str, float | str]:
    """Peak/RMS amplitude (normalized to [-1, 1]) of a 16-bit PCM mono wav.

    Only computed for a clip whose similarity came back NaN, to help tell a genuinely
    near-silent clip apart from a real model/data bug producing a degenerate embedding --
    diagnostics-only, so a read failure is reported, not raised, and never interrupts the
    transcription run over it.
    """
    try:
        with wave.open(str(path), "rb") as wav_file:
            frame_count = wav_file.getnframes()
            raw = wav_file.readframes(frame_count)
    except (OSError, wave.Error) as exc:
        return {"error": str(exc)}
    if not raw:
        return {"peak_amplitude": 0.0, "rms_amplitude": 0.0, "sample_count": 0}
    samples = struct.unpack(f"<{len(raw) // 2}h", raw)
    normalized = [s / 32768.0 for s in samples]
    peak = max(abs(s) for s in normalized)
    rms = math.sqrt(sum(s * s for s in normalized) / len(normalized))
    return {"peak_amplitude": peak, "rms_amplitude": rms, "sample_count": len(normalized)}


async def identify_speakers(
    transcript: Transcript,
    audio_path: Path,
    centroids: dict[str, Embedding],
    embed: EmbeddingFactory,
    similarity_margin_threshold: float,
    on_progress: Callable[[int, int], None] | None = None,
    *,
    log_diagnostics: bool = False,
    allow_unassigned: bool = True,
) -> Transcript:
    """Relabel each utterance's speaker with the best-matching player name, or UNASSIGNED_SPEAKER.

    For each utterance, extracts its audio clip from `audio_path`, embeds it, and compares it
    against every player's centroid in `centroids`. If the margin between the best and
    second-best match is below `similarity_margin_threshold`, the utterance is left as
    UNASSIGNED_SPEAKER rather than guessed -- unless `allow_unassigned` is False, in which case
    that check is skipped and the best match is always taken, regardless of how close the
    runner-up was. Raises ValueError if `centroids` has fewer than 2 entries (see
    SimilarityComputer).

    `allow_unassigned=False` only disables the margin-confidence check; an utterance too short
    to embed at all is still left UNASSIGNED_SPEAKER either way, since there's no embedding-based
    judgment to skip there -- there's simply nothing to compare.

    `log_diagnostics=True` additionally writes one line per utterance to the
    "tablesage.speaker_identification" logger (see module docstring comment above
    `_diagnostics_logger`) -- a plain value, not an `AppSettings` object, per
    `tablesage-tools`' settings-agnostic boundary; the caller reads the toggle from
    `AppSettings.speaker_identification.log_diagnostics` (and `allow_unassigned` from
    `AppSettings.speaker_identification.allow_unassigned`).
    """
    names = list(centroids)
    similarity_computer = SimilarityComputer(tuple(centroids[name] for name in names))

    # A corrupted reference centroid (NaN component) poisons every comparison against that
    # one speaker for the whole run -- check once, up front, rather than only discovering it
    # utterance-by-utterance.
    if log_diagnostics:
        nan_reference_names = [name for name in names if any(math.isnan(x) for x in centroids[name].root)]
        if nan_reference_names:
            _log_diagnostic(
                event="corrupt_reference_centroid",
                speaker_names=nan_reference_names,
                similarity_margin_threshold=similarity_margin_threshold,
            )

    total = len(transcript.utterances)
    new_utterances: list[Utterance] = []
    too_short_count = 0
    below_threshold_count = 0
    assigned_count = 0
    nan_margin_count = 0
    margins: list[float] = []

    with widelog.wide_event(
        op="identify_speakers",
        utterance_count=total,
        speaker_names=names,
        similarity_margin_threshold=similarity_margin_threshold,
        allow_unassigned=allow_unassigned,
        min_utterance_duration_seconds=MIN_UTTERANCE_DURATION_SECONDS,
    ) as log:
        with TemporaryDirectory() as tmpdir:
            tmp_file = Path(tmpdir) / "tmp.wav"
            for index, utterance in enumerate(transcript.utterances):
                duration = utterance.end - utterance.start
                if duration < MIN_UTTERANCE_DURATION_SECONDS:
                    # Too short for the embedding model's feature extractor to run on at all --
                    # leave it unassigned rather than crashing the whole transcription run.
                    too_short_count += 1
                    new_utterances.append(utterance.model_copy(update={"speaker": UNASSIGNED_SPEAKER, "similarity_margin": 0.0}))
                    if log_diagnostics:
                        _log_diagnostic(
                            utterance_index=index,
                            start=utterance.start,
                            end=utterance.end,
                            duration=duration,
                            reason="too_short",
                            assigned=False,
                            similarity_margin_threshold=similarity_margin_threshold,
                        )
                else:
                    await extract_clip(audio_path, tmp_file, utterance.start, utterance.end)

                    embedding = await embed.extract_async(tmp_file)
                    result: SimilarityResult = similarity_computer.compute_similarity(embedding)

                    # `margin` is NaN exactly when the best and/or second-best similarity is
                    # NaN -- which only happens if fewer than 2 references produced a real
                    # number, i.e. this candidate embedding itself is NaN across the board.
                    # Any *other* reference going NaN is pushed to the bottom of the ranking
                    # (see SimilarityComputer.compute_similarity) and doesn't affect the
                    # decision, but is still visible below via `similarities`.
                    nan_margin = math.isnan(result.margin)
                    if nan_margin:
                        nan_margin_count += 1
                        speaker = UNASSIGNED_SPEAKER
                        reason = "nan_similarity"
                    else:
                        margins.append(result.margin)
                        if allow_unassigned and result.margin < similarity_margin_threshold:
                            below_threshold_count += 1
                            speaker = UNASSIGNED_SPEAKER
                            reason = "below_margin_threshold"
                        else:
                            assigned_count += 1
                            speaker = names[result.best_match_index]
                            reason = "assigned"
                    new_utterances.append(utterance.model_copy(update={"speaker": speaker, "similarity_margin": result.margin}))

                    if log_diagnostics:
                        diagnostic_fields: dict[str, Any] = {
                            "utterance_index": index,
                            "start": utterance.start,
                            "end": utterance.end,
                            "duration": duration,
                            "reason": reason,
                            "assigned": speaker != UNASSIGNED_SPEAKER,
                            "similarity_margin_threshold": similarity_margin_threshold,
                            "best_speaker": names[result.best_match_index],
                            "best_similarity": result.best_match_similarity,
                            "second_speaker": names[result.second_best_index],
                            "second_similarity": result.second_best_similarity,
                            "margin": result.margin,
                            "similarities": dict(zip(names, result.similarities, strict=True)),
                        }
                        if nan_margin or any(math.isnan(s) for s in result.similarities):
                            diagnostic_fields["clip_amplitude"] = _clip_amplitude_stats(tmp_file)
                        _log_diagnostic(**diagnostic_fields)

                if on_progress is not None:
                    on_progress(index + 1, total)

        # Distinguishes *why* utterances ended up unassigned -- too short to embed at all,
        # embedded but the best/second-best match was too close to trust, or a NaN
        # similarity (a corrupt candidate embedding) -- since all three look identical from
        # the resulting transcript alone. Full per-utterance detail (who else it was close
        # to) is in the "tablesage.speaker_identification" diagnostics log, not here.
        log.set(
            too_short_count=too_short_count,
            below_margin_threshold_count=below_threshold_count,
            assigned_count=assigned_count,
            nan_margin_count=nan_margin_count,
            margin_min=min(margins) if margins else None,
            margin_max=max(margins) if margins else None,
            margin_mean=sum(margins) / len(margins) if margins else None,
        )

    return Transcript(utterances=new_utterances)
