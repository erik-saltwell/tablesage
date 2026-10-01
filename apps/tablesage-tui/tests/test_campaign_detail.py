from datetime import date
from unittest.mock import ANY, MagicMock

import pytest
from tablesage_application.paths import ArtifactName
from tablesage_application.session_pipeline.artifact_graph import ArtifactStatus, GenerationTask
from tablesage_model.model import Campaign, GlossaryEntry
from tablesage_model.model import Session as GameSession
from tablesage_tui.dialogs import CampaignDialog, ConfirmationDialog, GlossaryEntryDialog, SessionDialog
from tablesage_tui.screens.campaign_detail import CampaignDetailScreen
from tablesage_tui.screens.main_app import TableSageApp
from tablesage_tui.screens.session_detail import SessionDetailScreen
from textual.pilot import Pilot
from textual.widgets import Button, DataTable, Input, Static


def _application(
    *,
    campaign: Campaign | None = None,
    sessions: list[GameSession] | None = None,
    glossary: list[GlossaryEntry] | None = None,
) -> MagicMock:
    campaign = campaign or Campaign(name="Iron Pact")
    return MagicMock(
        get_campaign=MagicMock(return_value=campaign),
        list_sessions=MagicMock(return_value=sessions or []),
        list_glossary_entries=MagicMock(return_value=glossary or []),
        # Sensible defaults so navigating into a real SessionDetailScreen
        # (opened by N/E on the Sessions tab) doesn't crash on mount.
        get_session=MagicMock(return_value=GameSession(campaign_id=campaign.id, sequence_number=1, name="Session")),
        list_attendance=MagicMock(return_value=[]),
        session_artifacts=MagicMock(return_value=dict.fromkeys(ArtifactName, False)),
        session_artifact_states=MagicMock(return_value=dict.fromkeys(ArtifactName, ArtifactStatus.MISSING)),
        generate_outputs=MagicMock(return_value=()),
        can_transcribe_audio=MagicMock(return_value=(False, "Import input audio first.")),
        can_clean_session=MagicMock(return_value=(False, "No artifacts to delete.")),
        can_extract_glossary=MagicMock(return_value=(False, "Generate the Role Transcript first.")),
        can_export_artifacts=MagicMock(return_value=(False, "No artifacts to export yet.")),
        campaign_folder_exists=MagicMock(return_value=False),
        session_folder_would_collide=MagicMock(return_value=False),
    )


async def _wait_for_progress_worker(pilot: Pilot) -> None:
    await pilot.app.workers.wait_for_complete()
    await pilot.pause()


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
async def test_regenerate_all_outputs_processes_only_reviewed_audio_sessions() -> None:
    campaign = Campaign(name="Iron Pact")
    ready = GameSession(campaign_id=campaign.id, sequence_number=1, name="Ready")
    awaiting_review = GameSession(campaign_id=campaign.id, sequence_number=2, name="Awaiting review")
    application = _application(campaign=campaign, sessions=[ready, awaiting_review])
    application.session_artifacts.side_effect = lambda session_id: (
        {name: name is ArtifactName.INPUT_AUDIO for name in ArtifactName}
        if session_id in {ready.id, awaiting_review.id}
        else dict.fromkeys(ArtifactName, False)
    )
    application.session_artifact_states.side_effect = lambda session_id: {
        name: ArtifactStatus.CURRENT if session_id == ready.id and name is ArtifactName.REVIEWED_TRANSCRIPT else ArtifactStatus.MISSING
        for name in ArtifactName
    }
    application.generate_outputs.return_value = (GenerationTask(ready.id, ArtifactName.LEDGER),)

    async with TableSageApp(application).run_test() as pilot:
        pilot.app.push_screen(CampaignDetailScreen(campaign.id))
        await pilot.pause()

        await pilot.press("slash", "o")
        await _wait_for_progress_worker(pilot)

    application.generate_outputs.assert_called_once_with(ready.id, on_stage=ANY)


