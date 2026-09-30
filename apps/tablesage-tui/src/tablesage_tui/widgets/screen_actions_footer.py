"""Keep screen actions visible while editable fields consume their letter keys."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from textual import events
from textual.app import ComposeResult
from textual.widgets import Footer
from textual.widgets._footer import FooterKey

if TYPE_CHECKING:
    from ..screens.base import TableSageScreen


class ScreenActionKey(FooterKey):
    def on_mouse_down(self, event: events.MouseDown | None = None) -> None:
        # A normal FooterKey simulates typing its key. An editable field would
        # consume that letter, so clicks invoke the screen action directly.
        if event is not None:
            event.stop()
            event.prevent_default()
        if self._disabled:
            self.app.bell()
        else:
            self.call_later(self.app.run_action, self.action, default_namespace=self.screen)


class ScreenActionsFooter(Footer):
    def compose(self) -> ComposeResult:
        if not self._bindings_ready:
            return
        screen = cast("TableSageScreen", self.screen)
        shown: set[str] = set()
        for binding in screen.COMMON_BINDINGS:
            if not binding.show or binding.action in shown:
                continue
            state = screen.check_action(binding.action, ())
            if state is False:
                continue
            shown.add(binding.action)
            yield ScreenActionKey(
                binding.key.split(",")[0],
                self.app.get_key_display(binding),
                binding.description,
                binding.action,
                disabled=state is None,
                tooltip=binding.tooltip,
            ).data_bind(compact=Footer.compact)
