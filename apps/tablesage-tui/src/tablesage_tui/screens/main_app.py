from __future__ import annotations

from dotenv import load_dotenv
from tablesage_application import Application
from textual.app import App
from textual.binding import Binding
from textual.screen import Screen

from .landing import LandingScreen


class TableSageApp(App):
    def __init__(self, application: Application) -> None:
        self.application = application
        super().__init__()

    CSS_PATH = ["../styles/app.tcss"]
    BINDINGS = [
        Binding(
            "ctrl+q",
            "quit",
            "Quit",
            key_display="^Q",
            priority=True,
        ),
    ]

    ENABLE_COMMAND_PALETTE = False

    def get_default_screen(self) -> Screen[None]:
        return LandingScreen()


def main() -> None:
    load_dotenv()
    application = Application()
    app = TableSageApp(application)
    app.run()


if __name__ == "__main__":
    main()
