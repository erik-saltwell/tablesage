from __future__ import annotations

from collections.abc import Sequence

from tablesage_application.player_import_from_audio import SpeakerUtteranceClip
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, DataTable

from ..audio_playback import ClipPlayer
from ..widgets import EqualWidthButtonRow


def _format_timestamp(seconds: float) -> str:
    minutes, secs = divmod(int(seconds), 60)
    return f"{minutes:02d}:{secs:02d}"


class TranscriptViewDialog(ModalScreen[None]):
    """Stage 4's "show me everything Speaker N said" view.

    There's no way to reassign or exclude an individual utterance here (see
    `.documentation/import_players_from_audio_file.md` -- editing stays speaker-ID
    level), but pressing `P` (or the "Play Clip" button -- every other action in this app
    is reachable without memorizing a key, so this one is too) plays the selected row's
    clip to help judge it, since transcript text alone doesn't always settle "is this
    really who I think it is." Playback is bound to a dedicated key, not row selection,
    so browsing the table with the cursor never triggers audio by accident.
    """

    BINDINGS = [
        Binding("escape", "close", "Close", show=False),
        Binding("p,P", "play_selected", "Play Clip", key_display="P"),
    ]

    def __init__(self, *, speaker_id: str, clips: Sequence[SpeakerUtteranceClip]) -> None:
        super().__init__()
        self._speaker_id = speaker_id
        self._clips = list(clips)
        self._player = ClipPlayer()

    def compose(self) -> ComposeResult:
        with Vertical(id="transcript-view-dialog") as dialog:
            dialog.border_title = f" {self._speaker_id} "
            table: DataTable[str] = DataTable(id="transcript-view-table", cursor_type="row", zebra_stripes=True, classes="tablesage-table")
            table.add_column("Time", key="time")
            table.add_column("Text", key="text")
            for index, clip in enumerate(self._clips):
                text = clip.utterance.punctuated_text if clip.utterance.punctuated_text is not None else clip.utterance.text
                table.add_row(_format_timestamp(clip.utterance.start), text or "(no dialogue captured)", key=str(index))
            yield table
            with EqualWidthButtonRow(classes="dialog-actions"):
                yield Button("Play Clip", id="transcript-view-play")
                yield Button("Close", id="transcript-view-close")

    def action_play_selected(self) -> None:
        if not self._clips:
            return
        table = self.query_one("#transcript-view-table", DataTable)
        if table.row_count == 0:
            return
        row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key.value
        if row_key is None:
            return
        clip = self._clips[int(row_key)]
        self._player.play(clip.clip_path)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "transcript-view-play":
            self.action_play_selected()
        elif event.button.id == "transcript-view-close":
            self.dismiss(None)

    def action_close(self) -> None:
        self._player.stop()
        self.dismiss(None)
