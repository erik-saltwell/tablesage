from __future__ import annotations

import shutil
from pathlib import Path

from ... import _paths
from ...io import save_campaign_set
from ...model.campaign import CampaignSet


def setup_root_dir() -> None:
    root = _paths.data_root()
    campain_set_path = _paths.campaign_set_file()
    campaigns_dir: Path = _paths.campaigns_dir()
    if campaigns_dir.exists() != campain_set_path.exists():
        msg = "Root directory in inavild state!"
        raise RuntimeError(msg)
    _paths.ensure_dir(root)
    _paths.ensure_dir(campaigns_dir)
    if not campain_set_path.exists():
        campaign_set: CampaignSet = CampaignSet(campaigns=())
        save_campaign_set(campaign_set)


def tear_down_root_dir() -> None:
    root = _paths.data_root()
    shutil.rmtree(root)
