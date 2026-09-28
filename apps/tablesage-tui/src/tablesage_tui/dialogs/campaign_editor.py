from __future__ import annotations

from collections.abc import Awaitable, Callable

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Static

from ..widgets import EqualWidthButtonRow

OnCampaignSubmit = Callable[[str, str | None, str | None], Awaitable[str | None]]


class CampaignDialog(ModalScreen[None]):
    """Collect a campaign's name, description, and game system for both creation and editing.

    Field-level validation here is limited to name non-blankness. Everything else -- the
    application call and any folder-collision confirmation -- is the caller's `on_submit`,
    awaited here: `None` dismisses, a string is shown as an inline error with every field's
    typed value kept (see `intent.md` in the `metadata-below-lists` work item).
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=False),
    ]

    def __init__(
        self,
        *,
        title: str,
        on_submit: OnCampaignSubmit,
        name: str = "",
        description: str = "",
        game_system: str = "",
        submit_label: str = "Save",
    ) -> None:
        super().__init__()
        self._title = title
        self._on_submit = on_submit
        self._name = name
        self._description = description
        self._game_system = game_system
        self._submit_label = submit_label

    def compose(self) -> ComposeResult:
        with Vertical(id="campaign-dialog") as dialog:
            dialog.border_title = self._title
            with Horizontal(classes="field-row"):
                yield Static("Name", classes="field-label")
                yield Input(id="campaign-dialog-name", value=self._name)
            with Horizontal(classes="field-row"):
                yield Static("Description", classes="field-label")
                yield Input(id="campaign-dialog-description", value=self._description, placeholder="Optional description")
            with Horizontal(classes="field-row"):
                yield Static("Game System", classes="field-label")
                yield Input(id="campaign-dialog-game-system", value=self._game_system, placeholder="Optional game system")
            yield Static("", id="campaign-dialog-error", classes="dialog-error", markup=False)
            with EqualWidthButtonRow(classes="dialog-actions"):
                yield Button("Cancel", id="campaign-dialog-cancel")
                yield Button(self._submit_label, id="campaign-dialog-submit", variant="primary")

    def on_mount(self) -> None:
        self.query_one("#campaign-dialog-name", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "campaign-dialog-cancel":
            self.dismiss(None)
        elif event.button.id == "campaign-dialog-submit":
            self.run_worker(self._submit())

    def on_input_submitted(self, event: Input.Submitted) -> None:
        event.stop()
        self.run_worker(self._submit())

    def action_cancel(self) -> None:
        self.dismiss(None)

    async def _submit(self) -> None:
        name = self.query_one("#campaign-dialog-name", Input).value.strip()
        if not name:
            self._show_error("Name is required.")
            return
        description = self.query_one("#campaign-dialog-description", Input).value.strip() or None
        game_system = self.query_one("#campaign-dialog-game-system", Input).value.strip() or None

        submit_button = self.query_one("#campaign-dialog-submit", Button)
        submit_button.disabled = True
        try:
            error = await self._on_submit(name, description, game_system)
        finally:
            submit_button.disabled = False

        if error is None:
            self.dismiss(None)
        else:
            self._show_error(error)

    def _show_error(self, message: str) -> None:
        self.query_one("#campaign-dialog-error", Static).update(message)
