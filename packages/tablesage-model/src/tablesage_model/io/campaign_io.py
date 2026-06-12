from __future__ import annotations

import shutil
from pathlib import Path

from .. import _paths
from ..model.campaign import Campaign, CampaignName, CampaignSet, CampaignSummary, SessionSet
from ..model.cast import PlayerSet
from .campaign_set_io import load_campaign_set, save_campaign_set
from .player_set_io import load_player_set, save_player_set
from .session_set_io import load_session_set, save_session_set
from .yaml_io import load_model_from_yaml, save_model_to_yaml


def create_campaign(campaign_name: str, default_gm: str, system: str, description: str = "") -> str:
    campaign_slug: str = _paths.slugify(campaign_name)
    if _paths.campaign_dir(campaign_slug).exists():
        raise FileExistsError(f"A campaign with slug '{campaign_slug}' already exists")
    new_campaign_name: CampaignName = CampaignName(slug=campaign_slug, name=campaign_name)
    campaign: Campaign = Campaign(
        slug=campaign_slug,
        name=campaign_name,
        description=description,
        default_gm=default_gm,
        system=system,
    )

    # Build the campaign workspace fully before committing it to the campaign set, so a
    # partial scaffold leaves only an orphan dir (swept by cleanup_orphan_campaign_dirs)
    # rather than a set entry pointing at a broken campaign.
    save_campaign(campaign)
    save_session_set(campaign_slug, SessionSet(sessions=()))
    save_player_set(campaign_slug, PlayerSet(players=()))

    current: CampaignSet = load_campaign_set()
    updated: CampaignSet = CampaignSet(campaigns=(*current.campaigns, new_campaign_name))
    save_campaign_set(updated)
    return campaign_slug


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


def load_campaign_summaries() -> tuple[CampaignSummary, ...]:
    """Assemble a CampaignSummary for every campaign in the set index.

    Reads the campaign set once, then per campaign loads its campaign, session set, and
    player set (three file reads each) to build the summary. The returned tuple preserves
    the set index order; sorting is left to callers.

    Fail-fast: any campaign listed in the set whose detail files are missing or corrupt
    propagates the underlying error rather than degrading the whole list. This is safe
    because create_campaign builds a campaign's workspace fully before adding its slug to
    the set, so a slug in the set must always have complete files.
    """
    campaign_set: CampaignSet = load_campaign_set()
    summaries: list[CampaignSummary] = []
    for entry in campaign_set.campaigns:
        campaign: Campaign = load_campaign(entry.slug)
        session_set: SessionSet = load_session_set(entry.slug)
        player_set: PlayerSet = load_player_set(entry.slug)
        session_dates = [session.session_date for session in session_set.sessions]
        summaries.append(
            CampaignSummary(
                slug=campaign.slug,
                name=entry.name,
                description=campaign.description,
                default_gm=campaign.default_gm,
                system=campaign.system,
                state=campaign.state,
                first_session_date=min(session_dates) if session_dates else None,
                last_session_date=max(session_dates) if session_dates else None,
                session_count=len(session_set.sessions),
                player_count=len(player_set.players),
            )
        )
    return tuple(summaries)


def save_campaign(campaign: Campaign) -> None:
    file_path: Path = _paths.campaign_file(campaign.slug)
    if file_path.is_dir():
        raise IsADirectoryError(file_path)
    _paths.ensure_dir(file_path.parent)
    save_model_to_yaml(file_path, campaign)


def delete_campaign(campaign_slug: str) -> None:
    current = load_campaign_set()
    remaining = tuple(c for c in current.campaigns if c.slug != campaign_slug)
    save_campaign_set(CampaignSet(campaigns=remaining))


def list_orphan_campaign_dirs() -> tuple[str, ...]:
    root = _paths.campaigns_dir()
    if not root.exists():
        return ()
    known = {c.slug for c in load_campaign_set().campaigns}
    return tuple(child.name for child in sorted(root.iterdir()) if child.is_dir() and child.name not in known)


def cleanup_orphan_campaign_dirs() -> tuple[str, ...]:
    deleted = list_orphan_campaign_dirs()
    for campaign_slug in deleted:
        shutil.rmtree(_paths.campaign_dir(campaign_slug))
    return deleted
