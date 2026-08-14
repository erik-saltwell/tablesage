from __future__ import annotations

import asyncio

import torch

from ...io import load_player, save_player
from ...model.cast import Embedding, Player, VoiceSample
from ...settings import AppSettings, RemoveOutliersSettings


def _recompute_centroid(stacked: torch.Tensor) -> torch.Tensor:
    mean = stacked.mean(dim=0)
    return torch.nn.functional.normalize(mean, p=2, dim=0)


def _prune_outliers(samples: tuple[VoiceSample, ...], min_similarity: float, min_samples: int) -> tuple[tuple[VoiceSample, ...], Embedding]:
    # Embeddings from EmbeddingFactory are already L2-normalized, so cosine similarity = dot product.
    stacked = torch.tensor([s.embedding.root for s in samples], dtype=torch.float32)
    centroid = _recompute_centroid(stacked)
    kept = list(samples)
    while len(kept) > min_samples:
        similarities = stacked @ centroid
        worst_index = int(torch.argmin(similarities).item())
        if float(similarities[worst_index]) >= min_similarity:
            break
        keep_mask = torch.ones(len(kept), dtype=torch.bool)
        keep_mask[worst_index] = False
        stacked = stacked[keep_mask]
        kept = [s for i, s in enumerate(kept) if i != worst_index]
        centroid = _recompute_centroid(stacked)
    centroid_embedding = Embedding(root=tuple(float(x) for x in centroid))
    return tuple(kept), centroid_embedding


async def remove_outliers(campaign_slug: str, player_slug: str, app_settings: AppSettings) -> None:
    settings: RemoveOutliersSettings = app_settings.remove_outliers

    player: Player = await asyncio.to_thread(load_player, campaign_slug, player_slug)
    samples: tuple[VoiceSample, ...] = player.voice_samples

    if len(samples) <= settings.min_samples:
        return

    original_count = len(samples)
    samples, centroid = await asyncio.to_thread(_prune_outliers, samples, settings.min_sample_similarity, settings.min_samples)

    if len(samples) == original_count:
        return

    updated_player = Player(slug=player.slug, name=player.name, voice_samples=samples, centroid=centroid)
    await asyncio.to_thread(save_player, campaign_slug, updated_player)
