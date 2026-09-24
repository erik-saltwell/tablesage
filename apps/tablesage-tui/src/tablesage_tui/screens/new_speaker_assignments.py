from __future__ import annotations

import uuid
from collections.abc import Callable

from rich.text import Text
from tablesage_application.session_pipeline.review_new_speaker_assignments import ReviewData, ReviewPlayer, ReviewUtterance
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, DataTable, Static

from ..audio_playback import ReviewPlayback
from .base import TableSageScreen

# Actions on the highlighted utterance, which need a non-empty list.
_ROW_ACTIONS = frozenset({"toggle_removed", "replay", "toggle_mode"})


class _PaneTable(DataTable[object]):
    """A row table whose Left/Right move focus between the two panes instead of between columns."""

    def __init__(self, *, on_left: Callable[[], None], on_right: Callable[[], None], id: str) -> None:
        super().__init__(id=id, cursor_type="row", zebra_stripes=True, classes="tablesage-table")
        self._on_left = on_left
        self._on_right = on_right

    def action_cursor_left(self) -> None:
        self._on_left()

    def action_cursor_right(self) -> None:
        self._on_right()


def _format_seconds(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes, rest = divmod(round(seconds), 60)
    return f"{minutes}m {rest:02d}s"


class NewSpeakerAssignmentsScreen(TableSageScreen):
    """Step 3 of Process Session: keep or remove each utterance proposed as a new player's voice sample.

    Remove-only: a player's list can shrink but never grow. Removal is a toggle, and totals count
    kept utterances only. Confirm saves the kept utterances and hands control back to the caller,
    which continues processing; Cancel returns without writing anything.
    """

    section = "process session · new speaker assignments"
    COMMON_BINDINGS = [
        Binding("space", "toggle_mode", "Auto/Manual", key_display="Space"),
        Binding("r,R", "replay", "Replay", key_display="R"),
        Binding("d,D,delete,backspace", "toggle_removed", "Keep/Remove", key_display="D"),
        Binding("c,C", "confirm", "Confirm", key_display="C"),
        Binding("escape", "leave_utterances", "Players", key_display="Esc"),
        Binding("escape", "cancel", "Cancel", key_display="Esc"),
    ]

    def __init__(self, session_id: uuid.UUID, on_confirmed: Callable[[], None]) -> None:
        super().__init__()
        self._session_id = session_id
        self._on_confirmed = on_confirmed
        self._data: ReviewData | None = None
        self._removed: set[int] = set()
        self._player_row = 0
        self._playhead = 0
        self._programmatic_move = False
        self._playback = ReviewPlayback(self, on_advance=self._auto_advance, on_mode_changed=lambda: None)

    def compose_content(self) -> ComposeResult:
        with Vertical(id="new-speaker-review-panel", classes="panel surface-2") as panel:
            panel.border_title = " New Speaker Assignments "
            yield Static("Keep only utterances you're sure each new player spoke; they become voice samples.", classes="section-title")
            with Horizontal(id="new-speaker-review-columns"):
                with Vertical(id="new-speaker-review-players-column"):
                    players = _PaneTable(id="new-speaker-review-players", on_left=lambda: None, on_right=self._enter_utterances)
                    players.border_title = " Players "
                    players.add_column("Player", key="player")
                    players.add_column("Samples", key="samples")
                    players.add_column("Speech", key="speech")
                    yield players
                with Vertical(id="new-speaker-review-utterances-column"):
                    utterances = _PaneTable(id="new-speaker-review-utterances", on_left=self.action_leave_utterances, on_right=lambda: None)
                    utterances.border_title = " Utterances "
                    utterances.add_column("", key="removed", width=3)
                    utterances.add_column("Speech", key="speech")
                    utterances.add_column("Text", key="text")
                    yield utterances
            yield Static("No new players, so there's nothing to review.", id="new-speaker-review-empty")
            with Horizontal(id="new-speaker-review-actions"):
                yield Button("Cancel", id="new-speaker-review-cancel")
                yield Button("Confirm", id="new-speaker-review-confirm", variant="primary")

    def on_mount(self) -> None:
        self.query_one("#new-speaker-review-columns").display = False
        self.query_one("#new-speaker-review-empty").display = False
        try:
            data = self.application.new_speaker_assignment_review(self._session_id)
        except (OSError, ValueError) as exc:
            self._fail(f"Could not load the new speaker assignments: {exc}")
            return
        if not data.players:
            self._show(data)
            return
        indices = [utterance.index for player in data.players for utterance in player.utterances]
        self.run_with_progress(
            title="Review New Speaker Assignments",
            message="Preparing clips…",
            work=lambda: self.application.extract_new_speaker_review_clips(self._session_id, indices, self.report_progress),
            on_success=lambda _result: self._show(data),
            on_error=lambda exc: self._fail(f"Could not prepare clips: {exc}"),
        )

    def _fail(self, message: str) -> None:
        self.notify(message, severity="error")
        self._leave()

    def _show(self, data: ReviewData) -> None:
        self._data = data
        self._removed = set(data.removed)
        self.query_one("#new-speaker-review-columns").display = bool(data.players)
        self.query_one("#new-speaker-review-empty").display = not data.players
        if not data.players:
            self.query_one("#new-speaker-review-confirm", Button).focus()
            return
        table = self.query_one("#new-speaker-review-players", DataTable)
        for index, player in enumerate(data.players):
            table.add_row(*self._player_cells(player), key=str(index))
        self._fill_utterances(0)
        table.focus()

    # Players pane

    def _player_cells(self, player: ReviewPlayer) -> tuple[str, str, str]:
        kept = [utterance for utterance in player.utterances if utterance.index not in self._removed]
        seconds = sum(utterance.speech_seconds for utterance in kept)
        return player.player_name, str(len(kept)), _format_seconds(seconds)

    def _refresh_player_row(self, row: int) -> None:
        assert self._data is not None
        table = self.query_one("#new-speaker-review-players", DataTable)
        for column, value in zip(("player", "samples", "speech"), self._player_cells(self._data.players[row]), strict=True):
            table.update_cell(str(row), column, value)

    def _current_player(self) -> ReviewPlayer:
        assert self._data is not None
        return self._data.players[self._player_row]

    def _fill_utterances(self, player_row: int) -> None:
        self._player_row = player_row
        self._playhead = 0
        table = self.query_one("#new-speaker-review-utterances", DataTable)
        table.border_title = f" Utterances · {self._current_player().player_name} "
        table.clear()
        for utterance in self._current_player().utterances:
            table.add_row(*self._utterance_cells(utterance), key=str(utterance.index))

    # Utterances pane

    def _utterance_cells(self, utterance: ReviewUtterance) -> tuple[str, Text, Text]:
        removed = utterance.index in self._removed
        style = "dim strike" if removed else ""
        return "✗" if removed else "", Text(_format_seconds(utterance.speech_seconds), style=style), Text(utterance.text, style=style)

    def _refresh_utterance_row(self, row: int) -> None:
        utterance = self._current_player().utterances[row]
        table = self.query_one("#new-speaker-review-utterances", DataTable)
        for column, value in zip(("removed", "speech", "text"), self._utterance_cells(utterance), strict=True):
            table.update_cell(str(utterance.index), column, value)

    def _utterances_focused(self) -> bool:
        return self.focused is self.query_one("#new-speaker-review-utterances", DataTable)

    def _enter_utterances(self) -> None:
        if self._data is None or not self._current_player().utterances:
            return
        table = self.query_one("#new-speaker-review-utterances", DataTable)
        self._playhead = 0
        self._programmatic_move = True
        table.move_cursor(row=0)
        table.focus()
        self._play()

    def _play(self) -> None:
        utterance = self._current_player().utterances[self._playhead]
        self._playback.play(self.application.new_speaker_review_clip(self._session_id, utterance.index), utterance.clip_seconds)

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        event.stop()
        self.refresh_bindings()
        if self._data is None or not self._data.players:
            return
        if event.data_table.id == "new-speaker-review-players":
            if event.cursor_row != self._player_row:
                self._playback.stop()
                self._playback.set_manual()
                self._fill_utterances(event.cursor_row)
            return
        programmatic = self._programmatic_move
        self._programmatic_move = False
        if event.cursor_row == self._playhead:
            return
        self._playhead = event.cursor_row
        if not programmatic:
            self._playback.set_manual()
        if self._utterances_focused():
            self._play()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        event.stop()
        if event.data_table.id == "new-speaker-review-players":
            self._enter_utterances()
            return
        # Clicking an already-highlighted utterance (or pressing Enter) posts no highlight change,
        # so it's handled here; clicking a different row is handled by on_data_table_row_highlighted.
        if self._data is None or not self._current_player().utterances:
            return
        self._playhead = event.cursor_row
        self._playback.set_manual()
        self._play()

    def on_descendant_focus(self) -> None:
        self.refresh_bindings()

    def _auto_advance(self) -> bool:
        """Auto mode stays within the current player's list."""
        if self._playhead + 1 >= len(self._current_player().utterances):
            return False
        self._move_to(self._playhead + 1)
        return True

    def _move_to(self, row: int) -> None:
        self._programmatic_move = True
        self.query_one("#new-speaker-review-utterances", DataTable).move_cursor(row=row)

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        # False rather than None: a disabled binding still claims its key in the footer, which
        # would hide Esc's other meaning.
        in_utterances = self._data is not None and self._utterances_focused()
        if action in _ROW_ACTIONS:
            return in_utterances and bool(self._current_player().utterances)
        if action == "leave_utterances":
            return in_utterances
        if action == "cancel":
            return not in_utterances
        return super().check_action(action, parameters)

    def action_toggle_removed(self) -> None:
        index = self._current_player().utterances[self._playhead].index
        self._removed.symmetric_difference_update({index})
        self._refresh_utterance_row(self._playhead)
        self._refresh_player_row(self._player_row)
        if self._playhead + 1 < len(self._current_player().utterances):
            self._move_to(self._playhead + 1)

    def action_replay(self) -> None:
        self._play()

    def action_toggle_mode(self) -> None:
        self._playback.toggle_mode()

    def action_leave_utterances(self) -> None:
        self._playback.stop()
        self._playback.set_manual()
        self.query_one("#new-speaker-review-players", DataTable).focus()

    # Confirm / cancel

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.id == "new-speaker-review-confirm":
            self.action_confirm()
        elif event.button.id == "new-speaker-review-cancel":
            self.action_cancel()

    def action_confirm(self) -> None:
        if self._data is None:
            return
        kept = {
            player.player_id: [utterance.index for utterance in player.utterances if utterance.index not in self._removed]
            for player in self._data.players
        }
        try:
            self.application.confirm_new_speaker_assignment_review(self._session_id, kept)
        except (OSError, ValueError) as exc:
            self.notify(f"Could not save the reviewed assignments: {exc}", severity="error")
            return
        self._leave()
        self._on_confirmed()

    def action_cancel(self) -> None:
        self._leave()

    def _leave(self) -> None:
        self._playback.stop()
        self.application.discard_new_speaker_review_clips(self._session_id)
        self.app.pop_screen()

    def on_unmount(self) -> None:
        self._playback.stop()
        self.application.discard_new_speaker_review_clips(self._session_id)
