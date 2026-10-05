from __future__ import annotations

import math
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import widelog
from sqlmodel import Session
from tablesage_tools.embeddings import Embedding, cosine_similarity

from . import clips


@dataclass(frozen=True)
class RankedVoiceClip:
    filename: str
    duration_seconds: float
    similarity: float


@dataclass(frozen=True)
class VoiceSampleReview:
    player_name: str
    clips: tuple[RankedVoiceClip, ...]
    deleted_filenames: tuple[str, ...]
    skipped_filenames: tuple[str, ...]


def prepare_review(
    session: Session,
    player_id: uuid.UUID,
    folder: Path,
    embed: Callable[[Path], Embedding],
    min_sample_similarity: float,
    min_samples: int,
    on_progress: Callable[[int, int], None] | None = None,
) -> VoiceSampleReview:
    """Clean usable samples and rank survivors once; unscorable files remain untouched."""
    with widelog.wide_event(op="prepare_voice_sample_review", player_id=str(player_id)) as log:
        samples = clips.list_voice_clips(folder)
        embeddings: dict[Path, Embedding] = {}
        skipped: list[str] = []
        dimension: int | None = None
        for index, sample in enumerate(samples, start=1):
            path = folder / sample.filename
            try:
                if sample.duration_seconds <= 0:
                    raise ValueError("Clip has no readable audio.")
                embedding = embed(path)
                if not embedding.root or not all(math.isfinite(value) for value in embedding.root):
                    raise ValueError("Invalid voice embedding.")
                if sum(value * value for value in embedding.root) <= 0:
                    raise ValueError("Empty voice embedding.")
                if dimension is not None and len(embedding) != dimension:
                    raise ValueError("Incompatible embedding dimensions.")
                dimension = len(embedding)
                embeddings[path] = embedding
            except Exception:
                skipped.append(sample.filename)
            if on_progress is not None:
                on_progress(index, len(samples))

        player, deleted = clips.cleanup_voice_clips(
            session,
            player_id,
            folder,
            embeddings.__getitem__,
            min_sample_similarity=min_sample_similarity,
            min_samples=min_samples,
            eligible_paths=list(embeddings),
        )
        ranked = []
        if player.voice_print_embedding is not None:
            reference = Embedding.model_validate_json(player.voice_print_embedding)
            for sample in samples:
                path = folder / sample.filename
                if sample.filename in deleted or path not in embeddings:
                    continue
                try:
                    similarity = cosine_similarity(embeddings[path], reference)
                    if not math.isfinite(similarity):
                        raise ValueError("Invalid similarity score.")
                    ranked.append(RankedVoiceClip(sample.filename, sample.duration_seconds, similarity))
                except Exception:
                    skipped.append(sample.filename)
        ranked.sort(key=lambda sample: (sample.similarity, sample.filename))
        log.set(ranked_count=len(ranked), deleted_count=len(deleted), skipped_count=len(skipped))
        return VoiceSampleReview(player.name, tuple(ranked), tuple(deleted), tuple(skipped))
