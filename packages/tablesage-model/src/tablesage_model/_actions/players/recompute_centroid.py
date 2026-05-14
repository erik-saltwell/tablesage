from __future__ import annotations

import asyncio

from ..._tools.embeddings import compute_centroid
from ...io import load_player, save_player


async def recompute_centroid(campaign_slug: str, player_slug: str) -> None:
    player = load_player(campaign_slug, player_slug)
    if not player.voice_samples:
        return
    centroid = await asyncio.to_thread(compute_centroid, [s.embedding for s in player.voice_samples])
    save_player(
        campaign_slug,
        player.model_copy(update={"centroid": centroid}),
    )
