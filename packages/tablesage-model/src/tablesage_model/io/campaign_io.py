from __future__ import annotations

import shutil
from pathlib import Path

from .. import _paths
from ..model.campaign import Campaign, CampaignSet
from .campaign_set_io import load_campaign_set, save_campaign_set
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


def delete_campaign(campaign_slug: str) -> None:
    current = load_campaign_set()
    remaining = tuple(c for c in current.campaigns if c.slug != campaign_slug)
    save_campaign_set(CampaignSet(campaigns=remaining))


def cleanup_orphan_campaign_dirs() -> tuple[str, ...]:
    root = _paths.campaigns_dir()
    if not root.exists():
        return ()
    known = {c.slug for c in load_campaign_set().campaigns}
    deleted: list[str] = []
    for child in sorted(root.iterdir()):
        if child.is_dir() and child.name not in known:
            shutil.rmtree(child)
            deleted.append(child.name)
    return tuple(deleted)
