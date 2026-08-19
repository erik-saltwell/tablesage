from __future__ import annotations

from dotenv import load_dotenv
from tablesage_application import Application
from tablesage_model.setup import ensure_settings
from textual.app import App
from textual.binding import Binding
from textual.screen import Screen

from ..resources import load_resource
from .landing import LandingScreen


class TableSageApp(App):
    def __init__(self, application: Application | None = None) -> None:
        # `main()` is the real composition root and always injects settings-loaded
        # Application; this fallback (tests, ad-hoc scripts) gets AppSettings() defaults.
        self.application = application or Application()
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
    settings = ensure_settings(None, load_resource("settings.yaml"))
    application = Application(settings=settings)
    app = TableSageApp(application)
    app.run()


if __name__ == "__main__":
    main()
