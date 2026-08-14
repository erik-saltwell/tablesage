from __future__ import annotations

from typing import Protocol

from tablesage_model.io import (
    cleanup_orphan_campaign_dirs,
    create_campaign,
    delete_campaign,
    list_orphan_campaign_dirs,
    load_campaign,
    load_campaign_summaries,
    load_session,
    load_session_set,
)
from tablesage_model.model import Campaign, CampaignSummary, Session
from tablesage_model.setup import setup_root_dir


class ModelStore:
    def load_campaigns(self) -> tuple[CampaignSummary, ...]:
        return load_campaign_summaries()

    def load_campaign(self, campaign_slug: str) -> Campaign:
        return load_campaign(campaign_slug)

    def get_last_session_for_campaign(self, campaign_slug: str) -> Session:
        sessions = sorted(load_session_set(campaign_slug).sessions, key=lambda session: session.session_date, reverse=True)
        if not sessions:
            raise LookupError(f"Campaign '{campaign_slug}' has no sessions")
        return load_session(campaign_slug, sessions[0].slug)

    def prepare_tablesage_dir(self) -> None:
        setup_root_dir()

    def create_campaign(self, campaign_name: str, default_gm: str, system: str, description: str = "") -> str:
        return create_campaign(campaign_name=campaign_name, default_gm=default_gm, system=system, description=description)

    def delete_campaign(self, campaign_slug: str) -> None:
        delete_campaign(campaign_slug)

    def list_deleted_campaigns(self) -> tuple[str, ...]:
        return list_orphan_campaign_dirs()

    def clean_deleted_campaigns(self) -> tuple[str, ...]:
        return cleanup_orphan_campaign_dirs()


class ModelStoreHost(Protocol):
    @property
    def store(self) -> ModelStore: ...
