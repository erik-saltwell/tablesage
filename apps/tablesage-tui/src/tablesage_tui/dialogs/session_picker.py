from __future__ import annotations

import uuid
from typing import cast

from rich.text import Text
from tablesage_model.model import Campaign
from tablesage_model.model import Session as GameSession
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, DataTable, Select, Static
from textual.widgets.select import NoSelection


class SessionFromCampaignPickerDialog(ModalScreen[uuid.UUID | None]):
    """Pick a transcribed session to enhance players from, scoped to a chosen campaign.

    Sessions without a transcript are listed but grayed out (visible, not selectable) --
    the user should see "this session exists but hasn't been transcribed yet," not wonder
    why a session they know about is missing. See
    `.documentation/enhance_players_from_session.md`.
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=False),
    ]

    def __init__(
        self,
        *,
        campaigns: list[Campaign],
        sessions_by_campaign: dict[uuid.UUID, list[GameSession]],
        has_transcript: dict[uuid.UUID, bool],
    ) -> None:
        super().__init__()
        self._campaigns = campaigns
        self._sessions_by_campaign = sessions_by_campaign
        self._has_transcript = has_transcript

    def compose(self) -> ComposeResult:
        with Vertical(id="session-picker-dialog") as dialog:
            dialog.border_title = "From Session"

            if not self._campaigns:
                yield Static("No campaigns are available.", id="session-picker-empty")
                with Horizontal(classes="dialog-actions"):
                    yield Button("Close", id="session-picker-close")
                return

            with Horizontal(id="session-picker-campaign-row"):
                yield Static("Campaign", classes="field-label")
                yield Select[uuid.UUID](
                    [(campaign.name, campaign.id) for campaign in self._campaigns],
                    id="session-picker-campaign-select",
                    value=self._campaigns[0].id,
                    allow_blank=False,
                )

            table: DataTable[str] = DataTable(id="session-picker-table", cursor_type="row", zebra_stripes=True, classes="tablesage-table")
            table.add_column("Session", key="name")
            table.add_column("Date", key="date")
            table.add_column("Status", key="status")
            yield table

            with Horizontal(classes="dialog-actions"):
                yield Button("Cancel", id="session-picker-cancel")
                yield Button("Select", id="session-picker-select", variant="primary")

    def on_mount(self) -> None:
        if self._campaigns:
            self._reload_sessions(self._campaigns[0].id)
            self.query_one("#session-picker-table", DataTable).focus()

    def _reload_sessions(self, campaign_id: uuid.UUID) -> None:
        table = self.query_one("#session-picker-table", DataTable)
        table.clear()
        for session in self._sessions_by_campaign.get(campaign_id, []):
            eligible = self._has_transcript.get(session.id, False)
            style = "" if eligible else "dim"
            status = "Ready" if eligible else "No transcript"
            table.add_row(
                Text(session.name, style=style),
                Text(str(session.session_date) if session.session_date else "", style=style),
                Text(status, style=style),
                key=str(session.id),
            )

    def on_select_changed(self, event: Select.Changed) -> None:
        event.stop()
        value = event.value
        if isinstance(value, NoSelection):
            return
        self._reload_sessions(cast(uuid.UUID, value))

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        event.stop()
        self._submit()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id in ("session-picker-cancel", "session-picker-close"):
            self.dismiss(None)
        elif button_id == "session-picker-select":
            self._submit()

    def action_cancel(self) -> None:
        self.dismiss(None)

    def _submit(self) -> None:
        table = self.query_one("#session-picker-table", DataTable)
        if table.row_count == 0:
            return
        row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key.value
        if row_key is None:
            return
        session_id = uuid.UUID(row_key)
        if not self._has_transcript.get(session_id, False):
            self.notify("This session hasn't been transcribed yet.", severity="error")
            return
        self.dismiss(session_id)
