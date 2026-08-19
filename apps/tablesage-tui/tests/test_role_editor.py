import pytest
from tablesage_tui.dialogs import RoleEditorDialog
from tablesage_tui.screens.main_app import TableSageApp
from textual.widgets import Button, DataTable, Input


@pytest.mark.anyio
async def test_shows_existing_roles() -> None:
    async with TableSageApp().run_test() as pilot:
        pilot.app.push_screen(RoleEditorDialog(player_name="Alice", roles=["Zaria", "Narrator"]))
        await pilot.pause()

        table = pilot.app.screen.query_one("#role-editor-table", DataTable)
        rows = [str(table.get_row_at(i)[0]) for i in range(table.row_count)]
        assert rows == ["Zaria", "Narrator"]


@pytest.mark.anyio
async def test_add_role_via_enter() -> None:
    results: list[list[str] | None] = []

    async with TableSageApp().run_test() as pilot:
        pilot.app.push_screen(RoleEditorDialog(player_name="Alice", roles=["Zaria"]), results.append)
        await pilot.pause()

        pilot.app.screen.query_one("#role-editor-input", Input).value = "Narrator"
        await pilot.press("enter")
        await pilot.pause()

        table = pilot.app.screen.query_one("#role-editor-table", DataTable)
        rows = [str(table.get_row_at(i)[0]) for i in range(table.row_count)]
        assert rows == ["Zaria", "Narrator"]

        pilot.app.screen.query_one("#role-editor-save", Button).press()
        await pilot.pause()

        assert results == [["Zaria", "Narrator"]]


@pytest.mark.anyio
async def test_add_duplicate_role_is_a_no_op() -> None:
    async with TableSageApp().run_test() as pilot:
        pilot.app.push_screen(RoleEditorDialog(player_name="Alice", roles=["Zaria"]))
        await pilot.pause()

        pilot.app.screen.query_one("#role-editor-input", Input).value = "Zaria"
        await pilot.press("enter")
        await pilot.pause()

        table = pilot.app.screen.query_one("#role-editor-table", DataTable)
        assert table.row_count == 1


@pytest.mark.anyio
async def test_remove_selected_role() -> None:
    async with TableSageApp().run_test() as pilot:
        pilot.app.push_screen(RoleEditorDialog(player_name="Alice", roles=["Zaria", "Narrator"]))
        await pilot.pause()

        table = pilot.app.screen.query_one("#role-editor-table", DataTable)
        table.move_cursor(row=0)
        pilot.app.screen.query_one("#role-editor-remove", Button).press()
        await pilot.pause()

        rows = [str(table.get_row_at(i)[0]) for i in range(table.row_count)]
        assert rows == ["Narrator"]


@pytest.mark.anyio
async def test_cancel_dismisses_with_none() -> None:
    results: list[list[str] | None] = []

    async with TableSageApp().run_test() as pilot:
        pilot.app.push_screen(RoleEditorDialog(player_name="Alice", roles=["Zaria"]), results.append)
        await pilot.pause()

        pilot.app.screen.query_one("#role-editor-cancel", Button).press()
        await pilot.pause()

        assert results == [None]


@pytest.mark.anyio
async def test_escape_dismisses_with_none() -> None:
    results: list[list[str] | None] = []

    async with TableSageApp().run_test() as pilot:
        pilot.app.push_screen(RoleEditorDialog(player_name="Alice", roles=["Zaria"]), results.append)
        await pilot.pause()

        await pilot.press("escape")
        await pilot.pause()

        assert results == [None]
