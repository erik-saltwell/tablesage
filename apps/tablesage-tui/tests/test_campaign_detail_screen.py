from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from tablesage_model.model import (
    Campaign,
    CampaignState,
    GlossaryEntry,
    SessionSet,
)
from tablesage_tui.screens import campaign_detail
from tablesage_tui.screens.campaign_detail import CampaignDetailScreen
from tablesage_tui.widgets import CampaignStateWidget, GlossaryEntryWidget
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


def test_delete_glossary_entry_uses_delete_key_binding() -> None:
    binding = next(binding for binding in CampaignDetailScreen.BINDINGS if binding.action == "delete_glossary_entry")

    assert binding.key == "delete"
    assert binding.key_display == "Del"


def test_campaign_detail_has_no_player_bindings() -> None:
    player_actions = {
        "add_player",
        "delete_player",
        "update_player_name",
        "add_clips_from_folder",
        "add_clips_from_session",
        "recompute_speechprint",
    }

    bound_actions = {binding.action for binding in CampaignDetailScreen.BINDINGS}

    assert bound_actions.isdisjoint(player_actions)


def test_campaign_detail_starts_not_dirty(monkeypatch: pytest.MonkeyPatch) -> None:
    _stub_loaders(monkeypatch)

    async def scenario() -> None:
        detail_screen = CampaignDetailScreen(_campaign())
        app = _Host(detail_screen)
        async with app.run_test() as pilot:
            await pilot.pause()

            assert detail_screen.is_dirty is False

    asyncio.run(scenario())


def test_campaign_detail_metadata_input_changes_mark_screen_dirty(monkeypatch: pytest.MonkeyPatch) -> None:
    _stub_loaders(monkeypatch)

    async def scenario() -> None:
        detail_screen = CampaignDetailScreen(_campaign())
        app = _Host(detail_screen)
        async with app.run_test() as pilot:
            await pilot.pause()

            app.screen.query_one("#description-input", Input).value = "A changed description."
            await pilot.pause()

            assert detail_screen.campaign.description == "A changed description."
            assert detail_screen.is_dirty is True

    asyncio.run(scenario())


def test_campaign_detail_gm_and_system_input_changes_mark_screen_dirty(monkeypatch: pytest.MonkeyPatch) -> None:
    _stub_loaders(monkeypatch)

    async def scenario() -> None:
        detail_screen = CampaignDetailScreen(_campaign())
        app = _Host(detail_screen)
        async with app.run_test() as pilot:
            await pilot.pause()

            app.screen.query_one("#input-gm", Input).value = "Bex"
            app.screen.query_one("#input-system", Input).value = "Blades"
            await pilot.pause()

            assert detail_screen.campaign.default_gm == "Bex"
            assert detail_screen.campaign.system == "Blades"
            assert detail_screen.is_dirty is True

    asyncio.run(scenario())


def test_campaign_detail_state_change_marks_screen_dirty(monkeypatch: pytest.MonkeyPatch) -> None:
    _stub_loaders(monkeypatch)

    async def scenario() -> None:
        detail_screen = CampaignDetailScreen(_campaign())
        app = _Host(detail_screen)
        async with app.run_test() as pilot:
            await pilot.pause()

            detail_screen._on_campaign_state_changed(CampaignStateWidget.StateChanged(CampaignState.Archived))

            assert detail_screen.campaign.state == CampaignState.Archived
            assert detail_screen.is_dirty is True

    asyncio.run(scenario())


def test_campaign_detail_name_change_marks_screen_dirty(monkeypatch: pytest.MonkeyPatch) -> None:
    _stub_loaders(monkeypatch)

    async def scenario() -> None:
        detail_screen = CampaignDetailScreen(_campaign())
        app = _Host(detail_screen)
        async with app.run_test() as pilot:
            await pilot.pause()

            detail_screen._replace_campaign(name="Sable Crown")

            assert detail_screen.campaign.name == "Sable Crown"
            assert detail_screen.is_dirty is True

    asyncio.run(scenario())


def test_glossary_selection_enables_only_glossary_bindings(monkeypatch: pytest.MonkeyPatch) -> None:
    _stub_loaders(monkeypatch)

    async def scenario() -> None:
        detail_screen = CampaignDetailScreen(_campaign(glossary=(GlossaryEntry(term="Quarl", description="A lich-king."),)))
        app = _Host(detail_screen)
        async with app.run_test() as pilot:
            await pilot.pause()

            assert detail_screen.check_action("edit_glossary_entry", ()) is False
            assert detail_screen.check_action("delete_glossary_entry", ()) is False

            app.screen.query_one(GlossaryEntryWidget).focus()
            await pilot.pause()

            assert detail_screen._selected_glossary_term == "Quarl"
            assert detail_screen.check_action("edit_glossary_entry", ()) is True
            assert detail_screen.check_action("delete_glossary_entry", ()) is True

    asyncio.run(scenario())


def test_campaign_detail_renders_glossary_summary_without_player_summary(monkeypatch: pytest.MonkeyPatch) -> None:
    _stub_loaders(monkeypatch)

    async def scenario() -> None:
        detail_screen = CampaignDetailScreen(_campaign(glossary=(GlossaryEntry(term="Quarl", description="A lich-king."),)))
        app = _Host(detail_screen)
        async with app.run_test() as pilot:
            await pilot.pause()

            assert list(app.screen.query("#player-summary")) == []
            assert list(app.screen.query("#player-list")) == []
            assert list(app.screen.query("#glossary-summary"))

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


def test_add_glossary_entry_updates_campaign_glossary(monkeypatch: pytest.MonkeyPatch) -> None:
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

            assert detail_screen.campaign.glossary == (GlossaryEntry(term="Quarl", description="A lich-king."),)
            assert detail_screen.is_dirty is True
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

            assert detail_screen.campaign.glossary == (GlossaryEntry(term="Veyra", description="A queen in exile."),)
            assert detail_screen.is_dirty is True
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

            assert detail_screen.campaign.glossary == (entry,)

            await pilot.click("#confirm-delete-glossary-entry")
            await pilot.pause()

            assert detail_screen.campaign.glossary == ()
            assert detail_screen.is_dirty is True
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
            assert detail_screen.campaign.glossary == (GlossaryEntry(term="Quarl", description="A lich-king."),)

    asyncio.run(scenario())
