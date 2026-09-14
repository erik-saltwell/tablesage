"""A chronological, campaign-wide view of validated Session Scene Breakdowns."""

from __future__ import annotations

import uuid
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

from .previously_on import CampaignHistory
from .session_pipeline.scene_breakdown import Scene

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class CampaignSceneRecap(Record):
    """Every Campaign Scene bracketed by its first opening and final ending."""

    campaign_id: uuid.UUID
    campaign_name: Text
    starting_situation: Text
    scenes: tuple[Scene, ...]
    ending_situation: Text


def create_campaign_scene_recap(campaign_id: uuid.UUID, history: CampaignHistory) -> CampaignSceneRecap:
    """Flatten complete Session breakdowns into Campaign chronology.

    ``CampaignHistory`` is supplied by the application's freshness-aware loader,
    so this transformation performs no I/O and does not mutate managed artifacts.
    """
    if not history.sessions:
        raise ValueError("A Campaign Scene Recap requires at least one Session.")

    ordered_sessions = tuple(sorted(history.sessions, key=lambda item: item.sequence_number))
    return CampaignSceneRecap(
        campaign_id=campaign_id,
        campaign_name=history.campaign_name,
        starting_situation=ordered_sessions[0].breakdown.starting_situation,
        scenes=tuple(scene for campaign_session in ordered_sessions for scene in campaign_session.breakdown.scenes),
        ending_situation=ordered_sessions[-1].breakdown.ending_situation,
    )
