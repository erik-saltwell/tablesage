from __future__ import annotations

from tablesage_model.io import load_campaign_set
from tablesage_model.model import CampaignSet
from tablesage_model.setup import setup_root_dir


class ModelStore:
    def load_campaigns(self) -> CampaignSet:
        return load_campaign_set()

    def prepare_tablesage_dir(self) -> None:
        setup_root_dir()