@pytest.mark.anyio
async def test_generate_opportunities_secondary_binding_opens_screen() -> None:
    from tablesage_application.campaign_recap import CampaignSceneRecap
    from tablesage_tui.screens.opportunities import OpportunitiesScreen

    campaign = Campaign(name="Iron Pact")
    application = _application(campaign=campaign)
    application.create_campaign_scene_recap.return_value = CampaignSceneRecap(
        campaign_id=campaign.id, campaign_name=campaign.name, starting_situation="Start", scenes=(), ending_situation="End"
    )

    binding = next(binding for binding in CampaignDetailScreen.OTHER_BINDINGS if binding.action == "generate_opportunities")
    assert (binding.key, binding.description, binding.key_display) == ("y,Y", "Generate Opportunities", "Y")
    assert all(binding.action != "prepare_next_session" for binding in CampaignDetailScreen.OTHER_BINDINGS)

    async with TableSageApp(application).run_test() as pilot:
        pilot.app.push_screen(CampaignDetailScreen(campaign.id))
        await pilot.pause()

        await pilot.press("slash", "y")
        await _wait_for_progress_worker(pilot)
        assert isinstance(pilot.app.screen, OpportunitiesScreen)

    application.create_campaign_scene_recap.assert_called_once_with(campaign.id)


@pytest.mark.anyio
async def test_metadata_is_shown_read_only_on_load() -> None:
    campaign = Campaign(name="Iron Pact", description="A grim war", game_system="Dungeon World")
    application = _application(campaign=campaign)

    async with TableSageApp(application).run_test() as pilot:
        pilot.app.push_screen(CampaignDetailScreen(campaign.id))
        await pilot.pause()

        screen = pilot.app.screen
        assert screen.query_one("#campaign-name-value", Static).render() == "Iron Pact"
        assert screen.query_one("#campaign-description-value", Static).render() == "A grim war"
        assert screen.query_one("#campaign-game-system-value", Static).render() == "Dungeon World"


@pytest.mark.anyio
async def test_edit_metadata_dialog_is_prefilled_with_current_values() -> None:
    campaign = Campaign(name="Iron Pact", description="A grim war", game_system="Dungeon World")
    application = _application(campaign=campaign)

    async with TableSageApp(application).run_test() as pilot:
        pilot.app.push_screen(CampaignDetailScreen(campaign.id))
        await pilot.pause()

        await pilot.press("m")
        await pilot.pause()

        dialog = pilot.app.screen
        assert isinstance(dialog, CampaignDialog)
        assert dialog.query_one("#campaign-dialog-name", Input).value == "Iron Pact"
        assert dialog.query_one("#campaign-dialog-description", Input).value == "A grim war"
        assert dialog.query_one("#campaign-dialog-game-system", Input).value == "Dungeon World"


@pytest.mark.anyio
async def test_typing_a_tab_letter_into_a_metadata_dialog_field_does_not_switch_tabs() -> None:
    """A pushed, modal `CampaignDialog` is the current screen while open, so screen-level
    bindings on the underlying `CampaignDetailScreen` (like the S/G tab-switch shortcuts)
    don't fire for keys typed into its fields -- this is normal Textual modal-screen dispatch,
    exercised here because the previous implementation had its own bespoke keystroke handling
    that this replaces."""
    campaign = Campaign(name="Iron Pact")
    application = _application(campaign=campaign)

    async with TableSageApp(application).run_test() as pilot:
        pilot.app.push_screen(CampaignDetailScreen(campaign.id))
        await pilot.pause()

        screen = pilot.app.screen
        assert isinstance(screen, CampaignDetailScreen)

        await pilot.press("m")
        await pilot.pause()
        dialog = pilot.app.screen
        assert isinstance(dialog, CampaignDialog)
        description = dialog.query_one("#campaign-dialog-description", Input)
        description.focus()
        await pilot.pause()

        await pilot.press("r")
        await pilot.pause()

        assert description.value == "r"
        assert screen._active_tab == "sessions"


@pytest.mark.anyio
async def test_s_and_g_switch_tabs_when_a_table_has_focus() -> None:
    campaign = Campaign(name="Iron Pact")
    application = _application(campaign=campaign)

    async with TableSageApp(application).run_test() as pilot:
        pilot.app.push_screen(CampaignDetailScreen(campaign.id))
        await pilot.pause()

        screen = pilot.app.screen
        assert isinstance(screen, CampaignDetailScreen)
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

        await pilot.click("#tab-label-glossary")
        await pilot.pause()
        assert screen._active_tab == "glossary"

        await pilot.click("#tab-label-sessions")
        await pilot.pause()
        assert screen._active_tab == "sessions"


