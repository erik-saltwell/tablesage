from __future__ import annotations

import time
import uuid
from collections.abc import Callable
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

from rich.text import Text
from tablesage_application.session_pipeline import transcript_review
from tablesage_tools.speakers import UNASSIGNED_SPEAKER
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.timer import Timer
from textual.widgets import DataTable, Static
from textual.widgets.data_table import CursorType

from ..audio_playback import ClipPlayer
from .base import TableSageScreen

if TYPE_CHECKING:
    from tablesage_tools.model import Transcript

_MAX_ASSIGNABLE_ATTENDEES = 9
_AUTO_ADVANCE_DELAY = 0.25
_DIM_STYLE = "dim"


class PlaybackMode(Enum):
    MANUAL = "manual"
    AUTO = "auto"


class _ReviewTable(DataTable[object]):
    """A `DataTable` whose `Up`/`Down` cursor movement skips rows `is_row_enabled` rejects.

    Mouse clicks aren't filtered here -- `DataTable` has no per-row disabled/unclickable
    concept, so a click on a filtered row is instead caught and bounced back by
    `SpeakerReviewScreen.on_data_table_row_highlighted`, which can tell the two apart
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


class SpeakerReviewScreen(TableSageScreen):
    """Fast, keyboard-first correction of per-utterance speaker labels into hand-verified ground truth.

    See `.documentation/speaker_review_screen.md` for the full design. Corrections overwrite
    `Utterance.speaker` in `transcript.json` directly and are saved after every assignment --
    there is no separate save step and no persisted resume position (the screen always opens
    at row 0; a mouse click is the way back to the middle of a session reviewed before).
    """

    section = "session detail"

    BINDINGS = [
        Binding("escape", "pop_screen", "Back", key_display="Esc", show=False),
        Binding("space", "toggle_mode", "Auto/Manual", key_display="Space"),
        Binding("r,R", "replay", "Replay", key_display="R"),
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
        self._attendee_names: list[str] = []
        self._player = ClipPlayer()
        self._mode = PlaybackMode.MANUAL
        self._focus_speaker: str | None = None
        self._playhead = 0
        self._programmatic_move = False
        self._table_ready = False
        self._advance_timer: Timer | None = None
        self._clip_started_at = 0.0
        self._current_duration = 0.0

    def compose_content(self) -> ComposeResult:
        with Vertical(id="speaker-review-panel", classes="panel surface-2") as panel:
            panel.border_title = " review speakers "

            with Horizontal(id="speaker-review-status"):
                yield Static("Mode: Manual", id="speaker-review-mode")
                yield Static("Focus: All players", id="speaker-review-focus")
            yield Static("", id="speaker-review-legend")

            table = _ReviewTable(
                id="speaker-review-table",
                cursor_type="row",
                zebra_stripes=True,
                classes="tablesage-table",
                is_row_enabled=self._is_row_enabled,
            )
            table.add_column("", key="adjusted", width=3)
            table.add_column("Speaker", key="speaker")
            table.add_column("Text", key="text")
            yield table

    def on_mount(self) -> None:
        self._session_folder = self.application.session_folder(self._session_id)
        attendees = sorted(self.application.list_attendance(self._session_id), key=lambda attendee: attendee.player_name.casefold())
        self._attendee_names = [attendee.player_name for attendee in attendees[:_MAX_ASSIGNABLE_ATTENDEES]]
        self.query_one("#speaker-review-legend", Static).update(self._legend_text())

        def work() -> tuple[Transcript, Path]:
            assert self._session_folder is not None
            return self.application.extract_review_clips(self._session_id, on_progress=self.report_progress)

        self.run_with_progress(
            title="Review Speakers",
            message="Extracting clips…",
            work=work,
            on_success=self._after_extract,
        )

    def _legend_text(self) -> str:
        parts = [f"{index}: {name}" for index, name in enumerate(self._attendee_names, start=1)]
        parts.append("0: Unassigned")
        return "   ".join(parts)

    def _after_extract(self, result: tuple[Transcript, Path]) -> None:
        transcript, _clip_dir = result
        self._transcript = transcript
        table = self.query_one(_ReviewTable)
        for index in range(len(transcript.utterances)):
            marker, speaker, text = self._row_cell_values(index)
            table.add_row(marker, speaker, text, key=str(index))

        if not transcript.utterances:
            return
        self._playhead = 0
        self._mode = PlaybackMode.MANUAL
        self._update_mode_indicator()
        self._update_focus_indicator()
        self._table_ready = True
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
        marker = "✓" if utterance.adjusted else ""
        text = utterance.punctuated_text if utterance.punctuated_text is not None else utterance.text
        if self._is_row_enabled(index):
            return marker, utterance.speaker, text
        return Text(marker, style=_DIM_STYLE), Text(utterance.speaker, style=_DIM_STYLE), Text(text, style=_DIM_STYLE)

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
        if index == self._playhead and not programmatic:
            return

        self._playhead = index
        if not programmatic:
            self._mode = PlaybackMode.MANUAL
            self._update_mode_indicator()
        self._play(index)

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
        self._clip_started_at = time.monotonic()
        self._current_duration = max(0.0, utterance.end - utterance.start)
        clip = transcript_review.clip_path(self._session_folder, index)
        if clip.is_file():
            self._player.play(clip)
        self._reschedule_auto_advance()

    def _reschedule_auto_advance(self) -> None:
        if self._advance_timer is not None:
            self._advance_timer.stop()
            self._advance_timer = None
        if self._mode is not PlaybackMode.AUTO:
            return
        elapsed = time.monotonic() - self._clip_started_at
        remaining = max(0.0, self._current_duration - elapsed) + _AUTO_ADVANCE_DELAY
        self._advance_timer = self.set_timer(remaining, self._on_auto_advance_due)

    def _on_auto_advance_due(self) -> None:
        self._advance_timer = None
        next_index = self._next_enabled_row(self._playhead, 1)
        if next_index is None:
            self._mode = PlaybackMode.MANUAL
            self._update_mode_indicator()
            return
        self._move_to(next_index)

    def action_toggle_mode(self) -> None:
        self._mode = PlaybackMode.MANUAL if self._mode is PlaybackMode.AUTO else PlaybackMode.AUTO
        self._update_mode_indicator()
        self._reschedule_auto_advance()

    def action_replay(self) -> None:
        if self._transcript is None:
            return
        self._play(self._playhead)

    def _update_mode_indicator(self) -> None:
        label = "Auto" if self._mode is PlaybackMode.AUTO else "Manual"
        self.query_one("#speaker-review-mode", Static).update(f"Mode: {label}")

    def _update_focus_indicator(self) -> None:
        label = self._focus_speaker if self._focus_speaker is not None else "All players"
        self.query_one("#speaker-review-focus", Static).update(f"Focus: {label}")

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
        self.application.save_transcript(self._session_id, self._transcript)
        self._refresh_row(self._playhead)

        next_index = self._next_enabled_row(self._playhead, 1)
        if next_index is not None:
            self._move_to(next_index)

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

    # Exit

    def action_pop_screen(self) -> None:
        self._player.stop()
        if self._advance_timer is not None:
            self._advance_timer.stop()
            self._advance_timer = None
        self.application.discard_review_clips(self._session_id)
        super().action_pop_screen()
