from __future__ import annotations

import uuid
from collections.abc import Callable
from pathlib import Path

from rich.text import Text
from tablesage_application.campaign_corrections import Mapping
from tablesage_application.session_pipeline import transcript_review
from tablesage_tools.model import Transcript
from tablesage_tools.speakers import UNASSIGNED_SPEAKER
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, DataTable, Static
from textual.widgets.data_table import CursorType

from ..audio_playback import PlaybackMode, ReviewPlayback
from ..dialogs import (
    ConfirmationDialog,
    FindReplaceDialog,
    FindReplaceResult,
    ManualReviewUtteranceDialog,
    ManualReviewUtteranceResult,
)
from ..widgets import EqualWidthButtonRow
from .base import TableSageScreen

_MAX_ASSIGNABLE_ATTENDEES = 9
_DIM_STYLE = "dim"


class _ReviewTable(DataTable[object]):
    """A `DataTable` whose `Up`/`Down` cursor movement skips rows `is_row_enabled` rejects.

    Mouse clicks aren't filtered here -- `DataTable` has no per-row disabled/unclickable
    concept, so a click on a filtered row is instead caught and bounced back by
    `ManualReviewScreen.on_data_table_row_highlighted`, which can tell the two apart
    because keyboard-driven moves are guaranteed valid by this override.
    """

    def __init__(
        self,
        *,
        is_row_enabled: Callable[[int], bool],
        cursor_type: CursorType = "cell",
        zebra_stripes: bool = False,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(cursor_type=cursor_type, zebra_stripes=zebra_stripes, id=id, classes=classes)
        self._is_row_enabled = is_row_enabled

    def action_cursor_up(self) -> None:
        self._move_skipping_disabled(-1)

    def action_cursor_down(self) -> None:
        self._move_skipping_disabled(1)

    def _move_skipping_disabled(self, step: int) -> None:
        if not (self.show_cursor and self.cursor_type == "row"):
            if step < 0:
                super().action_scroll_up()
            else:
                super().action_scroll_down()
            return

        candidate = self.cursor_coordinate.row + step
        while 0 <= candidate < self.row_count and not self._is_row_enabled(candidate):
            candidate += step
        if 0 <= candidate < self.row_count:
            self.move_cursor(row=candidate)


class ManualReviewScreen(TableSageScreen):
    """The Review Transcript step: review speaker labels and text in a working copy of the spellchecked transcript.

    It starts from a still-valid saved draft, else the last completed review (as it was left), else the
    spellchecked transcript. Complete dismisses with the edited transcript and row decisions, which the step saves;
    leaving (Exit, Escape, or quitting the app) with unsaved edits offers Save (a resumable draft), Don't Save, or
    Cancel, then dismisses with None.
    """

    section = "process session · review transcript"

    COMMON_BINDINGS = [
        Binding("escape", "exit_review", "Exit", key_display="Esc"),
        Binding("space", "toggle_mode", "Auto/Manual", key_display="Space"),
        Binding("r,R", "replay", "Replay", key_display="R"),
        Binding("d,D,delete,backspace", "delete_utterance", "Keep/Remove", key_display="D"),
        Binding("f,F", "find_replace", "Find/Replace", key_display="F"),
        Binding("0", "assign_speaker(0)", "Unassigned", key_display="0"),
        *(
            Binding(str(n), f"assign_speaker({n})", "Assign Player", key_display="1-9", show=(n == 1))
            for n in range(1, _MAX_ASSIGNABLE_ATTENDEES + 1)
        ),
        *(
            Binding(f"ctrl+{n}", f"toggle_focus({n})", "Focus Player", key_display="^1-9", show=(n == 1))
            for n in range(1, _MAX_ASSIGNABLE_ATTENDEES + 1)
        ),
    ]

    def __init__(self, session_id: uuid.UUID) -> None:
        super().__init__()
        self._session_id = session_id
        self._session_folder: Path | None = None
        self._transcript: Transcript | None = None
        # `_clip_indices[i]` is the on-disk clip filename index (from `extract_review_clips`'s
        # original enumeration) for the utterance now at working-copy position `i`. Older saved
        # reviews may have physically deleted rows, so clip positions can differ from row positions.
        self._clip_indices: list[int] = []
        self._removed: set[int] = set()
        self._find_replacements: list[Mapping] = []
        self._all_attendee_names: list[str] = []
        self._attendee_names: list[str] = []
        self._playback = ReviewPlayback(self, on_advance=self._auto_advance, on_mode_changed=self._update_mode_indicator)
        self._focus_speaker: str | None = None
        self._playhead = 0
        self._programmatic_move = False
        self._table_ready = False
        self._visit_baseline: transcript_review.ReviewDecision | None = None
        # `DataTable`'s cursor defaults to row 0 before any real navigation, so a mouse click that
        # happens to land there first is reported as a reselect (`RowSelected`) rather than a
        # highlight -- see `on_data_table_row_selected`.
        self._user_has_navigated = False
        # Set around the initial `_play(0)` call in `_enter_review_phase`; see its use below.
        self._pending_mount_echo = False

    @property
    def session_id(self) -> uuid.UUID:
        return self._session_id

    def compose_content(self) -> ComposeResult:
        with Vertical(id="manual-review-panel", classes="panel surface-2") as panel:
            panel.display = False
            panel.border_title = " review transcript "

            with Horizontal(id="manual-review-status"):
                yield Static("Mode: Manual", id="manual-review-mode")
                yield Static("Focus: All players", id="manual-review-focus")
            yield Static("", id="manual-review-legend")

            table = _ReviewTable(
                id="manual-review-table",
                cursor_type="row",
                zebra_stripes=True,
                classes="tablesage-table",
                is_row_enabled=self._is_row_enabled,
            )
            table.add_column("", key="adjusted", width=3)
            table.add_column("Speaker", key="speaker")
            table.add_column("Text", key="text")
            yield table
            with EqualWidthButtonRow(id="manual-review-actions"):
                yield Button("Exit", id="manual-review-cancel")
                yield Button("Complete", id="manual-review-complete", variant="primary")

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        if action == "delete_utterance":
            return True if self._transcript is not None and self._transcript.utterances else None
        if action in {"toggle_mode", "replay", "find_replace", "assign_speaker", "toggle_focus"}:
            return True if self._transcript is not None else None
        return True

    def on_mount(self) -> None:
        self._session_folder = self.application.session_folder(self._session_id)
        attendees = sorted(self.application.list_attendance(self._session_id), key=lambda attendee: attendee.player_name.casefold())
        self._all_attendee_names = [attendee.player_name for attendee in attendees]
        self._attendee_names = self._all_attendee_names[:_MAX_ASSIGNABLE_ATTENDEES]
        self.query_one("#manual-review-legend", Static).update(self._legend_text())

        draft = self.application.load_review_draft(self._session_id)
        if draft is None:
            draft = self.application.saved_transcript_review(self._session_id)
        self.run_with_progress(
            title="Review Transcript",
            message="Restoring saved transcript edits…" if draft is not None else "Extracting clips…",
            work=lambda: self.application.extract_review_clips(self._session_id, on_progress=self.report_progress),
            on_success=lambda result: self._after_extract(result, draft),
            on_error=self._extract_failed,
        )

    def _extract_failed(self, exc: BaseException) -> None:
        self.notify(f"Could not open the transcript review: {exc}", severity="error")
        self._stop_review_resources()
        self.dismiss(None)

    def _after_extract(self, result: tuple[Transcript, Path], draft: transcript_review.ReviewDecision | Transcript | None) -> None:
        source, _clip_dir = result
        if draft is None:
            self._transcript = source
            self._clip_indices = list(range(len(source.utterances)))
        else:
            decision = draft if isinstance(draft, transcript_review.ReviewDecision) else transcript_review.ReviewDecision(draft)
            self._transcript = decision.transcript
            self._clip_indices = self._draft_clip_indices(source, decision.transcript)
            self._removed = set(decision.removed_indices)
            self._find_replacements = list(decision.find_replacements)
        self._visit_baseline = self._decision()
        self.query_one("#manual-review-panel").display = True
        self._enter_review_phase()

    @staticmethod
    def _draft_clip_indices(source: Transcript, draft: Transcript) -> list[int]:
        """Match saved utterances to source clips by their immutable time spans.

        A saved draft may have deleted rows, so its current position is not reliably the source
        clip filename. An unmatched row gets a nonexistent index; playback then safely no-ops.
        """
        available: dict[tuple[float, float], list[int]] = {}
        for index, utterance in enumerate(source.utterances):
            available.setdefault((utterance.start, utterance.end), []).append(index)
        indices: list[int] = []
        for utterance in draft.utterances:
            matches = available.get((utterance.start, utterance.end), [])
            indices.append(matches.pop(0) if matches else -1)
        return indices

    def _legend_text(self) -> str:
        parts = [f"{index}: {name}" for index, name in enumerate(self._attendee_names, start=1)]
        parts.append("0: Unassigned")
        return "   ".join(parts)

    def _enter_review_phase(self) -> None:
        assert self._transcript is not None
        table = self.query_one(_ReviewTable)
        for index in range(len(self._transcript.utterances)):
            marker, speaker, text = self._row_cell_values(index)
            table.add_row(marker, speaker, text, key=str(index))

        table.focus()
        self.refresh_bindings()
        if not self._transcript.utterances:
            return
        self._playhead = 0
        self._playback.set_manual()
        self._update_mode_indicator()
        self._update_focus_indicator()
        self._table_ready = True
        # `DataTable.add_row` above highlights row 0 itself the moment the table gets its first
        # row (a cursor becomes available where there was none) and queues a `RowHighlighted` for
        # it -- delivered only once this method returns, by which point row 0 has already played
        # here directly. `on_data_table_row_highlighted` discards that one expected echo.
        self._pending_mount_echo = True
        self._play(0)

    # Row rendering

    def _is_row_enabled(self, index: int) -> bool:
        if self._focus_speaker is None:
            return True
        assert self._transcript is not None
        return self._transcript.utterances[index].speaker == self._focus_speaker

    def _row_cell_values(self, index: int) -> tuple[object, object, object]:
        assert self._transcript is not None
        utterance = self._transcript.utterances[index]
        removed = index in self._removed
        marker = "✗" if removed else "✓" if utterance.adjusted else ""
        text = utterance.punctuated_text if utterance.punctuated_text is not None else utterance.text
        if self._is_row_enabled(index) and not removed:
            return marker, utterance.speaker, text
        style = "dim strike" if removed else _DIM_STYLE
        return Text(marker), Text(utterance.speaker, style=style), Text(text, style=style)

    def _utterance_text(self, index: int) -> str:
        assert self._transcript is not None
        utterance = self._transcript.utterances[index]
        return utterance.punctuated_text if utterance.punctuated_text is not None else utterance.text

    def _refresh_row(self, index: int) -> None:
        marker, speaker, text = self._row_cell_values(index)
        table = self.query_one(_ReviewTable)
        key = str(index)
        table.update_cell(key, "adjusted", marker)
        table.update_cell(key, "speaker", speaker)
        table.update_cell(key, "text", text)

    def _rebuild_table_styles(self) -> None:
        assert self._transcript is not None
        for index in range(len(self._transcript.utterances)):
            self._refresh_row(index)

    # Navigation / row-highlighted -- the single place a row change causes side effects
    # (playback, and forcing Manual mode for anything not driven by our own code).

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        self.refresh_bindings()
        if not self._table_ready:
            return
        event.stop()
        index = event.cursor_row

        if not self._is_row_enabled(index):
            # Only reachable via a mouse click on a row single-player mode filtered out --
            # `_ReviewTable`'s cursor_up/down override guarantees keyboard moves never land here.
            self.query_one(_ReviewTable).move_cursor(row=self._playhead, scroll=False)
            return

        programmatic = self._programmatic_move
        self._programmatic_move = False

        if self._pending_mount_echo:
            self._pending_mount_echo = False
            if index == 0 and not programmatic:
                return

        # Guards against a redundant echo (e.g. the disabled-row bounce-back above, which moves the
        # cursor back to the playhead without setting `_programmatic_move`) once that row has
        # actually been played. Before that, `_playhead`'s initial 0 coincides with `DataTable`'s own
        # default cursor row, so a mouse click that only changes column (not row) -- landing outside
        # the first, narrow column -- would otherwise look identical to that echo and be dropped
        # silently, even though nothing has played for this visit yet.
        if index == self._playhead and not programmatic and self._user_has_navigated:
            return

        self._user_has_navigated = True
        self._playhead = index
        if not programmatic:
            self._playback.set_manual()
        self._play(index)

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """A second click on the selected row (or Enter) opens that row's editor.

        `DataTable` only posts this (rather than `RowHighlighted`) when the click lands on
        whatever row is already its cursor -- which, before any real navigation happens, is row 0
        by the widget's own default. That makes the very first click on a freshly opened screen
        land here instead of `on_data_table_row_highlighted`, even though nothing has actually
        played yet from that click. Treat that one case as a highlight (play, don't edit); any
        later reselect is a genuine second click and opens the editor as usual.
        """
        event.stop()
        if not self._table_ready or self._transcript is None:
            return
        index = event.cursor_row
        if not self._is_row_enabled(index):
            return

        if not self._user_has_navigated:
            self._user_has_navigated = True
            self._playhead = index
            self._playback.set_manual()
            self._play(index)
            return

        def on_saved(result: ManualReviewUtteranceResult | None) -> None:
            if result is None or self._transcript is None:
                return
            self._transcript = transcript_review.edit_utterance(
                self._transcript,
                index,
                result.speaker,
                result.text,
            )
            self._refresh_row(index)

        utterance = self._transcript.utterances[index]
        self.app.push_screen(
            ManualReviewUtteranceDialog(
                attendee_names=self._all_attendee_names,
                speaker=utterance.speaker,
                text=self._utterance_text(index),
            ),
            on_saved,
        )

    def _next_enabled_row(self, start: int, step: int) -> int | None:
        assert self._transcript is not None
        total = len(self._transcript.utterances)
        candidate = start + step
        while 0 <= candidate < total:
            if self._is_row_enabled(candidate):
                return candidate
            candidate += step
        return None

    def _move_to(self, index: int) -> None:
        self._programmatic_move = True
        self.query_one(_ReviewTable).move_cursor(row=index)

    # Playback

    def _play(self, index: int) -> None:
        """Play row `index`'s clip -- a no-op (not an error) if it has none.

        A handful of utterances per real session have no clip: `extract_review_clips` skips
        extraction for one whose `end` isn't strictly after its `start` (see that function's
        docstring). Such a row is still reviewable and assignable from its text alone.
        """
        assert self._transcript is not None and self._session_folder is not None
        utterance = self._transcript.utterances[index]
        clip = transcript_review.clip_path(self._session_folder, self._clip_indices[index])
        self._playback.play(clip, utterance.end - utterance.start)

    def _auto_advance(self) -> bool:
        next_index = self._next_enabled_row(self._playhead, 1)
        if next_index is None:
            return False
        self._move_to(next_index)
        return True

    def action_toggle_mode(self) -> None:
        self._playback.toggle_mode()

    def action_replay(self) -> None:
        if self._transcript is None:
            return
        self._play(self._playhead)

    def _update_mode_indicator(self) -> None:
        label = "Auto" if self._playback.mode is PlaybackMode.AUTO else "Manual"
        self.query_one("#manual-review-mode", Static).update(f"Mode: {label}")

    def _update_focus_indicator(self) -> None:
        label = self._focus_speaker if self._focus_speaker is not None else "All players"
        self.query_one("#manual-review-focus", Static).update(f"Focus: {label}")

    # Assignment

    def action_assign_speaker(self, number: int) -> None:
        if self._transcript is None:
            return
        if number == 0:
            speaker = UNASSIGNED_SPEAKER
        else:
            if number > len(self._attendee_names):
                return
            speaker = self._attendee_names[number - 1]

        self._transcript = transcript_review.assign_speaker(self._transcript, self._playhead, speaker)
        self._refresh_row(self._playhead)

        next_index = self._next_enabled_row(self._playhead, 1)
        if next_index is not None:
            self._move_to(next_index)

    # Keep/Remove leaves the row and its source clip available for restoration.

    def action_delete_utterance(self) -> None:
        if self._transcript is None or not self._transcript.utterances:
            return

        index = self._playhead
        self._removed.symmetric_difference_update({index})
        self._refresh_row(index)

    # Find & Replace -- a bulk edit across every utterance's displayed text, not just the
    # playhead row. Like every other row edit here, it only changes the working copy.

    def action_find_replace(self) -> None:
        if self._transcript is None:
            return

        def on_result(result: FindReplaceResult | None) -> None:
            if result is None or self._transcript is None:
                return
            kept_indices = [index for index in range(len(self._transcript.utterances)) if index not in self._removed]
            kept = Transcript(utterances=[self._transcript.utterances[index] for index in kept_indices])
            changed, outcome = transcript_review.replace_text(kept, result.find, result.replace, result.case_sensitive)
            if outcome.utterance_count:
                utterances = list(self._transcript.utterances)
                for index, utterance in zip(kept_indices, changed.utterances, strict=True):
                    utterances[index] = utterance
                self._transcript = Transcript(utterances=utterances)
                if result.find.strip() and result.replace.strip():
                    mapping = Mapping(result.find, result.replace, result.case_sensitive)
                    if mapping not in self._find_replacements:
                        self._find_replacements.append(mapping)
            self._rebuild_table_styles()
            if not outcome.utterance_count:
                self.notify("No matches found.", severity="warning")
                return
            occurrence_plural = "" if outcome.occurrence_count == 1 else "s"
            utterance_plural = "" if outcome.utterance_count == 1 else "s"
            self.notify(
                f"Replaced {outcome.occurrence_count} occurrence{occurrence_plural} "
                f"in {outcome.utterance_count} utterance{utterance_plural}."
            )

        self.app.push_screen(FindReplaceDialog(), on_result)

    # Single-player mode

    def action_toggle_focus(self, number: int) -> None:
        if self._transcript is None or number > len(self._attendee_names):
            return
        target = self._attendee_names[number - 1]

        if self._focus_speaker == target:
            self._focus_speaker = None
            self._rebuild_table_styles()
            self._update_focus_indicator()
            return

        if not any(utterance.speaker == target for utterance in self._transcript.utterances):
            self.notify(f"No utterances currently assigned to {target}.", severity="warning")
            return

        self._focus_speaker = target
        self._rebuild_table_styles()
        self._update_focus_indicator()

        if not self._is_row_enabled(self._playhead):
            next_index = self._next_enabled_row(self._playhead, 1)
            if next_index is None:
                next_index = self._next_enabled_row(self._playhead, -1)
            assert next_index is not None
            self._move_to(next_index)

    # Complete / cancel

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.id == "manual-review-complete":
            self.action_complete()
        elif event.button.id == "manual-review-cancel":
            self.action_exit_review()

    def action_complete(self) -> None:
        if self._transcript is None:
            return
        self._stop_review_resources()
        self.dismiss(self._decision())

    def action_exit_review(self) -> None:
        """Cancel the step, first offering to save changed transcript work as a draft."""
        self.confirm_leave(lambda: self.dismiss(None))

    def confirm_leave(self, on_confirm: Callable[[], object]) -> None:
        """Offer the save-draft decision before leaving; the application quit path uses it too."""
        if not self._has_unsaved_transcript_changes():
            self._stop_review_resources()
            on_confirm()
            return

        def on_choice(choice: bool | None) -> None:
            if choice is None:
                return
            if choice:
                assert self._transcript is not None
                try:
                    self.application.save_review_draft(self._session_id, self._decision())
                except Exception as exc:
                    self.notify(f"Could not save transcript edits: {exc}", severity="error")
                    return
            self._stop_review_resources()
            on_confirm()

        self.app.push_screen(
            ConfirmationDialog(
                title="Save Transcript Edits?",
                prompt="Save your transcript edits so you can continue reviewing them later?",
                no_label="Don't Save",
                yes_label="Save",
            ),
            on_choice,
        )

    def _has_unsaved_transcript_changes(self) -> bool:
        return self._transcript is not None and self._visit_baseline is not None and self._decision() != self._visit_baseline

    def _decision(self) -> transcript_review.ReviewDecision:
        assert self._transcript is not None
        return transcript_review.ReviewDecision(
            self._transcript.model_copy(deep=True), tuple(sorted(self._removed)), tuple(self._find_replacements)
        )

    def _stop_review_resources(self) -> None:
        self._playback.stop()
        self.application.discard_review_clips(self._session_id)
