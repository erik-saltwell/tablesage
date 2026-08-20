import uuid

import pytest
from tablesage_application.sessions import Attendee
from tablesage_model.model import Player
from tablesage_tui.dialogs import AttendeeDialog, AttendeeResult, TextInputDialog
from tablesage_tui.screens.main_app import TableSageApp
from textual.widgets import Button, DataTable, Input, Select

_ALICE = Player(name="Alice")
_BOB = Player(name="Bob")


@pytest.mark.anyio
async def test_add_mode_starts_blank_with_no_roles_and_save_disabled() -> None:
    async with TableSageApp().run_test() as pilot:
        pilot.app.push_screen(AttendeeDialog(players=[_ALICE, _BOB], attendee=None))
        await pilot.pause()

        select = pilot.app.screen.query_one("#attendee-player-select", Select)
        assert select.is_blank()
        assert pilot.app.screen.query_one("#attendee-role-table", DataTable).row_count == 0
        assert pilot.app.screen.query_one("#attendee-save", Button).disabled


@pytest.mark.anyio
async def test_edit_mode_preselects_player_and_shows_existing_roles() -> None:
    attendee = Attendee(attendance_id=uuid.uuid4(), player_id=_ALICE.id, player_name="Alice", roles=("Zaria", "Narrator"))

    async with TableSageApp().run_test() as pilot:
        pilot.app.push_screen(AttendeeDialog(players=[_ALICE, _BOB], attendee=attendee))
        await pilot.pause()

        select = pilot.app.screen.query_one("#attendee-player-select", Select)
        assert select.value == _ALICE.id

        table = pilot.app.screen.query_one("#attendee-role-table", DataTable)
        rows = [str(table.get_row_at(i)[0]) for i in range(table.row_count)]
        assert rows == ["Zaria", "Narrator"]

        # A player is already selected and roles already exist, so Save starts enabled.
        assert not pilot.app.screen.query_one("#attendee-save", Button).disabled


@pytest.mark.anyio
async def test_add_custom_role_via_dialog() -> None:
    attendee = Attendee(attendance_id=uuid.uuid4(), player_id=_ALICE.id, player_name="Alice", roles=("Zaria",))

    async with TableSageApp().run_test() as pilot:
        pilot.app.push_screen(AttendeeDialog(players=[_ALICE], attendee=attendee))
        await pilot.pause()

        pilot.app.screen.query_one("#attendee-add-role", Button).press()
        await pilot.pause()
        assert isinstance(pilot.app.screen, TextInputDialog)

        pilot.app.screen.query_one("#text-input-value", Input).value = "Narrator"
        await pilot.press("enter")
        await pilot.pause()

        table = pilot.app.screen.query_one("#attendee-role-table", DataTable)
        rows = [str(table.get_row_at(i)[0]) for i in range(table.row_count)]
        assert rows == ["Zaria", "Narrator"]


@pytest.mark.anyio
async def test_add_duplicate_custom_role_is_a_no_op() -> None:
    attendee = Attendee(attendance_id=uuid.uuid4(), player_id=_ALICE.id, player_name="Alice", roles=("Zaria",))

    async with TableSageApp().run_test() as pilot:
        pilot.app.push_screen(AttendeeDialog(players=[_ALICE], attendee=attendee))
        await pilot.pause()

        pilot.app.screen.query_one("#attendee-add-role", Button).press()
        await pilot.pause()
        pilot.app.screen.query_one("#text-input-value", Input).value = "Zaria"
        await pilot.press("enter")
        await pilot.pause()

        assert pilot.app.screen.query_one("#attendee-role-table", DataTable).row_count == 1


@pytest.mark.anyio
async def test_add_game_master_role_is_one_click() -> None:
    attendee = Attendee(attendance_id=uuid.uuid4(), player_id=_ALICE.id, player_name="Alice", roles=("Zaria",))

    async with TableSageApp().run_test() as pilot:
        pilot.app.push_screen(AttendeeDialog(players=[_ALICE], attendee=attendee))
        await pilot.pause()

        pilot.app.screen.query_one("#attendee-add-gm", Button).press()
        await pilot.pause()

        table = pilot.app.screen.query_one("#attendee-role-table", DataTable)
        rows = [str(table.get_row_at(i)[0]) for i in range(table.row_count)]
        assert rows == ["Zaria", "Game Master"]


@pytest.mark.anyio
async def test_add_duplicate_game_master_role_is_a_no_op() -> None:
    attendee = Attendee(attendance_id=uuid.uuid4(), player_id=_ALICE.id, player_name="Alice", roles=("Game Master",))

    async with TableSageApp().run_test() as pilot:
        pilot.app.push_screen(AttendeeDialog(players=[_ALICE], attendee=attendee))
        await pilot.pause()

        pilot.app.screen.query_one("#attendee-add-gm", Button).press()
        await pilot.pause()

        assert pilot.app.screen.query_one("#attendee-role-table", DataTable).row_count == 1


