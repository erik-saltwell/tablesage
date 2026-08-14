from __future__ import annotations

import asyncio
from pathlib import Path

from tablesage_model.model import CampaignState, CampaignSummary
from tablesage_tui.screens.campaigns import (
    ACTIVE_STATUS_STYLE,
    ARCHIVED_STATUS_STYLE,
    CAMPAIGN_NAME_STYLE,
    CampaignsScreen,
    _format_campaign_cell,
    _format_campaign_state,
)
from textual.app import App


class _Store:
    def __init__(self, campaigns: tuple[CampaignSummary, ...]) -> None:
        self.campaigns = campaigns
        self.deleted_campaign_slugs: list[str] = []
        self.deleted_campaigns_to_clean: tuple[str, ...] = ("iron-pact",)
        self.clean_deleted_campaigns_called = False

    def load_campaigns(self) -> tuple[CampaignSummary, ...]:
        return tuple(campaign for campaign in self.campaigns if campaign.slug not in self.deleted_campaign_slugs)

    def delete_campaign(self, campaign_slug: str) -> None:
        self.deleted_campaign_slugs.append(campaign_slug)

    def list_deleted_campaigns(self) -> tuple[str, ...]:
        return self.deleted_campaigns_to_clean

    def clean_deleted_campaigns(self) -> tuple[str, ...]:
        self.clean_deleted_campaigns_called = True
        return self.deleted_campaigns_to_clean


class _Host(App[None]):
    CSS_PATH = Path(__file__).parents[1] / "src" / "tablesage_tui" / "styles" / "app.tcss"

    def __init__(self, screen: CampaignsScreen, store: _Store) -> None:
        super().__init__()
        self._screen = screen
        self._store = store

    async def on_mount(self) -> None:
        await self.push_screen(self._screen)

    @property
    def store(self) -> _Store:
        return self._store


def _campaign(slug: str = "iron-pact", name: str = "Iron Pact") -> CampaignSummary:
    return CampaignSummary(slug=slug, name=name, description="A grim pact campaign")


def test_format_campaign_state_uses_green_dot_for_active() -> None:
    cell = _format_campaign_state(CampaignState.Active)

    assert cell.plain == "●"
    assert cell.style == ACTIVE_STATUS_STYLE


def test_format_campaign_state_uses_grey_dot_for_archived() -> None:
    cell = _format_campaign_state(CampaignState.Archived)

    assert cell.plain == "●"
    assert cell.style == ARCHIVED_STATUS_STYLE


def test_format_campaign_cell_renders_name_and_description_on_separate_lines() -> None:
    campaign = _campaign()

    cell = _format_campaign_cell(campaign)

    assert cell.plain == "Iron Pact\nA grim pact campaign"
    assert cell.no_wrap is True
    assert cell.overflow == "crop"
    assert cell.spans[0].start == 0
    assert cell.spans[0].end == len("Iron Pact")
    assert cell.spans[0].style == CAMPAIGN_NAME_STYLE


def test_delete_campaign_binding_requires_highlighted_campaign() -> None:
    screen = CampaignsScreen(())

    assert screen.check_action("delete_campaign", ()) is False

    screen.highlighted_campaign_slug = "iron-pact"

    assert screen.check_action("delete_campaign", ()) is True


def test_delete_campaign_confirmation_calls_store_delete() -> None:
    async def scenario() -> None:
        campaigns = (_campaign(),)
        store = _Store(campaigns)
        screen = CampaignsScreen(campaigns)
        app = _Host(screen, store)
        async with app.run_test() as pilot:
            await pilot.pause()

            screen.action_delete_campaign()
            await pilot.pause()

            await pilot.click("#confirmation-yes")
            await pilot.pause()

            assert store.deleted_campaign_slugs == ["iron-pact"]
            assert screen.campaigns == ()

    asyncio.run(scenario())


def test_clean_deleted_campaigns_requires_confirmation_when_campaigns_are_pending_cleanup() -> None:
    async def scenario() -> None:
        campaigns = (_campaign(),)
        store = _Store(campaigns)
        screen = CampaignsScreen(campaigns)
        app = _Host(screen, store)
        async with app.run_test() as pilot:
            await pilot.pause()

            screen.action_clean_deleted_campaigns()
            await pilot.pause()

            assert store.clean_deleted_campaigns_called is False

            await pilot.click("#confirmation-yes")
            await pilot.pause()

            assert store.clean_deleted_campaigns_called is True

    asyncio.run(scenario())


def test_clean_deleted_campaigns_skips_confirmation_when_no_campaigns_are_pending_cleanup() -> None:
    async def scenario() -> None:
        campaigns = (_campaign(),)
        store = _Store(campaigns)
        store.deleted_campaigns_to_clean = ()
        screen = CampaignsScreen(campaigns)
        app = _Host(screen, store)
        async with app.run_test() as pilot:
            await pilot.pause()

            screen.action_clean_deleted_campaigns()
            await pilot.pause()

            assert store.clean_deleted_campaigns_called is False
            assert not list(app.screen.query("#confirmation-yes"))

    asyncio.run(scenario())
