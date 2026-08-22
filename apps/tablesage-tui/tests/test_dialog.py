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
    assert button.styles.border.top[0] == "solid"
    assert button.styles.border.top[1].hex == border


@pytest.mark.anyio
async def test_dialog_buttons_cover_secondary_and_primary_states() -> None:
    """Every Button state shares one identity color for text+border (secondary:
    sage-400 #A3B88C, primary: sage-200 #D7E6BE) -- see the Button rule in
    app.tcss. Only resting (transparent bg), hover/focus (50%-alpha wash of the
    identity color), pressed (solid identity-color bg, transparent text), and
    disabled (both text/border become $fg-muted #8F988B, no primary/secondary
    distinction) diverge from that identity color.
    """
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
            border="#A3B88C",
        )

        await pilot.hover(cancel, (1, 1))
        assert_button_colors(
            cancel,
            background="#A3B88C7F",
            foreground="#A3B88C",
            border="#A3B88C",
        )

        cancel.focus()
        await pilot.pause()
        assert_button_colors(
            cancel,
            background="#A3B88C7F",
            foreground="#A3B88C",
            border="#A3B88C",
        )

        cancel.add_class("-active")
        await pilot.pause()
        assert_button_colors(
            cancel,
            background="#A3B88C",
            foreground="#00000000",
            border="#A3B88C",
        )
        cancel.remove_class("-active")

        cancel.disabled = True
        await pilot.pause()
        assert_button_colors(
            cancel,
            background="#00000000",
            foreground="#8F988B",
            border="#8F988B",
        )

        pilot.app.screen.query_one(Input).value = "Example"
        await pilot.pause()

        assert_button_colors(
            submit,
            background="#00000000",
            foreground="#D7E6BE",
            border="#D7E6BE",
        )

        await pilot.hover(submit, (1, 1))
        assert_button_colors(
            submit,
            background="#D7E6BE7F",
            foreground="#D7E6BE",
            border="#D7E6BE",
        )

        submit.focus()
        await pilot.pause()
        assert_button_colors(
            submit,
            background="#D7E6BE7F",
            foreground="#D7E6BE",
            border="#D7E6BE",
        )

        submit.add_class("-active")
        await pilot.pause()
        assert_button_colors(
            submit,
            background="#D7E6BE",
            foreground="#00000000",
            border="#D7E6BE",
        )
        submit.remove_class("-active")

        submit.disabled = True
        await pilot.pause()
        assert_button_colors(
            submit,
            background="#00000000",
            foreground="#8F988B",
            border="#8F988B",
        )
