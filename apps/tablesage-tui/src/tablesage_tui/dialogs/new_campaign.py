from __future__ import annotations

from dataclasses import dataclass

from tablesage_model.io import slugify
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Static


@dataclass(frozen=True)
class NewCampaignResult:
    name: str
    description: str
    system: str
    default_gm: str


class NewCampaignDialog(ModalScreen[NewCampaignResult | None]):
    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=False),
    ]

    def __init__(self, existing_slugs: frozenset[str] = frozenset()) -> None:
        super().__init__()
        self._existing_slugs = existing_slugs

    def compose(self) -> ComposeResult:
        with Vertical(id="new-campaign-dialog") as dlg:
            dlg.border_title = "New Campaign"
            yield Input(placeholder="Campaign name", id="campaign-name")
            yield Input(placeholder="Description", id="campaign-description")
            yield Input(placeholder="System", id="campaign-system")
            yield Input(placeholder="Default GM", id="campaign-default-gm")
            yield Static("", id="new-campaign-error")

            with Horizontal(classes="dialog-actions"):
                yield Button("Cancel", id="cancel")
                yield Button("Create", id="create", variant="primary")

    def on_mount(self) -> None:
        self.query_one("#campaign-name", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.dismiss(None)
            return

        if event.button.id == "create":
            self._submit()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        event.stop()
        self._submit()

    def action_cancel(self) -> None:
        self.dismiss(None)

    def _submit(self) -> None:
        name_input = self.query_one("#campaign-name", Input)
        description_input = self.query_one("#campaign-description", Input)
        system_input = self.query_one("#campaign-system", Input)
        default_gm_input = self.query_one("#campaign-default-gm", Input)

        name = name_input.value.strip()
        description = description_input.value.strip()
        system = system_input.value.strip()
        default_gm = default_gm_input.value.strip()

        if not name:
            self.query_one("#new-campaign-error", Static).update("Campaign name is required.")
            name_input.focus()
            return

        if slugify(name) in self._existing_slugs:
            self.query_one("#new-campaign-error", Static).update("A campaign with that name already exists.")
            name_input.focus()
            return

        if not system:
            self.query_one("#new-campaign-error", Static).update("System is required.")
            system_input.focus()
            return

        if not default_gm:
            self.query_one("#new-campaign-error", Static).update("Default GM is required.")
            default_gm_input.focus()
            return

        self.dismiss(NewCampaignResult(name=name, description=description, system=system, default_gm=default_gm))