@pytest.mark.anyio
async def test_edit_selected_role_renames_it() -> None:
    attendee = Attendee(attendance_id=uuid.uuid4(), player_id=_ALICE.id, player_name="Alice", roles=("Zaria", "Narrator"))

    async with TableSageApp().run_test() as pilot:
        pilot.app.push_screen(AttendeeDialog(players=[_ALICE], attendee=attendee))
        await pilot.pause()

        table = pilot.app.screen.query_one("#attendee-role-table", DataTable)
        table.move_cursor(row=0)
        pilot.app.screen.query_one("#attendee-edit-role", Button).press()
        await pilot.pause()

        assert isinstance(pilot.app.screen, TextInputDialog)
        assert pilot.app.screen.query_one("#text-input-value", Input).value == "Zaria"
        pilot.app.screen.query_one("#text-input-value", Input).value = "Bard"
        await pilot.press("enter")
        await pilot.pause()

        rows = [str(table.get_row_at(i)[0]) for i in range(table.row_count)]
        assert rows == ["Bard", "Narrator"]


@pytest.mark.anyio
async def test_edit_selected_role_rejects_renaming_to_an_existing_role() -> None:
    attendee = Attendee(attendance_id=uuid.uuid4(), player_id=_ALICE.id, player_name="Alice", roles=("Zaria", "Narrator"))

    async with TableSageApp().run_test() as pilot:
        pilot.app.push_screen(AttendeeDialog(players=[_ALICE], attendee=attendee))
        await pilot.pause()

        table = pilot.app.screen.query_one("#attendee-role-table", DataTable)
        table.move_cursor(row=0)
        pilot.app.screen.query_one("#attendee-edit-role", Button).press()
        await pilot.pause()
        pilot.app.screen.query_one("#text-input-value", Input).value = "Narrator"
        await pilot.press("enter")
        await pilot.pause()

        rows = [str(table.get_row_at(i)[0]) for i in range(table.row_count)]
        assert rows == ["Zaria", "Narrator"]


@pytest.mark.anyio
async def test_remove_selected_role() -> None:
    attendee = Attendee(attendance_id=uuid.uuid4(), player_id=_ALICE.id, player_name="Alice", roles=("Zaria", "Narrator"))

    async with TableSageApp().run_test() as pilot:
        pilot.app.push_screen(AttendeeDialog(players=[_ALICE], attendee=attendee))
        await pilot.pause()

        table = pilot.app.screen.query_one("#attendee-role-table", DataTable)
        table.move_cursor(row=0)
        pilot.app.screen.query_one("#attendee-remove-role", Button).press()
        await pilot.pause()

        rows = [str(table.get_row_at(i)[0]) for i in range(table.row_count)]
        assert rows == ["Narrator"]


@pytest.mark.anyio
async def test_removing_last_role_disables_save() -> None:
    attendee = Attendee(attendance_id=uuid.uuid4(), player_id=_ALICE.id, player_name="Alice", roles=("Zaria",))

    async with TableSageApp().run_test() as pilot:
        pilot.app.push_screen(AttendeeDialog(players=[_ALICE], attendee=attendee))
        await pilot.pause()

        table = pilot.app.screen.query_one("#attendee-role-table", DataTable)
        table.move_cursor(row=0)
        pilot.app.screen.query_one("#attendee-remove-role", Button).press()
        await pilot.pause()

        assert pilot.app.screen.query_one("#attendee-save", Button).disabled


@pytest.mark.anyio
async def test_save_dismisses_with_chosen_player_and_roles() -> None:
    results: list[AttendeeResult | None] = []

    async with TableSageApp().run_test() as pilot:
        pilot.app.push_screen(AttendeeDialog(players=[_ALICE, _BOB], attendee=None), results.append)
        await pilot.pause()

        pilot.app.screen.query_one("#attendee-player-select", Select).value = _BOB.id
        await pilot.pause()
        pilot.app.screen.query_one("#attendee-add-gm", Button).press()
        await pilot.pause()
        pilot.app.screen.query_one("#attendee-save", Button).press()
        await pilot.pause()

        assert results == [AttendeeResult(player_id=_BOB.id, roles=("Game Master",))]


@pytest.mark.anyio
async def test_cancel_dismisses_with_none() -> None:
    attendee = Attendee(attendance_id=uuid.uuid4(), player_id=_ALICE.id, player_name="Alice", roles=("Zaria",))
    results: list[AttendeeResult | None] = []

    async with TableSageApp().run_test() as pilot:
        pilot.app.push_screen(AttendeeDialog(players=[_ALICE], attendee=attendee), results.append)
        await pilot.pause()

        pilot.app.screen.query_one("#attendee-cancel", Button).press()
        await pilot.pause()

        assert results == [None]


@pytest.mark.anyio
async def test_escape_dismisses_with_none() -> None:
    attendee = Attendee(attendance_id=uuid.uuid4(), player_id=_ALICE.id, player_name="Alice", roles=("Zaria",))
    results: list[AttendeeResult | None] = []

    async with TableSageApp().run_test() as pilot:
        pilot.app.push_screen(AttendeeDialog(players=[_ALICE], attendee=attendee), results.append)
        await pilot.pause()

        await pilot.press("escape")
        await pilot.pause()

        assert results == [None]


@pytest.mark.anyio
async def test_no_players_available_shows_message_and_close_button() -> None:
    results: list[AttendeeResult | None] = []

    async with TableSageApp().run_test() as pilot:
        pilot.app.push_screen(AttendeeDialog(players=[], attendee=None), results.append)
        await pilot.pause()

        assert pilot.app.screen.query_one("#attendee-empty")
        pilot.app.screen.query_one("#attendee-close", Button).press()
        await pilot.pause()

        assert results == [None]