@pytest.mark.anyio
async def test_renaming_via_metadata_dialog_commits_on_submit() -> None:
    campaign = Campaign(name="Iron Pact")
    application = _application(campaign=campaign)
    renamed = Campaign(id=campaign.id, name="Iron Pact Reforged")

    def rename(_campaign_id: object, _name: str) -> Campaign:
        # Dismissing the dialog resumes CampaignDetailScreen, whose `on_screen_resume` reloads
        # from `get_campaign` -- mirror a real backend by making the mock reflect the rename.
        application.get_campaign.return_value = renamed
        return renamed

    application.rename_campaign = MagicMock(side_effect=rename)

    async with TableSageApp(application).run_test() as pilot:
        pilot.app.push_screen(CampaignDetailScreen(campaign.id))
        await pilot.pause()

        await pilot.press("m")
        await pilot.pause()
        dialog = pilot.app.screen
        assert isinstance(dialog, CampaignDialog)

        name_input = dialog.query_one("#campaign-dialog-name", Input)
        name_input.focus()
        name_input.value = "Iron Pact Reforged"
        await pilot.press("enter")
        await _wait_for_progress_worker(pilot)

        application.rename_campaign.assert_called_once_with(campaign.id, "Iron Pact Reforged")
        assert isinstance(pilot.app.screen, CampaignDetailScreen)
        assert pilot.app.screen.query_one("#campaign-name-value", Static).render() == "Iron Pact Reforged"


@pytest.mark.anyio
async def test_duplicate_rename_shows_inline_error_and_keeps_dialog_open() -> None:
    campaign = Campaign(name="Iron Pact")
    application = _application(campaign=campaign)
    application.rename_campaign = MagicMock(side_effect=ValueError("A campaign named 'Ashen Crown' already exists."))

    async with TableSageApp(application).run_test() as pilot:
        pilot.app.push_screen(CampaignDetailScreen(campaign.id))
        await pilot.pause()

        await pilot.press("m")
        await pilot.pause()
        dialog = pilot.app.screen
        assert isinstance(dialog, CampaignDialog)

        name_input = dialog.query_one("#campaign-dialog-name", Input)
        name_input.focus()
        name_input.value = "Ashen Crown"
        await pilot.press("enter")
        await _wait_for_progress_worker(pilot)

        application.rename_campaign.assert_called_once_with(campaign.id, "Ashen Crown")
        assert isinstance(pilot.app.screen, CampaignDialog)
        assert "Ashen Crown" in str(dialog.query_one("#campaign-dialog-error", Static).render())
        assert name_input.value == "Ashen Crown"


@pytest.mark.anyio
async def test_rename_folder_collision_prompts_then_deletes_and_renames() -> None:
    campaign = Campaign(name="Iron Pact")
    application = _application(campaign=campaign)
    application.campaign_folder_exists = MagicMock(return_value=True)
    application.delete_orphan_campaign_folder = MagicMock()
    renamed = Campaign(id=campaign.id, name="Ashen Crown")

    def rename(_campaign_id: object, _name: str) -> Campaign:
        application.get_campaign.return_value = renamed
        return renamed

    application.rename_campaign = MagicMock(side_effect=rename)

    async with TableSageApp(application).run_test() as pilot:
        pilot.app.push_screen(CampaignDetailScreen(campaign.id))
        await pilot.pause()

        await pilot.press("m")
        await pilot.pause()
        dialog = pilot.app.screen
        assert isinstance(dialog, CampaignDialog)

        name_input = dialog.query_one("#campaign-dialog-name", Input)
        name_input.focus()
        name_input.value = "Ashen Crown"
        await pilot.press("enter")
        await pilot.pause()

        assert isinstance(pilot.app.screen, ConfirmationDialog)
        application.rename_campaign.assert_not_called()

        await pilot.press("tab", "tab", "enter")
        await _wait_for_progress_worker(pilot)

        application.delete_orphan_campaign_folder.assert_called_once_with("Ashen Crown")
        application.rename_campaign.assert_called_once_with(campaign.id, "Ashen Crown")
        assert isinstance(pilot.app.screen, CampaignDetailScreen)
        assert pilot.app.screen.query_one("#campaign-name-value", Static).render() == "Ashen Crown"


