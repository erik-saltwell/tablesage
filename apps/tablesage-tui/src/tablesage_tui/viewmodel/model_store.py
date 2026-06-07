from __future__ import annotations

from typing import Protocol

from tablesage_model.io import create_campaign, load_campaign_summaries
from tablesage_model.model import CampaignSummary
from tablesage_model.setup import setup_root_dir


class ModelStore:
    def load_campaigns(self) -> tuple[CampaignSummary, ...]:
        return load_campaign_summaries()

    def prepare_tablesage_dir(self) -> None:
        setup_root_dir()

    def create_campaign(self, campaign_name: str, default_gm: str, system: str, description: str = "") -> str:
        return create_campaign(campaign_name=campaign_name, default_gm=default_gm, system=system, description=description)


class ModelStoreHost(Protocol):
    @property
    def store(self) -> ModelStore: ...
