from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from tablesage_application import Application
from tablesage_application.observability import configure_logging
from tablesage_model.setup import ensure_settings
from textual.app import App
from textual.binding import Binding
from textual.notifications import SeverityLevel
from textual.screen import Screen

from ..resources import load_resource
from .landing import LandingScreen


class TableSageApp(App):
    ERROR_NOTIFICATION_TIMEOUT = float("inf")

    def __init__(self, application: Application | None = None) -> None:
        # `main()` is the real composition root and always injects settings-loaded
        # Application; this fallback (tests, ad-hoc scripts) gets AppSettings() defaults.
        self.application = application or Application()
        super().__init__()

    CSS_PATH = ["../styles/app.tcss"]
    BINDINGS = [
        # Kept working everywhere (priority=True), but not shown in the footer
        # except on LandingScreen, which re-declares it with show=True.
        Binding(
            "ctrl+q",
            "quit",
            "Quit",
            key_display="^Q",
            priority=True,
            show=False,
        ),
    ]

    ENABLE_COMMAND_PALETTE = False

    def notify(
        self,
        message: str,
        *,
        title: str = "",
        severity: SeverityLevel = "information",
        timeout: float | None = None,
        markup: bool = True,
    ) -> None:
        """Show errors until clicked while leaving other notifications temporary."""
        if severity == "error":
            timeout = self.ERROR_NOTIFICATION_TIMEOUT
        super().notify(
            message,
            title=title,
            severity=severity,
            timeout=timeout,
            markup=markup,
        )

    def get_default_screen(self) -> Screen[None]:
        return LandingScreen()


def main() -> None:
    load_dotenv()
    configure_logging(Path.cwd())
    settings = ensure_settings(None, load_resource("settings.yaml"))
    application = Application(settings=settings)
    app = TableSageApp(application)
    app.run()


if __name__ == "__main__":
    main()
