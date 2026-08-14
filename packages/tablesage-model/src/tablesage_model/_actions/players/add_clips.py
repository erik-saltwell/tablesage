from __future__ import annotations

import asyncio
import shutil
from pathlib import Path

from ... import _paths
from ..._tools.embeddings import EmbeddingFactory, compute_centroid
from ..._tools.ffmpeg import clean_clip
from ...io import load_player, save_player
from ...model.cast import Embedding, Player, ProvenanceType, VoiceSample
from .enhance_voices import delete_voice_samples_by_source


def _get_source_files(clip_directory: Path) -> list[Path]:
    return [path for path in sorted(clip_directory.glob("*.wav")) if path.is_file()]


async def add_clips(
    campaign_slug: str,
    player_slug: str,
    player_name: str,
    clip_directory: Path,
    *,
    clean_clips: bool = False,
) -> None:
    if not clip_directory.exists():
        msg = f"Cannot add clips from {clip_directory} because it does not exist"
        raise ValueError(msg)

    if not clip_directory.is_dir():
        msg = f"Cannot add clips from {clip_directory} because it is not a directory"
        raise ValueError(msg)

    sources: list[Path] = _get_source_files(clip_directory)
    if not sources:
        msg = "Cannot add clips from directory with no .wav files"
        raise ValueError(msg)

    source_id = str(clip_directory.resolve())
    player_dir = _paths.player_dir(campaign_slug, player_slug)

    try:
        existing_player = load_player(campaign_slug, player_slug)
    except FileNotFoundError:
        retained: tuple[VoiceSample, ...] = ()
    else:
        retraction = delete_voice_samples_by_source(existing_player, source=source_id, provenance_type=ProvenanceType.IMPORT)
        for removed_sample in retraction.removed:
            (player_dir / removed_sample.filepath).unlink(missing_ok=True)
        retained = retraction.kept.voice_samples

    embeddings_factory: EmbeddingFactory = EmbeddingFactory()
    new_samples: list[VoiceSample] = []
    voice_clip_path = _paths.voice_clips_dir(campaign_slug, player_slug)
    _paths.ensure_dir(voice_clip_path)
    for index, source_path in enumerate(sources):
        filename: str = _paths.generate_voice_sample_filename()
        target_path: Path = voice_clip_path / filename
        if clean_clips:
            await clean_clip(source_path, target_path, normalize=False)
        else:
            shutil.copy2(source_path, target_path)
        embedding: Embedding = await embeddings_factory.extract_async(target_path)
        relative_target_path = target_path.relative_to(player_dir)
        new_samples.append(
            VoiceSample(
                filepath=relative_target_path,
                embedding=embedding,
                provenance_type=ProvenanceType.IMPORT,
                source=source_id,
                index=index,
            )
        )

    unioned = (*retained, *new_samples)
    centroid = await asyncio.to_thread(compute_centroid, [s.embedding for s in unioned])
    save_player(
        campaign_slug,
        Player(slug=player_slug, name=player_name, voice_samples=unioned, centroid=centroid),
    )
