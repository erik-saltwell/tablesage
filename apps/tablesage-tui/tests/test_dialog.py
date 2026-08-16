import pytest
from tablesage_tui.dialogs import TextInputDialog
from tablesage_tui.screens.main_app import TableSageApp
from textual.widgets import Button, Input


def assert_button_colors(
    button: Button,
    *,
    background: str,
    foreground: str,
    border: str,
) -> None:
    assert button.styles.background.hex == background
    assert button.styles.color.hex == foreground
    assert button.styles.border.top[0] == "tall"
    assert button.styles.border.top[1].hex == border


@pytest.mark.anyio
async def test_dialog_buttons_cover_secondary_and_primary_states() -> None:
    async with TableSageApp().run_test(size=(100, 30)) as pilot:
        pilot.app.push_screen(
            TextInputDialog(
                title="New Campaign",
                prompt="Enter a name",
                placeholder="Campaign name",
                submit_label="Create Campaign",
            )
        )
        await pilot.pause()

        cancel = pilot.app.screen.query_one("#text-input-cancel", Button)
        submit = pilot.app.screen.query_one("#text-input-submit", Button)

        assert cancel.region.width == submit.region.width
        assert cancel.region.height == submit.region.height == 3
        assert cancel.region.width > len(str(cancel.label))
        assert submit.region.width > len(str(submit.label))

        assert_button_colors(
            cancel,
            background="#00000000",
            foreground="#A3B88C",
            border="#5B714A",
        )
        assert_button_colors(
            submit,
            background="#5B714A",
            foreground="#171E19",
            border="#5B714A",
        )

        await pilot.hover(cancel, (1, 1))
        assert_button_colors(
            cancel,
            background="#35442D",
            foreground="#D6D1BF",
            border="#5B714A",
        )

        cancel.focus()
        await pilot.pause()
        assert_button_colors(
            cancel,
            background="#35442D",
            foreground="#D6D1BF",
            border="#5B714A",
        )

        cancel.add_class("-active")
        await pilot.pause()
        assert_button_colors(
            cancel,
            background="#5B714A",
            foreground="#090D0A",
            border="#5B714A",
        )

        cancel.disabled = True
        await pilot.pause()
        assert_button_colors(
            cancel,
            background="#00000000",
            foreground="#485A3B",
            border="#5B714A",
        )

        pilot.app.screen.query_one(Input).value = "Example"
        await pilot.pause()

        assert_button_colors(
            submit,
            background="#5B714A",
            foreground="#090D0A",
            border="#5B714A",
        )

        await pilot.hover(submit, (1, 1))
        assert_button_colors(
            submit,
            background="#A3B88C",
            foreground="#090D0A",
            border="#5B714A",
        )

        submit.focus()
        await pilot.pause()
        assert_button_colors(
            submit,
            background="#5B714A",
            foreground="#090D0A",
            border="#5B714A",
        )

        submit.add_class("-active")
        await pilot.pause()
        assert_button_colors(
            submit,
            background="#5B714A",
            foreground="#090D0A",
            border="#5B714A",
        )
