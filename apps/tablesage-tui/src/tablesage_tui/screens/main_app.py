from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import widelog
from tablesage_application import Application
from tablesage_application.configuration import Configuration, validate_models
from tablesage_application.observability import configure_logging
from tablesage_model.setup import ensure_settings
from textual.app import App
from textual.binding import Binding
from textual.notifications import SeverityLevel
from textual.screen import Screen

from ..resources import load_resource
from ..startup import ensure_media_tools
from .landing import LandingScreen


class TableSageApp(App):
    ERROR_NOTIFICATION_TIMEOUT = float("inf")

    def __init__(
        self, application: Application | None = None, *, configuration: Configuration | None = None, settings_review_required: bool = False
    ) -> None:
        # `main()` is the real composition root and always injects settings-loaded
        # Application; this fallback (tests, ad-hoc scripts) gets AppSettings() defaults.
        self.application = application or Application()
        self.configuration = configuration
        self.settings_review_required = settings_review_required
        super().__init__()

    def on_mount(self) -> None:
        with widelog.wide_event(op="tablesage.app_started", cwd=str(Path.cwd()), python=sys.version.split()[0], pid=os.getpid()):
            pass
        if self.settings_review_required:
            self.notify(
                "Configure and save your settings before progressing. Press S to open Settings.",
                title="Settings required",
                severity="warning",
                timeout=float("inf"),
            )

    def exit(self, *args: Any, **kwargs: Any) -> None:
        # Logged when exit is requested, while screens and workers still exist, so an interrupted
        # run is distinguishable from one that never started.
        with widelog.wide_event(
            op="tablesage.app_exit",
            screen_stack=[type(screen).__name__ for screen in self.screen_stack],
            running_workers=[worker.name for worker in self.workers if worker.is_running],
        ):
            pass
        super().exit(*args, **kwargs)

    def action_open_settings(self) -> None:
        from .settings import SettingsScreen

        if self.configuration is None:
            self.configuration = Configuration(Path.cwd())
        self.push_screen(SettingsScreen(self.configuration, required=self.settings_review_required))

    async def action_quit(self) -> None:
        from .previously_on import PreviouslyOnScreen
        from .settings import SettingsScreen
        from .speaker_review import ManualReviewScreen

        if isinstance(self.screen, PreviouslyOnScreen):
            self.screen.confirm_leave(self.exit)
        elif isinstance(self.screen, ManualReviewScreen):
            self.screen.confirm_leave(self.exit)
        elif any(isinstance(screen, PreviouslyOnScreen) for screen in self.screen_stack):
            self.notify("Close the current dialog before leaving Previously On.")
        elif any(isinstance(screen, ManualReviewScreen) for screen in self.screen_stack):
            self.notify("Close the current dialog before saving or discarding transcript edits.")
        elif isinstance(self.screen, SettingsScreen):
            self.screen.confirm_leave(self.exit)
        elif any(isinstance(screen, SettingsScreen) and screen._dirty() for screen in self.screen_stack):
            self.notify("Close the current dialog to save or discard your Settings changes before quitting.")
        else:
            self.exit()

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
    ensure_media_tools()
    configuration = Configuration(Path.cwd())
    configure_logging(Path.cwd())
    settings = ensure_settings(None, load_resource("settings.yaml"))
    review_required = configuration.needs_review(settings)
    validate_models(settings)
    application = Application(settings=settings)
    app = TableSageApp(application, configuration=configuration, settings_review_required=review_required)
    app.run()


if __name__ == "__main__":
    main()
