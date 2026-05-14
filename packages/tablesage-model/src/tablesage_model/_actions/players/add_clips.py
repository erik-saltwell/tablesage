from __future__ import annotations

import asyncio
import shutil
from pathlib import Path

from ... import _paths
from ..._tools.embeddings import EmbeddingFactory, compute_centroid
from ...io import save_player
from ...model.cast import Embedding, Player, VoiceSample


def _get_source_files(clip_directory: Path) -> list[Path]:
    return [path for path in sorted(clip_directory.glob("*.wav")) if path.is_file()]


async def add_clips(campaign_slug: str, player_slug: str, player_name: str, clip_directory: Path) -> None:
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

    embeddings_factory: EmbeddingFactory = EmbeddingFactory()
    voice_samples: list[VoiceSample] = []
    voice_clip_path = _paths.voice_clips_dir(campaign_slug, player_slug)
    _paths.ensure_dir(voice_clip_path)
    player_file_path: Path = _paths.player_file(campaign_slug, player_slug)
    for source_path in sources:
        filename: str = _paths.generate_voice_sample_filename()
        target_path: Path = voice_clip_path / filename
        shutil.copy2(source_path, target_path)
        embedding: Embedding = await embeddings_factory.extract_async(target_path)
        relative_target_path = target_path.relative_to(player_file_path.parent)
        voice_sample: VoiceSample = VoiceSample(filepath=relative_target_path, embedding=embedding)
        voice_samples.append(voice_sample)
    centroid = await asyncio.to_thread(compute_centroid, [s.embedding for s in voice_samples])
    player: Player = Player(slug=player_slug, name=player_name, voice_samples=tuple(voice_samples), centroid=centroid)
    save_player(campaign_slug, player)
