from __future__ import annotations

import uuid
from collections.abc import Callable

from rich.text import Text
from tablesage_application.voice_clips.review import RankedVoiceClip, VoiceSampleReview
from tablesage_model.model import Player
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import Button, Static

from ..dialogs import ConfirmationDialog
from ..widgets import EqualWidthButtonRow
from ..widgets.voice_clip_table import VoiceClipTable
from .base import TableSageScreen

_BATCH_SIZE = 20


class VoiceSampleReviewScreen(TableSageScreen):
    """Review the least similar stored samples, with reversible removals in fixed batches."""

    section = "review outliers"
    HIDDEN_BINDINGS = [Binding("escape", "cancel", "Cancel", show=False)]
    COMMON_BINDINGS = [
        Binding("c,C", "continue", "Continue", key_display="C"),
        Binding("l,L", "load_more", "Load 20 More", key_display="L"),
        Binding("r,R", "replay", "Replay", key_display="R"),
        Binding("space", "toggle_mode", "Manual/Autoplay", key_display="Space"),
        Binding("d,D,delete,backspace", "toggle_removed", "Delete Clip", key_display="D"),
    ]

    def __init__(self, player_id: uuid.UUID, player_name: str) -> None:
        super().__init__()
        self._player_id = player_id
        self.campaign = player_name
        self._data: VoiceSampleReview | None = None
        self._loaded = 0
        self._removed: set[str] = set()

    @property
    def table(self) -> VoiceClipTable:
        return self.query_one("#voice-sample-review-table", VoiceClipTable)

    def compose_content(self) -> ComposeResult:
        with Vertical(id="voice-sample-review-panel", classes="panel surface-2") as panel:
            panel.border_title = f" Review Outliers · {self.campaign} "
            yield Static(
                "Listen for the right speaker. Lower similarity puts a clip earlier; it does not prove a wrong speaker.",
                id="voice-sample-review-help",
            )
            yield Static("Mode: Manual", id="voice-sample-review-status")
            yield Static("", id="voice-sample-review-cleanup")
            table = VoiceClipTable(
                id="voice-sample-review-table", clip_path=lambda filename: self.application.voice_clip_path(self._player_id, filename)
            )
            table.add_column("", key="removed", width=3)
            table.add_column("Clip", key="filename")
            table.add_column("Duration", key="duration")
            table.add_column("Similarity", key="similarity")
            yield table
        with EqualWidthButtonRow(id="voice-sample-review-actions"):
            yield Button("Cancel", id="voice-sample-review-cancel")
            yield Button("Continue", id="voice-sample-review-continue", variant="primary", disabled=True)

    def on_mount(self) -> None:
        self.run_with_progress(
            title="Review Outliers",
            message="Cleaning up excluded clips and comparing remaining voices…",
            work=lambda: self.application.prepare_voice_sample_review(self._player_id, self.report_progress),
            on_success=self._show_review,
            on_error=self._fail,
        )

    def _show_review(self, data: VoiceSampleReview) -> None:
        self._data = data
        if not data.clips:
            self.notify(
                f"No usable clips to review. Cleanup deleted {len(data.deleted_filenames)} clip(s); "
                f"skipped {len(data.skipped_filenames)} unscorable clip(s).",
                severity="warning",
            )
            self.dismiss()
            return
        self.query_one("#voice-sample-review-cleanup", Static).update(
            f"Cleanup permanently deleted {len(data.deleted_filenames)} clip(s). "
            f"Skipped {len(data.skipped_filenames)} unscorable clip(s). Cancel discards only marked removals."
        )
        self.query_one("#voice-sample-review-continue", Button).disabled = False
        self.action_load_more()
        self.table.focus()
        self.table.play_selected()

    def _cells(self, clip: RankedVoiceClip) -> tuple[Text, Text, Text, Text]:
        removed = clip.filename in self._removed
        style = "dim strike" if removed else ""
        return (
            Text("✗" if removed else ""),
            Text(clip.filename, style=style),
            Text(f"{clip.duration_seconds:.1f}s", style=style),
            Text(f"{clip.similarity:.3f}", style=style),
        )

    def _update_status(self) -> None:
        total = len(self._data.clips) if self._data is not None else 0
        self.query_one("#voice-sample-review-status", Static).update(
            f"Mode: {self.table.mode_label}   ·   Loaded: {self._loaded} of {total}   ·   Marked for deletion: {len(self._removed)}"
        )
        self.refresh_bindings()

    def on_voice_clip_table_playback_changed(self) -> None:
        self._update_status()

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        if action == "load_more":
            return True if self._data is not None and self._loaded < len(self._data.clips) else None
        if action in {"continue", "replay", "toggle_mode", "toggle_removed"}:
            return True if self._data is not None and self._loaded else None
        if action == "refresh_screen":
            return False  # A review's ranking must stay fixed for the visit.
        return super().check_action(action, parameters)

    def action_load_more(self) -> None:
        if self._data is None:
            return
        end = min(self._loaded + _BATCH_SIZE, len(self._data.clips))
        for clip in self._data.clips[self._loaded : end]:
            self.table.add_clip(clip.filename, clip.duration_seconds, *self._cells(clip))
        self._loaded = end
        self._update_status()

    def action_replay(self) -> None:
        self.table.play_selected()

    def action_toggle_mode(self) -> None:
        self.table.toggle_mode()

    def action_toggle_removed(self) -> None:
        filename = self.table.selected_filename
        if self._data is None or filename is None:
            return
        self._removed.symmetric_difference_update({filename})
        clip = self._data.clips[self.table.cursor_row]
        for column, value in zip(("removed", "filename", "duration", "similarity"), self._cells(clip), strict=True):
            self.table.update_cell(filename, column, value)
        self._update_status()
        self.table.advance()

    def action_continue(self) -> None:
        if self._data is None:
            return
        self.table.stop_playback()
        if not self._removed:
            self.dismiss()
            return
        self.run_with_progress(
            title="Applying Sample Review",
            message=f"Deleting {len(self._removed)} marked clip(s) and recomputing the voice print…",
            work=lambda: self.application.delete_voice_clips(self._player_id, sorted(self._removed), self.report_progress),
            on_success=self._applied,
            on_error=self._fail,
        )

    def _applied(self, _player: Player) -> None:
        self.dismiss()

    def _fail(self, error: BaseException) -> None:
        self.notify(str(error), severity="error", markup=False)
        self.table.stop_playback()
        self.dismiss()

    def confirm_leave(self, leave: Callable[[], object], *, quitting: bool = False) -> None:
        self.table.stop_playback()
        if not self._removed:
            leave()
            return

        def on_choice(answer: bool | None) -> None:
            if answer:
                leave()

        self.app.push_screen(
            ConfirmationDialog(
                title="Discard Sample Removals?",
                prompt=f"Discard {len(self._removed)} pending removal(s)? Automatic cleanup is already permanent.",
                show_cancel=False,
                no_label="Keep Reviewing",
                yes_label="Discard and Quit" if quitting else "Discard",
            ),
            on_choice,
        )

    def action_cancel(self) -> None:
        self.confirm_leave(self.dismiss)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.id == "voice-sample-review-continue":
            self.action_continue()
        elif event.button.id == "voice-sample-review-cancel":
            self.action_cancel()

    def on_screen_suspend(self) -> None:
        self.table.stop_playback()
