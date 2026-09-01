from datetime import date
from unittest.mock import MagicMock

import pytest
from tablesage_application.paths import ArtifactName
from tablesage_model.model import Campaign, CampaignPlayer, GlossaryEntry, Player
from tablesage_model.model import Session as GameSession
from tablesage_tui.dialogs import ConfirmationDialog, GlossaryEntryDialog, PlayerPickerDialog, RolePickerDialog, TextInputDialog
from tablesage_tui.screens.campaign_detail import CampaignDetailScreen
from tablesage_tui.screens.main_app import TableSageApp
from tablesage_tui.screens.session_detail import SessionDetailScreen
from tablesage_tui.widgets import CommittingInput
from textual.widgets import Button, DataTable, Input, Static


def _application(
    *,
    campaign: Campaign | None = None,
    roster: list[tuple[CampaignPlayer, Player]] | None = None,
    sessions: list[GameSession] | None = None,
    glossary: list[GlossaryEntry] | None = None,
    players: list[Player] | None = None,
) -> MagicMock:
    campaign = campaign or Campaign(name="Iron Pact")
    return MagicMock(
        get_campaign=MagicMock(return_value=campaign),
        list_roster=MagicMock(return_value=roster or []),
        list_sessions=MagicMock(return_value=sessions or []),
        list_glossary_entries=MagicMock(return_value=glossary or []),
        list_players=MagicMock(return_value=players or []),
        # Sensible defaults so navigating into a real SessionDetailScreen
        # (opened by N/E on the Sessions tab) doesn't crash on mount.
        get_session=MagicMock(return_value=GameSession(campaign_id=campaign.id, sequence_number=1, name="Session")),
        list_attendance=MagicMock(return_value=[]),
        session_artifacts=MagicMock(return_value=dict.fromkeys(ArtifactName, False)),
        can_transcribe_audio=MagicMock(return_value=(False, "Import input audio first.")),
        next_generation_step=MagicMock(return_value=None),
        can_export_artifacts=MagicMock(return_value=(False, "No artifacts to export yet.")),
        campaign_folder_exists=MagicMock(return_value=False),
        session_folder_would_collide=MagicMock(return_value=False),
    )


@pytest.mark.anyio
async def test_sessions_is_the_default_tab() -> None:
    campaign = Campaign(name="Iron Pact")
    application = _application(campaign=campaign)

    async with TableSageApp(application).run_test() as pilot:
        pilot.app.push_screen(CampaignDetailScreen(campaign.id))
        await pilot.pause()

        screen = pilot.app.screen
        assert isinstance(screen, CampaignDetailScreen)
        assert screen._active_tab == "sessions"


@pytest.mark.anyio
async def test_metadata_inputs_are_prefilled() -> None:
    campaign = Campaign(name="Iron Pact", description="A grim war", game_system="Dungeon World")
    application = _application(campaign=campaign)

    async with TableSageApp(application).run_test() as pilot:
        pilot.app.push_screen(CampaignDetailScreen(campaign.id))
        await pilot.pause()

        screen = pilot.app.screen
        assert screen.query_one("#campaign-name-input", Input).value == "Iron Pact"
        assert screen.query_one("#campaign-description-input", Input).value == "A grim war"
        assert screen.query_one("#campaign-game-system-input", Input).value == "Dungeon World"


@pytest.mark.anyio
async def test_typing_a_tab_letter_into_a_field_does_not_switch_tabs() -> None:
    campaign = Campaign(name="Iron Pact")
    application = _application(campaign=campaign)

    async with TableSageApp(application).run_test() as pilot:
        pilot.app.push_screen(CampaignDetailScreen(campaign.id))
        await pilot.pause()

        screen = pilot.app.screen
        assert isinstance(screen, CampaignDetailScreen)
        description = screen.query_one("#campaign-description-input", CommittingInput)
        description.focus()
        await pilot.pause()

        await pilot.press("r")
        await pilot.pause()

        assert description.value == "r"
        assert screen._active_tab == "sessions"


