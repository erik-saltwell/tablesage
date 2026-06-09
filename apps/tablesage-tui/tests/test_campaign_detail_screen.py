from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from tablesage_model.model import Campaign, CampaignState, GlossaryEntry, PlayerSet, SessionSet
from tablesage_tui.screens import campaign_detail
from tablesage_tui.screens.campaign_detail import CampaignDetailScreen
from tablesage_tui.widgets import GlossaryEntryWidget
from tablesage_tui.widgets.tablesage_header import TableSageHeader
from textual.app import App
from textual.widgets import Input, Static, TextArea


class _Host(App[None]):
    CSS_PATH = Path(__file__).parents[1] / "src" / "tablesage_tui" / "styles" / "app.tcss"

    def __init__(self, screen: CampaignDetailScreen) -> None:
        super().__init__()
        self._screen = screen

    async def on_mount(self) -> None:
        await self.push_screen(self._screen)


def _campaign(glossary: tuple[GlossaryEntry, ...] = ()) -> Campaign:
    return Campaign(
        slug="iron-pact",
        name="Iron Pact",
        description="A grim pact campaign.",
        system="D&D 5e",
        default_gm="Ada",
        state=CampaignState.Active,
        glossary=glossary,
    )


def _stub_loaders(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(campaign_detail, "load_session_set", lambda _slug: SessionSet(sessions=()))
    monkeypatch.setattr(campaign_detail, "load_player_set", lambda _slug: PlayerSet(players=()))


def test_campaign_detail_header_shows_campaign_path(monkeypatch: pytest.MonkeyPatch) -> None:
    _stub_loaders(monkeypatch)

    async def scenario() -> None:
        app = _Host(CampaignDetailScreen(_campaign()))
        async with app.run_test() as pilot:
            await pilot.pause()

            header = app.screen.query_one(TableSageHeader)
            header_context = header.query_one(".header-context", Static)

            assert header.section == "campaigns / Iron Pact"
            assert str(header_context.render()) == "v0.3.1 · campaigns / Iron Pact"

    asyncio.run(scenario())


def test_campaign_detail_tabs_render_literal_labels(monkeypatch: pytest.MonkeyPatch) -> None:
    _stub_loaders(monkeypatch)

    async def scenario() -> None:
        app = _Host(CampaignDetailScreen(_campaign()))
        async with app.run_test() as pilot:
            await pilot.pause()

            labels = [str(tab.render()) for tab in app.screen.query("ContentTab")]

            assert labels == [" overview ", " sessions "]

    asyncio.run(scenario())


def test_campaign_detail_renders_sorted_glossary_entry_widgets(monkeypatch: pytest.MonkeyPatch) -> None:
    _stub_loaders(monkeypatch)

    async def scenario() -> None:
        app = _Host(
            CampaignDetailScreen(
                _campaign(
                    glossary=(
                        GlossaryEntry(term="Zephyr", description="A fast airship."),
                        GlossaryEntry(term="Aster", description="A hidden city."),
                    )
                )
            )
        )
        async with app.run_test() as pilot:
            await pilot.pause()

            entries = list(app.screen.query(GlossaryEntryWidget))

            assert [entry.term for entry in entries] == ["Aster", "Zephyr"]
            assert str(entries[0].query_one(".glossary-entry-term", Static).render()) == "Aster"
            assert str(entries[0].query_one(".glossary-entry-description", Static).render()) == "A hidden city."
            assert list(app.screen.query("#add-glossary-entry")) == []

    asyncio.run(scenario())


def test_add_glossary_entry_updates_screen_glossary_without_changing_campaign(monkeypatch: pytest.MonkeyPatch) -> None:
    _stub_loaders(monkeypatch)

    async def scenario() -> None:
        campaign = _campaign()
        detail_screen = CampaignDetailScreen(campaign)
        app = _Host(detail_screen)
        async with app.run_test() as pilot:
            await pilot.pause()
            detail_screen.action_add_glossary_entry()
            await pilot.pause()

            app.screen.query_one("#glossary-term", Input).value = "Quarl"
            app.screen.query_one("#glossary-description", TextArea).text = "A lich-king."
            await pilot.click("#save-glossary-entry")
            await pilot.pause()

            assert detail_screen.glossary == (GlossaryEntry(term="Quarl", description="A lich-king."),)
            assert campaign.glossary == ()
            assert app.screen.query_one(GlossaryEntryWidget).term == "Quarl"

    asyncio.run(scenario())


def test_edit_glossary_entry_can_rename_term_in_screen_glossary(monkeypatch: pytest.MonkeyPatch) -> None:
    _stub_loaders(monkeypatch)

    async def scenario() -> None:
        detail_screen = CampaignDetailScreen(_campaign(glossary=(GlossaryEntry(term="Quarl", description="A lich-king."),)))
        app = _Host(detail_screen)
        async with app.run_test() as pilot:
            await pilot.pause()

            detail_screen._selected_glossary_term = "Quarl"
            detail_screen.action_edit_glossary_entry()
            await pilot.pause()

            app.screen.query_one("#glossary-term", Input).value = "Veyra"
            app.screen.query_one("#glossary-description", TextArea).text = "A queen in exile."
            await pilot.click("#save-glossary-entry")
            await pilot.pause()

            assert detail_screen.glossary == (GlossaryEntry(term="Veyra", description="A queen in exile."),)
            assert app.screen.query_one(GlossaryEntryWidget).term == "Veyra"

    asyncio.run(scenario())


def test_delete_glossary_entry_requires_confirmation(monkeypatch: pytest.MonkeyPatch) -> None:
    _stub_loaders(monkeypatch)

    async def scenario() -> None:
        entry = GlossaryEntry(term="Quarl", description="A lich-king.")
        detail_screen = CampaignDetailScreen(_campaign(glossary=(entry,)))
        app = _Host(detail_screen)
        async with app.run_test() as pilot:
            await pilot.pause()

            detail_screen._selected_glossary_term = "Quarl"
            detail_screen.action_delete_glossary_entry()
            await pilot.pause()

            assert detail_screen.glossary == (entry,)

            await pilot.click("#confirm-delete-glossary-entry")
            await pilot.pause()

            assert detail_screen.glossary == ()
            assert list(app.screen.query(GlossaryEntryWidget)) == []

    asyncio.run(scenario())


def test_duplicate_glossary_term_keeps_dialog_open(monkeypatch: pytest.MonkeyPatch) -> None:
    _stub_loaders(monkeypatch)

    async def scenario() -> None:
        detail_screen = CampaignDetailScreen(_campaign(glossary=(GlossaryEntry(term="Quarl", description="A lich-king."),)))
        app = _Host(detail_screen)
        async with app.run_test() as pilot:
            await pilot.pause()
            detail_screen.action_add_glossary_entry()
            await pilot.pause()

            app.screen.query_one("#glossary-term", Input).value = "Quarl"
            app.screen.query_one("#glossary-description", TextArea).text = "Duplicate."
            await pilot.click("#save-glossary-entry")
            await pilot.pause()

            error = app.screen.query_one("#glossary-entry-error", Static)
            assert "already exists" in str(error.render())
            assert detail_screen.glossary == (GlossaryEntry(term="Quarl", description="A lich-king."),)

    asyncio.run(scenario())