@pytest.mark.anyio
async def test_rename_folder_collision_cancelled_keeps_dialog_open_with_error() -> None:
    campaign = Campaign(name="Iron Pact")
    application = _application(campaign=campaign)
    application.campaign_folder_exists = MagicMock(return_value=True)
    application.rename_campaign = MagicMock()

    async with TableSageApp(application).run_test() as pilot:
        pilot.app.push_screen(CampaignDetailScreen(campaign.id))
        await pilot.pause()

        await pilot.press("m")
        await pilot.pause()
        dialog = pilot.app.screen
        assert isinstance(dialog, CampaignDialog)

        name_input = dialog.query_one("#campaign-dialog-name", Input)
        name_input.focus()
        name_input.value = "Ashen Crown"
        await pilot.press("enter")
        await pilot.pause()

        assert isinstance(pilot.app.screen, ConfirmationDialog)
        await pilot.press("escape")
        await _wait_for_progress_worker(pilot)

        application.rename_campaign.assert_not_called()
        # `resolve_folder_collision` returning `False` on a cancelled collision leaves the
        # caller's dialog open (not the underlying screen) with the typed name intact and an
        # inline error, per `TableSageScreen.resolve_folder_collision`'s docstring.
        assert isinstance(pilot.app.screen, CampaignDialog)
        assert name_input.value == "Ashen Crown"
        assert "Ashen Crown" in str(dialog.query_one("#campaign-dialog-error", Static).render())


@pytest.mark.anyio
async def test_description_and_game_system_commit_together_via_metadata_dialog() -> None:
    campaign = Campaign(name="Iron Pact")
    application = _application(campaign=campaign)
    updated = Campaign(id=campaign.id, name="Iron Pact", description="New desc", game_system="D&D")

    def update(_campaign_id: object, _description: str | None, _game_system: str | None) -> Campaign:
        # Dismissing the dialog resumes CampaignDetailScreen, whose `on_screen_resume` reloads
        # from `get_campaign` -- mirror a real backend by making the mock reflect the update.
        application.get_campaign.return_value = updated
        return updated

    application.update_campaign = MagicMock(side_effect=update)

    async with TableSageApp(application).run_test() as pilot:
        pilot.app.push_screen(CampaignDetailScreen(campaign.id))
        await pilot.pause()

        await pilot.press("m")
        await pilot.pause()
        dialog = pilot.app.screen
        assert isinstance(dialog, CampaignDialog)

        description = dialog.query_one("#campaign-dialog-description", Input)
        description.focus()
        description.value = "New desc"
        await pilot.press("enter")
        await _wait_for_progress_worker(pilot)

        application.update_campaign.assert_called_once_with(campaign.id, "New desc", None)
        assert isinstance(pilot.app.screen, CampaignDetailScreen)
        assert pilot.app.screen.query_one("#campaign-description-value", Static).render() == "New desc"


@pytest.mark.anyio
async def test_escape_within_metadata_dialog_cancels_without_saving() -> None:
    """Unlike the old committing-input behavior (Escape committed the focused field before
    popping the screen), the dialog's own Escape binding cancels outright -- see
    `CampaignDialog.action_cancel` -- discarding the typed value and never calling
    `on_submit`/`application.rename_campaign`."""
    campaign = Campaign(name="Iron Pact")
    application = _application(campaign=campaign)
    application.rename_campaign = MagicMock(return_value=Campaign(id=campaign.id, name="Iron Pact Reforged"))

    async with TableSageApp(application).run_test() as pilot:
        pilot.app.push_screen(CampaignDetailScreen(campaign.id))
        await pilot.pause()

        await pilot.press("m")
        await pilot.pause()
        dialog = pilot.app.screen
        assert isinstance(dialog, CampaignDialog)
        name_input = dialog.query_one("#campaign-dialog-name", Input)
        name_input.focus()
        name_input.value = "Iron Pact Reforged"

        await pilot.press("escape")
        await pilot.pause()

        application.rename_campaign.assert_not_called()
        assert isinstance(pilot.app.screen, CampaignDetailScreen)
        assert pilot.app.screen.query_one("#campaign-name-value", Static).render() == "Iron Pact"


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
    created = GameSession(campaign_id=campaign.id, sequence_number=1, name="Session One", session_date=date(2026, 10, 1))
    application = _application(campaign=campaign)
    application.create_session = MagicMock(return_value=created)

    async with TableSageApp(application).run_test() as pilot:
        pilot.app.push_screen(CampaignDetailScreen(campaign.id))
        await pilot.pause()

        await pilot.press("n")
        await pilot.pause()
        assert isinstance(pilot.app.screen, SessionDialog)

        pilot.app.screen.query_one("#session-dialog-name", Input).value = "Session One"
        pilot.app.screen.query_one("#session-dialog-date", Input).value = "2026-10-01"
        await pilot.press("enter")
        await _wait_for_progress_worker(pilot)

        application.create_session.assert_called_once_with(campaign.id, "Session One", date(2026, 10, 1))
        assert isinstance(pilot.app.screen, SessionDetailScreen)