@pytest.mark.anyio
async def test_rs_g_switch_tabs_when_a_table_has_focus() -> None:
    campaign = Campaign(name="Iron Pact")
    application = _application(campaign=campaign)

    async with TableSageApp(application).run_test() as pilot:
        pilot.app.push_screen(CampaignDetailScreen(campaign.id))
        await pilot.pause()

        screen = pilot.app.screen
        assert isinstance(screen, CampaignDetailScreen)
        await pilot.press("r")
        await pilot.pause()
        assert screen._active_tab == "roster"

        await pilot.press("g")
        await pilot.pause()
        assert screen._active_tab == "glossary"

        await pilot.press("s")
        await pilot.pause()
        assert screen._active_tab == "sessions"


@pytest.mark.anyio
async def test_tabs_are_mouse_clickable() -> None:
    campaign = Campaign(name="Iron Pact")
    application = _application(campaign=campaign)

    async with TableSageApp(application).run_test() as pilot:
        pilot.app.push_screen(CampaignDetailScreen(campaign.id))
        await pilot.pause()

        screen = pilot.app.screen
        assert isinstance(screen, CampaignDetailScreen)

        await pilot.click("#tab-label-roster")
        await pilot.pause()
        assert screen._active_tab == "roster"

        await pilot.click("#tab-label-glossary")
        await pilot.pause()
        assert screen._active_tab == "glossary"

        await pilot.click("#tab-label-sessions")
        await pilot.pause()
        assert screen._active_tab == "sessions"


@pytest.mark.anyio
async def test_renaming_commits_on_blur() -> None:
    campaign = Campaign(name="Iron Pact")
    application = _application(campaign=campaign)
    application.rename_campaign = MagicMock(return_value=Campaign(id=campaign.id, name="Iron Pact Reforged"))

    async with TableSageApp(application).run_test() as pilot:
        pilot.app.push_screen(CampaignDetailScreen(campaign.id))
        await pilot.pause()

        name_input = pilot.app.screen.query_one("#campaign-name-input", CommittingInput)
        name_input.focus()
        await pilot.pause()
        name_input.value = "Iron Pact Reforged"

        await pilot.press("tab")
        await pilot.pause()

        application.rename_campaign.assert_called_once_with(campaign.id, "Iron Pact Reforged")


@pytest.mark.anyio
async def test_duplicate_rename_shows_error_and_resets_value() -> None:
    campaign = Campaign(name="Iron Pact")
    application = _application(campaign=campaign)
    application.rename_campaign = MagicMock(side_effect=ValueError("A campaign named 'Ashen Crown' already exists."))

    async with TableSageApp(application).run_test() as pilot:
        pilot.app.push_screen(CampaignDetailScreen(campaign.id))
        await pilot.pause()

        name_input = pilot.app.screen.query_one("#campaign-name-input", CommittingInput)
        name_input.focus()
        await pilot.pause()
        name_input.value = "Ashen Crown"

        await pilot.press("tab")
        await pilot.pause()

        assert name_input.value == "Iron Pact"


@pytest.mark.anyio
async def test_rename_folder_collision_prompts_then_deletes_and_renames() -> None:
    campaign = Campaign(name="Iron Pact")
    application = _application(campaign=campaign)
    application.campaign_folder_exists = MagicMock(return_value=True)
    application.delete_orphan_campaign_folder = MagicMock()
    application.rename_campaign = MagicMock(return_value=Campaign(id=campaign.id, name="Ashen Crown"))

    async with TableSageApp(application).run_test() as pilot:
        pilot.app.push_screen(CampaignDetailScreen(campaign.id))
        await pilot.pause()

        name_input = pilot.app.screen.query_one("#campaign-name-input", CommittingInput)
        name_input.focus()
        await pilot.pause()
        name_input.value = "Ashen Crown"

        await pilot.press("tab")
        await pilot.pause()

        assert isinstance(pilot.app.screen, ConfirmationDialog)
        application.rename_campaign.assert_not_called()

        await pilot.press("tab", "tab", "enter")
        await pilot.pause()

        application.delete_orphan_campaign_folder.assert_called_once_with("Ashen Crown")
        application.rename_campaign.assert_called_once_with(campaign.id, "Ashen Crown")


@pytest.mark.anyio
async def test_description_and_game_system_commit_together() -> None:
    campaign = Campaign(name="Iron Pact")
    application = _application(campaign=campaign)
    application.update_campaign = MagicMock(
        return_value=Campaign(id=campaign.id, name="Iron Pact", description="New desc", game_system="D&D")
    )

    async with TableSageApp(application).run_test() as pilot:
        pilot.app.push_screen(CampaignDetailScreen(campaign.id))
        await pilot.pause()

        description = pilot.app.screen.query_one("#campaign-description-input", CommittingInput)
        description.focus()
        await pilot.pause()
        description.value = "New desc"

        await pilot.press("tab")
        await pilot.pause()

        application.update_campaign.assert_called_once_with(campaign.id, "New desc", None)


