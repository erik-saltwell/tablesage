from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Static


class PlayerArchiveErrorsDialog(ModalScreen[None]):
    DEFAULT_CSS = """
    PlayerArchiveErrorsDialog { align: center middle; }
    PlayerArchiveErrorsDialog > Vertical {
        width: 80%; height: 80%; border: round $error; background: $surface; padding: 1 2;
    }
    PlayerArchiveErrorsDialog VerticalScroll { height: 1fr; }
    """
    BINDINGS = [Binding("escape", "close", "Close", show=False)]

    def __init__(self, message: str, *, title: str = "Import Players Failed") -> None:
        super().__init__()
        self._message = message
        self._title = title

    def compose(self) -> ComposeResult:
        with Vertical() as panel:
            panel.border_title = self._title
            with VerticalScroll():
                yield Static(self._message, markup=False)
            yield Button("Close", id="player-archive-errors-close", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(None)

    def action_close(self) -> None:
        self.dismiss(None)
