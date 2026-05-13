from __future__ import annotations

from pathlib import Path

from .. import _paths
from ..model.campaign import Campaign
from .yaml_io import load_model_from_yaml, save_model_to_yaml


def load_campaign(campaign_slug: str) -> Campaign:
    file_path: Path = _paths.campaign_file(campaign_slug)
    if not file_path.exists():
        raise FileNotFoundError(file_path)
    if not file_path.is_file():
        raise IsADirectoryError(file_path)
    campaign = load_model_from_yaml(file_path, Campaign)
    if campaign.slug != campaign_slug:
        raise ValueError(f"Slug mismatch: directory is '{campaign_slug}', file says '{campaign.slug}'")
    return campaign


def save_campaign(campaign: Campaign) -> None:
    file_path: Path = _paths.campaign_file(campaign.slug)
    if file_path.is_dir():
        raise IsADirectoryError(file_path)
    save_model_to_yaml(file_path, campaign)