@pytest.mark.anyio
async def test_escape_commits_focused_field_before_popping() -> None:
    campaign = Campaign(name="Iron Pact")
    application = _application(campaign=campaign)
    application.rename_campaign = MagicMock(return_value=Campaign(id=campaign.id, name="Iron Pact Reforged"))

    async with TableSageApp(application).run_test() as pilot:
        pilot.app.push_screen(CampaignDetailScreen(campaign.id))
        await pilot.pause()

        name_input = pilot.app.screen.query_one("#campaign-name-input", CommittingInput)
        name_input.focus()
        await pilot.pause()
        name_input.value = "Iron Pact Reforged"

        await pilot.press("escape")
        await pilot.pause()

        application.rename_campaign.assert_called_once_with(campaign.id, "Iron Pact Reforged")


@pytest.mark.anyio
async def test_roster_table_shows_friendly_gm_label() -> None:
    campaign = Campaign(name="Iron Pact")
    player = Player(name="Alice")
    membership = CampaignPlayer(campaign_id=campaign.id, player_id=player.id, default_role_name="game-master")
    application = _application(campaign=campaign, roster=[(membership, player)])

    async with TableSageApp(application).run_test() as pilot:
        pilot.app.push_screen(CampaignDetailScreen(campaign.id))
        await pilot.pause()
        await pilot.press("r")
        await pilot.pause()

        table = pilot.app.screen.query_one("#roster-table", DataTable)
        row = tuple(str(cell) for cell in table.get_row_at(0))
        assert row == ("Alice", "Game Master")


@pytest.mark.anyio
async def test_new_roster_member_flow() -> None:
    campaign = Campaign(name="Iron Pact")
    player = Player(name="Alice")
    membership = CampaignPlayer(campaign_id=campaign.id, player_id=player.id, default_role_name="game-master")
    application = _application(campaign=campaign, players=[player])
    application.add_player_to_campaign = MagicMock(return_value=membership)

    async with TableSageApp(application).run_test() as pilot:
        pilot.app.push_screen(CampaignDetailScreen(campaign.id))
        await pilot.pause()
        await pilot.press("r")
        await pilot.pause()

        await pilot.press("n")
        await pilot.pause()
        assert isinstance(pilot.app.screen, PlayerPickerDialog)

        await pilot.press("enter")
        await pilot.pause()
        role_dialog = pilot.app.screen
        assert isinstance(role_dialog, RolePickerDialog)
        assert "Alice" in str(role_dialog.query_one("#role-picker-prompt", Static).render())

        role_dialog.query_one("#role-picker-gm", Button).press()
        await pilot.pause()

        application.add_player_to_campaign.assert_called_once_with(campaign.id, player.id, "game-master")


@pytest.mark.anyio
async def test_edit_roster_member_role_dialog_shows_player_and_current_role() -> None:
    campaign = Campaign(name="Iron Pact")
    player = Player(name="Alice")
    membership = CampaignPlayer(campaign_id=campaign.id, player_id=player.id, default_role_name="game-master")
    application = _application(campaign=campaign, roster=[(membership, player)])
    application.update_default_role = MagicMock()

    async with TableSageApp(application).run_test() as pilot:
        pilot.app.push_screen(CampaignDetailScreen(campaign.id))
        await pilot.pause()
        await pilot.press("r")
        await pilot.pause()

        await pilot.press("e")
        await pilot.pause()
        role_dialog = pilot.app.screen
        assert isinstance(role_dialog, RolePickerDialog)
        assert "Alice" in str(role_dialog.query_one("#role-picker-prompt", Static).render())
        assert "Game Master" in str(role_dialog.query_one("#role-picker-current", Static).render())

        role_dialog.query_one("#role-picker-character", Button).press()
        await pilot.pause()
        assert "Alice" in str(pilot.app.screen.query_one("#text-input-prompt", Static).render())


