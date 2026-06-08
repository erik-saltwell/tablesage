from __future__ import annotations

import asyncio

import pytest
from tablesage_model.model import Campaign, CampaignState, PlayerSet, SessionSet
from tablesage_tui.screens import campaign_detail
from tablesage_tui.screens.campaign_detail import CampaignDetailScreen
from tablesage_tui.widgets.tablesage_header import TableSageHeader
from textual.app import App
from textual.widgets import Static


class _Host(App[None]):
    def __init__(self, screen: CampaignDetailScreen) -> None:
        super().__init__()
        self._screen = screen

    async def on_mount(self) -> None:
        await self.push_screen(self._screen)


def test_campaign_detail_header_shows_campaign_path(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(campaign_detail, "load_session_set", lambda _slug: SessionSet(sessions=()))
    monkeypatch.setattr(campaign_detail, "load_player_set", lambda _slug: PlayerSet(players=()))

    async def scenario() -> None:
        app = _Host(
            CampaignDetailScreen(
                Campaign(
                    slug="iron-pact",
                    name="Iron Pact",
                    description="A grim pact campaign.",
                    system="D&D 5e",
                    default_gm="Ada",
                    state=CampaignState.Active,
                )
            )
        )
        async with app.run_test() as pilot:
            await pilot.pause()

            header = app.screen.query_one(TableSageHeader)
            header_context = header.query_one(".header-context", Static)

            assert header.section == "campaigns / Iron Pact"
            assert str(header_context.render()) == "v0.3.1 · campaigns / Iron Pact"

    asyncio.run(scenario())


def test_campaign_detail_tabs_render_literal_labels(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(campaign_detail, "load_session_set", lambda _slug: SessionSet(sessions=()))
    monkeypatch.setattr(campaign_detail, "load_player_set", lambda _slug: PlayerSet(players=()))

    async def scenario() -> None:
        app = _Host(
            CampaignDetailScreen(
                Campaign(
                    slug="iron-pact",
                    name="Iron Pact",
                    description="A grim pact campaign.",
                    system="D&D 5e",
                    default_gm="Ada",
                    state=CampaignState.Active,
                )
            )
        )
        async with app.run_test() as pilot:
            await pilot.pause()

            labels = [str(tab.render()) for tab in app.screen.query("ContentTab")]

            assert labels == [" overview ", " sessions "]

    asyncio.run(scenario())
