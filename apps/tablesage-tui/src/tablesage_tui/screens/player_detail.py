from __future__ import annotations

import hashlib
import uuid
from pathlib import Path
from typing import TYPE_CHECKING

from tablesage_model.model import Player
from tablesage_model.player_names import validate_player_name
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import DataTable, Static

from ..dialogs import ConfirmationDialog, PlayerDialog
from ..dialogs.file_picker import SelectDirectory
from ..widgets.tablesage_header import TableSageHeader
from ..widgets.voice_clip_table import VoiceClipTable
from .base import TableSageScreen

if TYPE_CHECKING:
    from tablesage_application.voice_clips.clips import ImportResult


class PlayerDetailScreen(TableSageScreen):
    """A single player's metadata, voice-print state, and voice clips."""

    section = "player detail"
    HIDDEN_BINDINGS = [
        Binding("escape", "pop_screen", "Back", key_display="Esc", show=False),
    ]
    COMMON_BINDINGS = [
        Binding("f,F", "import_from_directory", "Folder Import", key_display="F"),
        Binding("m,M", "edit_metadata", "Edit Metadata", key_display="M"),
        Binding("v,V", "review_samples", "Review Outliers", key_display="V"),
        Binding("p,P", "play_clip", "Play", key_display="P"),
        Binding("space", "toggle_mode", "Manual/Autoplay", key_display="Space"),
        Binding("d,D,delete,backspace", "delete_clip", "Delete Voice Clip", key_display="D"),
    ]
    OTHER_BINDINGS = [
        Binding("r,R", "recompute_voice_print", "Recompute", key_display="R"),
        Binding("c,C", "cleanup", "Clean Up", key_display="C"),
    ]

    def __init__(self, player_id: uuid.UUID) -> None:
        super().__init__()
        self._player_id = player_id
        self._player_name = ""

    def compose_content(self) -> ComposeResult:
        with Vertical(id="player-detail-panel", classes="panel surface-2") as panel:
            panel.border_title = " player "

            with Vertical(id="player-metadata"):
                with Horizontal(classes="field-row"):
                    yield Static("Name", classes="field-label")
                    yield Static("", id="player-name-value", classes="field-value")
                with Horizontal(classes="field-row", id="player-stats-row"):
                    yield Static("Voice Print Samples:", classes="field-label")
                    yield Static("", id="player-sample-count-value", classes="field-value")
                    yield Static("", classes="field-spacer")
                    yield Static("Computed At:", classes="field-label")
                    yield Static("", id="player-computed-at-value", classes="field-value")
                    yield Static("", classes="field-spacer")
                    yield Static("Voice Print", classes="field-label")
                    yield Static("", id="player-voice-print-hash-value", classes="field-value")
                    yield Static("", classes="field-spacer")
                    yield Static("Duration", classes="field-label")
                    yield Static("", id="player-total-duration-value", classes="field-value")

            yield Static("Voice Clips", classes="section-title")
            yield Static("Mode: Manual", id="player-playback-mode")
            table = VoiceClipTable(
                id="voice-clips-table", clip_path=lambda filename: self.application.voice_clip_path(self._player_id, filename)
            )
            table.add_column("Clip", key="filename")
            table.add_column("Duration", key="duration")
            yield table

    def on_mount(self) -> None:
        self.refresh_data()
        self.query_one(VoiceClipTable).focus()

    def refresh_data(self) -> None:
        player = self.application.get_player(self._player_id)
        self._player_name = player.name

        self.query_one(TableSageHeader).campaign = self._player_name
        self.query_one("#player-name-value", Static).update(self._player_name)
        self._refresh_voice_print_display(player)
        self._reload_voice_clips()

    # Metadata

    def action_edit_metadata(self) -> None:
        self.app.push_screen(
            PlayerDialog(title="Edit Metadata", name=self._player_name, submit_label="Save", on_submit=self._submit_metadata)
        )

    async def _submit_metadata(self, name: str) -> str | None:
        if name == self._player_name:
            return None
        try:
            validate_player_name(name)
        except ValueError as exc:
            return str(exc)

        proceed = await self.resolve_folder_collision(
            title="Player Folder Exists",
            prompt=(
                f"A player folder named '{name}' already exists on disk. "
                "This may be left over from a previously deleted player. Delete it and continue?"
            ),
            exists=lambda: self.application.player_folder_exists(name),
            delete_existing=lambda: self.application.delete_orphan_player_folder(name),
        )
        if not proceed:
            return f"Rename cancelled: a player folder named '{name}' already exists."

        try:
            renamed = self.application.rename_player(self._player_id, name)
        except ValueError as exc:
            return str(exc)
        self._player_name = renamed.name
        self.query_one(TableSageHeader).campaign = self._player_name
        self.query_one("#player-name-value", Static).update(self._player_name)
        return None

    def _refresh_voice_print_display(self, player: Player) -> None:
        self.query_one("#player-sample-count-value", Static).update(str(player.sample_count))
        computed_at = player.computed_at.strftime("%Y-%m-%d %H:%M") if player.computed_at else "Never"
        self.query_one("#player-computed-at-value", Static).update(computed_at)
        self.query_one("#player-voice-print-hash-value", Static).update(self._voice_print_hash(player))

    @staticmethod
    def _voice_print_hash(player: Player) -> str:
        """A short hash of the voice print, computed here (not stored) purely so a recompute's effect is visible at a glance."""
        if player.voice_print_embedding is None:
            return "None"
        return hashlib.sha256(player.voice_print_embedding.encode()).hexdigest()[:8]

    # Voice clips

    def _reload_voice_clips(self) -> None:
        table = self.query_one("#voice-clips-table", VoiceClipTable)
        selected = self._selected_clip_filename()

        total_duration = 0.0
        # Loading and restoring a selection should stay silent; user navigation still plays clips.
        with table.prevent(DataTable.RowHighlighted):
            table.reset_clips()
            restored_row: int | None = None
            for index, clip in enumerate(self.application.list_voice_clips(self._player_id)):
                table.add_clip(clip.filename, clip.duration_seconds, clip.filename, f"{clip.duration_seconds:.1f}s")
                total_duration += clip.duration_seconds
                if selected is not None and clip.filename == selected:
                    restored_row = index

            if restored_row is not None:
                table.move_cursor(row=restored_row)

        self.query_one("#player-total-duration-value", Static).update(self._format_duration(total_duration))
        self.refresh_bindings()

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        if action in {"delete_clip", "play_clip", "toggle_mode"}:
            return True if self._selected_clip_filename() is not None else None
        return True

    def on_voice_clip_table_playback_changed(self) -> None:
        self.query_one("#player-playback-mode", Static).update(f"Mode: {self.query_one(VoiceClipTable).mode_label}")

    def action_play_clip(self) -> None:
        self.query_one(VoiceClipTable).play_selected()

    def action_toggle_mode(self) -> None:
        self.query_one(VoiceClipTable).toggle_mode()

    def action_review_samples(self) -> None:
        from .voice_sample_review import VoiceSampleReviewScreen

        self.query_one(VoiceClipTable).stop_playback()
        self.app.push_screen(VoiceSampleReviewScreen(self._player_id, self._player_name), lambda _result: self.refresh_data())

    def on_screen_suspend(self) -> None:
        self.query_one(VoiceClipTable).stop_playback()

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        self.refresh_bindings()

    @staticmethod
    def _format_duration(total_seconds: float) -> str:
        """`M:SS` across every clip on disk -- not just the ones the current voice print used."""
        minutes, seconds = divmod(round(total_seconds), 60)
        return f"{minutes}:{seconds:02d}"

    def _selected_clip_filename(self) -> str | None:
        table = self.query_one("#voice-clips-table", DataTable)
        if table.row_count == 0:
            return None
        row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key.value
        return row_key

    def action_delete_clip(self) -> None:
        filename = self._selected_clip_filename()
        if filename is None:
            return

        def on_dismiss(confirmed: bool | None) -> None:
            if not confirmed:
                return
            self.run_with_progress(
                title="Deleting Clip",
                message=f"Deleting '{filename}' and recomputing the voice print…",
                work=lambda: self.application.delete_voice_clip(self._player_id, filename, self.report_progress),
                on_success=self._after_delete_clip,
            )

        self.app.push_screen(
            ConfirmationDialog(
                title="Delete Voice Clip",
                prompt=f"Delete '{filename}'? The voice print will be recomputed from the remaining clips.",
            ),
            on_dismiss,
        )

    def _after_delete_clip(self, player: Player) -> None:
        self._refresh_voice_print_display(player)
        self._reload_voice_clips()

    def action_recompute_voice_print(self) -> None:
        self.run_with_progress(
            title="Recomputing Voice Print",
            message="Embedding voice clips and recomputing the voice print…",
            work=lambda: self.application.recompute_voice_print(self._player_id, self.report_progress),
            on_success=self._after_recompute_voice_print,
        )

    def _after_recompute_voice_print(self, player: Player) -> None:
        self._refresh_voice_print_display(player)
        if player.sample_count:
            self.notify(f"Voice print recomputed from {player.sample_count} clip(s).")
        else:
            self.notify("No voice clips on disk; voice print cleared.")

    def action_cleanup(self) -> None:
        def on_dismiss(confirmed: bool | None) -> None:
            if not confirmed:
                return
            self.run_with_progress(
                title="Cleaning Up",
                message="Recomputing the voice print and removing unused voice clips…",
                work=lambda: self.application.cleanup_voice_clips(self._player_id, self.report_progress),
                on_success=self._after_cleanup,
            )

        self.app.push_screen(
            ConfirmationDialog(
                title="Clean Up Voice Clips",
                prompt="Recompute the voice print and permanently delete any duplicate or outlier clip files it finds?",
            ),
            on_dismiss,
        )

    def _after_cleanup(self, result: tuple[Player, list[str]]) -> None:
        player, deleted_filenames = result
        self._refresh_voice_print_display(player)
        self._reload_voice_clips()
        if deleted_filenames:
            self.notify(f"Removed {len(deleted_filenames)} unused voice clip(s).")
        else:
            self.notify("No unused voice clips found.")

    def action_import_from_directory(self) -> None:
        def on_picked(source_dir: Path | None) -> None:
            if source_dir is None:
                return

            try:
                self.application.validate_import_source(source_dir)
            except ValueError as exc:
                self.notify(str(exc), severity="error")
                return

            def on_clean_choice(should_clean_audio: bool | None) -> None:
                if should_clean_audio is None:
                    return
                self._confirm_directory_import(source_dir, should_clean_audio)

            self.app.push_screen(
                ConfirmationDialog(
                    title="Clean Audio",
                    prompt="Clean these audio files (denoise, format) before importing them?",
                ),
                on_clean_choice,
            )

        self.app.push_screen(
            SelectDirectory(title="Import Voice Clips From Directory", location=Path.home()),
            on_picked,
        )

    def _confirm_directory_import(self, source_dir: Path, should_clean_audio: bool) -> None:
        prior_clips = self.application.find_prior_import_clips(self._player_id, source_dir)
        if not prior_clips:
            self._run_directory_import(source_dir, should_clean_audio)
            return

        def on_confirm(confirmed: bool | None) -> None:
            if confirmed:
                self._run_directory_import(source_dir, should_clean_audio)

        self.app.push_screen(
            ConfirmationDialog(
                title="Replace Prior Import",
                prompt=f"This will replace {len(prior_clips)} clip(s) previously imported from this directory.",
            ),
            on_confirm,
        )

    def _run_directory_import(self, source_dir: Path, should_clean_audio: bool) -> None:
        message = f"Importing voice clips from '{source_dir}'…"
        if should_clean_audio:
            message = f"Cleaning and importing voice clips from '{source_dir}'…"
        self.run_with_progress(
            title="Importing Voice Clips",
            message=message,
            work=lambda: self.application.import_voice_clips(
                self._player_id, source_dir, self.report_progress, should_clean_audio=should_clean_audio
            ),
            on_success=self._after_import_from_directory,
        )

    def _after_import_from_directory(self, result: tuple[Player, ImportResult]) -> None:
        player, import_result = result
        self._refresh_voice_print_display(player)
        self._reload_voice_clips()

        if import_result.imported_count == 0:
            self.notify(
                f"No usable clips imported; voice print unchanged. Skipped {len(import_result.rejected_filenames)} clip(s).",
                severity="warning",
            )
            return

        message = f"Imported {import_result.imported_count} clip(s)."
        if import_result.replaced_count:
            message += f" Replaced {import_result.replaced_count} prior clip(s)."
        if import_result.rejected_filenames:
            message += f" Skipped {len(import_result.rejected_filenames)} (couldn't embed)."
        if import_result.removed_outlier_filenames:
            message += f" Removed {len(import_result.removed_outlier_filenames)} outlier clip(s)."
        self.notify(message)
