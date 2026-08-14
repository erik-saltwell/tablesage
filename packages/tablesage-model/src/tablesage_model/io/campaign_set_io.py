from __future__ import annotations

from pathlib import Path

from .. import _paths
from ..model.campaign import CampaignSet
from .yaml_io import load_model_from_yaml, save_model_to_yaml


def load_campaign_set() -> CampaignSet:
    file_path: Path = _paths.campaign_set_file()
    if not file_path.exists():
        raise FileNotFoundError(file_path)
    if not file_path.is_file():
        raise IsADirectoryError(file_path)
    return load_model_from_yaml(file_path, CampaignSet)


def save_campaign_set(campaign_set: CampaignSet) -> None:
    file_path: Path = _paths.campaign_set_file()
    if file_path.is_dir():
        raise IsADirectoryError(file_path)
    save_model_to_yaml(file_path, campaign_set)
