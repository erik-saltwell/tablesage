from __future__ import annotations

import re
from collections.abc import Awaitable, Callable
from datetime import date

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Static

from ..widgets import EqualWidthButtonRow

OnSessionSubmit = Callable[[str, date | None], Awaitable[str | None]]


class SessionDialog(ModalScreen[None]):
    """Collect a session's name and date for both creation and metadata editing.

    Field-level validation covers name non-blankness, an optional required date, and strict date format (`YYYY-MM-DD`) --
    the date starts blank and has no default. Everything else -- the application call -- is the
    caller's `on_submit`, awaited here: `None` dismisses, a string is shown as an inline error
    with every field's typed value kept (see `intent.md` in the `metadata-below-lists` work
    item). Session folders are numbered slots, not name-derived, so there is no folder-collision
    check on a session name/date, unlike Player and Campaign.
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=False),
    ]

    def __init__(
        self,
        *,
        title: str,
        on_submit: OnSessionSubmit,
        name: str = "",
        session_date: date | None = None,
        submit_label: str = "Save",
        date_required: bool = False,
    ) -> None:
        super().__init__()
        self._title = title
        self._on_submit = on_submit
        self._name = name
        self._session_date = session_date
        self._submit_label = submit_label
        self._date_required = date_required

    def compose(self) -> ComposeResult:
        with Vertical(id="session-dialog") as dialog:
            dialog.border_title = self._title
            with Horizontal(classes="field-row"):
                yield Static("Name", classes="field-label")
                yield Input(id="session-dialog-name", value=self._name)
            with Horizontal(classes="field-row"):
                yield Static("Date", classes="field-label")
                yield Input(
                    id="session-dialog-date",
                    value=str(self._session_date) if self._session_date else "",
                    placeholder="YYYY-MM-DD (required)" if self._date_required else "YYYY-MM-DD (optional)",
                )
            yield Static("", id="session-dialog-error", classes="dialog-error", markup=False)
            with EqualWidthButtonRow(classes="dialog-actions"):
                yield Button("Cancel", id="session-dialog-cancel")
                yield Button(self._submit_label, id="session-dialog-submit", variant="primary")

    def on_mount(self) -> None:
        self.query_one("#session-dialog-name", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "session-dialog-cancel":
            self.dismiss(None)
        elif event.button.id == "session-dialog-submit":
            self.run_worker(self._submit())

    def on_input_submitted(self, event: Input.Submitted) -> None:
        event.stop()
        self.run_worker(self._submit())

    def action_cancel(self) -> None:
        self.dismiss(None)

    async def _submit(self) -> None:
        name = self.query_one("#session-dialog-name", Input).value.strip()
        if not name:
            self._show_error("Name is required.")
            return

        raw_date = self.query_one("#session-dialog-date", Input).value.strip()
        session_date: date | None
        if not raw_date:
            if self._date_required:
                self._show_error("Date is required.")
                return
            session_date = None
        else:
            try:
                if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", raw_date):
                    raise ValueError("Expected YYYY-MM-DD")
                session_date = date.fromisoformat(raw_date)
            except ValueError:
                self._show_error(f"'{raw_date}' isn't a valid date (expected YYYY-MM-DD).")
                return

        submit_button = self.query_one("#session-dialog-submit", Button)
        submit_button.disabled = True
        try:
            error = await self._on_submit(name, session_date)
        finally:
            submit_button.disabled = False

        if error is None:
            self.dismiss(None)
        else:
            self._show_error(error)

    def _show_error(self, message: str) -> None:
        self.query_one("#session-dialog-error", Static).update(message)