@pytest.mark.anyio
async def test_player_picker_shows_message_when_no_players_available() -> None:
    campaign = Campaign(name="Iron Pact")
    application = _application(campaign=campaign, players=[])

    async with TableSageApp(application).run_test() as pilot:
        pilot.app.push_screen(CampaignDetailScreen(campaign.id))
        await pilot.pause()
        await pilot.press("r")
        await pilot.pause()
        await pilot.press("n")
        await pilot.pause()

        assert isinstance(pilot.app.screen, PlayerPickerDialog)
        assert pilot.app.screen.query_one("#player-picker-empty")


@pytest.mark.anyio
async def test_delete_roster_member_confirms_then_removes() -> None:
    campaign = Campaign(name="Iron Pact")
    player = Player(name="Alice")
    membership = CampaignPlayer(campaign_id=campaign.id, player_id=player.id, default_role_name="game-master")
    application = _application(campaign=campaign, roster=[(membership, player)])
    application.remove_from_roster = MagicMock()

    async with TableSageApp(application).run_test() as pilot:
        pilot.app.push_screen(CampaignDetailScreen(campaign.id))
        await pilot.pause()
        await pilot.press("r")
        await pilot.pause()

        await pilot.press("d")
        await pilot.pause()
        assert isinstance(pilot.app.screen, ConfirmationDialog)

        await pilot.press("tab", "tab", "enter")
        await pilot.pause()

        application.remove_from_roster.assert_called_once_with(membership.id)


@pytest.mark.anyio
async def test_glossary_table_shows_entries() -> None:
    campaign = Campaign(name="Iron Pact")
    entry = GlossaryEntry(campaign_id=campaign.id, term="Ironhold", description="A fortress")
    application = _application(campaign=campaign, glossary=[entry])

    async with TableSageApp(application).run_test() as pilot:
        pilot.app.push_screen(CampaignDetailScreen(campaign.id))
        await pilot.pause()
        await pilot.press("g")
        await pilot.pause()

        table = pilot.app.screen.query_one("#glossary-table", DataTable)
        row = tuple(str(cell) for cell in table.get_row_at(0))
        assert row == ("Ironhold", "A fortress")


@pytest.mark.anyio
async def test_new_glossary_entry_flow() -> None:
    campaign = Campaign(name="Iron Pact")
    application = _application(campaign=campaign)
    application.create_glossary_entry = MagicMock()

    async with TableSageApp(application).run_test() as pilot:
        pilot.app.push_screen(CampaignDetailScreen(campaign.id))
        await pilot.pause()
        await pilot.press("g")
        await pilot.pause()

        await pilot.press("n")
        await pilot.pause()
        assert isinstance(pilot.app.screen, GlossaryEntryDialog)

        pilot.app.screen.query_one("#glossary-entry-term", Input).value = "Ironhold"
        pilot.app.screen.query_one("#glossary-entry-submit", Button).press()
        await pilot.pause()

        application.create_glossary_entry.assert_called_once()
        created_entry = application.create_glossary_entry.call_args.args[0]
        assert created_entry.term == "Ironhold"
        assert created_entry.campaign_id == campaign.id


@pytest.mark.anyio
async def test_glossary_duplicate_term_shows_error() -> None:
    campaign = Campaign(name="Iron Pact")
    application = _application(campaign=campaign)
    application.create_glossary_entry = MagicMock(side_effect=ValueError("A glossary term 'Ironhold' already exists in this campaign."))

    async with TableSageApp(application).run_test() as pilot:
        pilot.app.push_screen(CampaignDetailScreen(campaign.id))
        await pilot.pause()
        await pilot.press("g")
        await pilot.pause()
        await pilot.press("n")
        await pilot.pause()

        pilot.app.screen.query_one("#glossary-entry-term", Input).value = "Ironhold"
        pilot.app.screen.query_one("#glossary-entry-submit", Button).press()
        await pilot.pause()

        assert isinstance(pilot.app.screen, CampaignDetailScreen)


@pytest.mark.anyio
async def test_delete_glossary_entry_confirms_then_deletes() -> None:
    campaign = Campaign(name="Iron Pact")
    entry = GlossaryEntry(campaign_id=campaign.id, term="Ironhold")
    application = _application(campaign=campaign, glossary=[entry])
    application.delete_glossary_entry = MagicMock()

    async with TableSageApp(application).run_test() as pilot:
        pilot.app.push_screen(CampaignDetailScreen(campaign.id))
        await pilot.pause()
        await pilot.press("g")
        await pilot.pause()

        await pilot.press("d")
        await pilot.pause()
        await pilot.press("tab", "tab", "enter")
        await pilot.pause()

        application.delete_glossary_entry.assert_called_once_with(campaign.id, entry.id)