@pytest.mark.anyio
async def test_new_session_folder_collision_prompts_then_deletes_and_creates() -> None:
    campaign = Campaign(name="Iron Pact")
    created = GameSession(campaign_id=campaign.id, sequence_number=1, name="Session One", session_date=date(2026, 10, 1))
    application = _application(campaign=campaign)
    application.session_folder_would_collide = MagicMock(return_value=True)
    application.delete_colliding_session_folder = MagicMock()
    application.create_session = MagicMock(return_value=created)

    async with TableSageApp(application).run_test() as pilot:
        pilot.app.push_screen(CampaignDetailScreen(campaign.id))
        await pilot.pause()

        await pilot.press("n")
        await pilot.pause()
        pilot.app.screen.query_one("#session-dialog-name", Input).value = "Session One"
        pilot.app.screen.query_one("#session-dialog-date", Input).value = "2026-10-01"
        await pilot.press("enter")
        await pilot.pause()

        assert isinstance(pilot.app.screen, ConfirmationDialog)
        application.create_session.assert_not_called()

        await pilot.press("tab", "tab", "enter")
        await _wait_for_progress_worker(pilot)

        application.delete_colliding_session_folder.assert_called_once_with(campaign.id)
        application.create_session.assert_called_once_with(campaign.id, "Session One", date(2026, 10, 1))
        assert isinstance(pilot.app.screen, SessionDetailScreen)


@pytest.mark.anyio
async def test_new_session_folder_collision_cancelled_keeps_dialog_open_with_error() -> None:
    campaign = Campaign(name="Iron Pact")
    application = _application(campaign=campaign)
    application.session_folder_would_collide = MagicMock(return_value=True)
    application.create_session = MagicMock()

    async with TableSageApp(application).run_test() as pilot:
        pilot.app.push_screen(CampaignDetailScreen(campaign.id))
        await pilot.pause()

        await pilot.press("n")
        await pilot.pause()
        dialog = pilot.app.screen
        assert isinstance(dialog, SessionDialog)
        dialog.query_one("#session-dialog-name", Input).value = "Session One"
        dialog.query_one("#session-dialog-date", Input).value = "2026-10-01"
        await pilot.press("enter")
        await pilot.pause()

        assert isinstance(pilot.app.screen, ConfirmationDialog)
        await pilot.press("escape")
        await _wait_for_progress_worker(pilot)

        application.create_session.assert_not_called()
        # A cancelled collision leaves the SessionDialog itself open with an inline error
        # (see `TableSageScreen.resolve_folder_collision`), not the underlying CampaignDetailScreen.
        assert isinstance(pilot.app.screen, SessionDialog)
        assert "already exists" in str(dialog.query_one("#session-dialog-error", Static).render())
        assert dialog.query_one("#session-dialog-name", Input).value == "Session One"


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
        # Focus lands on the Sessions table automatically -- no more AUTO_FOCUS on a name input.
        assert pilot.app.focused is pilot.app.screen.query_one("#sessions-table")

        # A single Esc now pops straight back (no more "first Esc leaves the field" step).
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

        await pilot.press("g")
        await pilot.pause()
        screen = pilot.app.screen
        assert isinstance(screen, CampaignDetailScreen)
        assert screen._active_tab == "glossary"

        application.get_campaign.reset_mock()
        application.list_sessions.reset_mock()
        application.list_glossary_entries.reset_mock()

        await pilot.press("f5")
        await pilot.pause()

        application.get_campaign.assert_called_once()
        application.list_sessions.assert_called_once()
        application.list_glossary_entries.assert_called_once()
        assert screen._active_tab == "glossary"