@pytest.mark.anyio
async def test_sessions_table_shows_sessions_sorted_by_sequence() -> None:
    campaign = Campaign(name="Iron Pact")
    session_two = GameSession(campaign_id=campaign.id, sequence_number=2, name="Second", session_date=date(2026, 2, 1))
    session_one = GameSession(campaign_id=campaign.id, sequence_number=1, name="First", session_date=date(2026, 1, 1))
    application = _application(campaign=campaign, sessions=[session_two, session_one])

    async with TableSageApp(application).run_test() as pilot:
        pilot.app.push_screen(CampaignDetailScreen(campaign.id))
        await pilot.pause()

        table = pilot.app.screen.query_one("#sessions-table", DataTable)
        assert [str(column.label) for column in table.columns.values()] == ["#", "Name", "Date"]
        rows = [tuple(str(cell) for cell in table.get_row_at(i)) for i in range(table.row_count)]
        assert rows == [
            ("001", "First", "2026-01-01"),
            ("002", "Second", "2026-02-01"),
        ]


@pytest.mark.anyio
async def test_new_session_creates_and_opens_session_detail() -> None:
    campaign = Campaign(name="Iron Pact")
    created = GameSession(campaign_id=campaign.id, sequence_number=1, name="Session One")
    application = _application(campaign=campaign)
    application.create_session = MagicMock(return_value=created)

    async with TableSageApp(application).run_test() as pilot:
        pilot.app.push_screen(CampaignDetailScreen(campaign.id))
        await pilot.pause()

        await pilot.press("n")
        await pilot.pause()
        assert isinstance(pilot.app.screen, TextInputDialog)

        pilot.app.screen.query_one("#text-input-value", Input).value = "Session One"
        await pilot.press("enter")
        await pilot.pause()

        application.create_session.assert_called_once_with(campaign.id, "Session One")
        assert isinstance(pilot.app.screen, SessionDetailScreen)


@pytest.mark.anyio
async def test_new_session_folder_collision_prompts_then_deletes_and_creates() -> None:
    campaign = Campaign(name="Iron Pact")
    created = GameSession(campaign_id=campaign.id, sequence_number=1, name="Session One")
    application = _application(campaign=campaign)
    application.session_folder_would_collide = MagicMock(return_value=True)
    application.delete_colliding_session_folder = MagicMock()
    application.create_session = MagicMock(return_value=created)

    async with TableSageApp(application).run_test() as pilot:
        pilot.app.push_screen(CampaignDetailScreen(campaign.id))
        await pilot.pause()

        await pilot.press("n")
        await pilot.pause()
        pilot.app.screen.query_one("#text-input-value", Input).value = "Session One"
        await pilot.press("enter")
        await pilot.pause()

        assert isinstance(pilot.app.screen, ConfirmationDialog)
        application.create_session.assert_not_called()

        await pilot.press("tab", "tab", "enter")
        await pilot.pause()

        application.delete_colliding_session_folder.assert_called_once_with(campaign.id)
        application.create_session.assert_called_once_with(campaign.id, "Session One")
        assert isinstance(pilot.app.screen, SessionDetailScreen)


@pytest.mark.anyio
async def test_new_session_folder_collision_cancelled_does_not_create() -> None:
    campaign = Campaign(name="Iron Pact")
    application = _application(campaign=campaign)
    application.session_folder_would_collide = MagicMock(return_value=True)
    application.create_session = MagicMock()

    async with TableSageApp(application).run_test() as pilot:
        pilot.app.push_screen(CampaignDetailScreen(campaign.id))
        await pilot.pause()

        await pilot.press("n")
        await pilot.pause()
        pilot.app.screen.query_one("#text-input-value", Input).value = "Session One"
        await pilot.press("enter")
        await pilot.pause()

        assert isinstance(pilot.app.screen, ConfirmationDialog)
        await pilot.press("escape")
        await pilot.pause()

        application.create_session.assert_not_called()
        assert isinstance(pilot.app.screen, CampaignDetailScreen)


@pytest.mark.anyio
async def test_edit_session_opens_session_detail() -> None:
    campaign = Campaign(name="Iron Pact")
    game_session = GameSession(campaign_id=campaign.id, sequence_number=1, name="Session One")
    application = _application(campaign=campaign, sessions=[game_session])
    application.get_session = MagicMock(return_value=game_session)

    async with TableSageApp(application).run_test() as pilot:
        pilot.app.push_screen(CampaignDetailScreen(campaign.id))
        await pilot.pause()

        await pilot.press("enter")
        await pilot.pause()

        assert isinstance(pilot.app.screen, SessionDetailScreen)


@pytest.mark.anyio
async def test_delete_session_confirms_then_deletes_and_reloads() -> None:
    campaign = Campaign(name="Iron Pact")
    game_session = GameSession(campaign_id=campaign.id, sequence_number=1, name="Session One")
    application = _application(campaign=campaign, sessions=[game_session])
    application.delete_session = MagicMock()

    async with TableSageApp(application).run_test() as pilot:
        pilot.app.push_screen(CampaignDetailScreen(campaign.id))
        await pilot.pause()

        await pilot.press("d")
        await pilot.pause()
        assert isinstance(pilot.app.screen, ConfirmationDialog)

        await pilot.press("tab", "tab", "enter")
        await pilot.pause()

        application.delete_session.assert_called_once_with(game_session.id)
        assert isinstance(pilot.app.screen, CampaignDetailScreen)
        assert application.list_sessions.call_count >= 2


@pytest.mark.anyio
async def test_cleanup_sessions_confirms_then_cleans() -> None:
    campaign = Campaign(name="Iron Pact")
    application = _application(campaign=campaign)
    application.cleanup_orphan_session_dirs = MagicMock(return_value=["004"])

    async with TableSageApp(application).run_test() as pilot:
        pilot.app.push_screen(CampaignDetailScreen(campaign.id))
        await pilot.pause()

        await pilot.press("c")
        await pilot.pause()
        assert isinstance(pilot.app.screen, ConfirmationDialog)

        await pilot.press("tab", "tab", "enter")
        await pilot.pause()

        application.cleanup_orphan_session_dirs.assert_called_once_with(campaign.id)


@pytest.mark.anyio
async def test_cleanup_is_not_available_outside_sessions_tab() -> None:
    campaign = Campaign(name="Iron Pact")
    application = _application(campaign=campaign)
    application.cleanup_orphan_session_dirs = MagicMock()

    async with TableSageApp(application).run_test() as pilot:
        pilot.app.push_screen(CampaignDetailScreen(campaign.id))
        await pilot.pause()
        await pilot.press("r")
        await pilot.pause()

        await pilot.press("c")
        await pilot.pause()

        assert isinstance(pilot.app.screen, CampaignDetailScreen)
        application.cleanup_orphan_session_dirs.assert_not_called()


@pytest.mark.anyio
async def test_escape_pops_back_to_campaign_list() -> None:
    from tablesage_tui.screens.campaign_list import CampaignListScreen

    campaign = Campaign(name="Iron Pact")
    application = _application(campaign=campaign)
    application.list_campaigns = MagicMock(return_value=[campaign])
    application.last_session_dates = MagicMock(return_value={})

    async with TableSageApp(application).run_test() as pilot:
        await pilot.press("c")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        assert isinstance(pilot.app.screen, CampaignDetailScreen)

        await pilot.press("escape")
        await pilot.pause()

        assert isinstance(pilot.app.screen, CampaignListScreen)


@pytest.mark.anyio
async def test_f5_reloads_metadata_and_all_tabs_without_changing_active_tab() -> None:
    campaign = Campaign(name="Iron Pact")
    application = _application(campaign=campaign)

    async with TableSageApp(application).run_test() as pilot:
        pilot.app.push_screen(CampaignDetailScreen(campaign.id))
        await pilot.pause()

        await pilot.press("r")
        await pilot.pause()
        screen = pilot.app.screen
        assert isinstance(screen, CampaignDetailScreen)
        assert screen._active_tab == "roster"

        application.get_campaign.reset_mock()
        application.list_roster.reset_mock()
        application.list_sessions.reset_mock()
        application.list_glossary_entries.reset_mock()

        await pilot.press("f5")
        await pilot.pause()

        application.get_campaign.assert_called_once()
        application.list_roster.assert_called_once()
        application.list_sessions.assert_called_once()
        application.list_glossary_entries.assert_called_once()
        assert screen._active_tab == "roster"
